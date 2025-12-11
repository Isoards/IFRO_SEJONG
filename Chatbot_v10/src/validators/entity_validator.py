"""
Entity Validator - v4.2 Validation Pyramid
계획서 2.3: Validator (Rule → Small Model → LLM + RL)

v4.2 핵심:
- L0: 길이 < N, 전부 숫자, stopword, 대명사 → reject
- L1: Small model (의미 있는 엔티티 후보인지)
- L2: LLM 도메인 내 의미 검증
- Domain Dictionary 연동
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from difflib import SequenceMatcher

from src.validators.base import BaseValidator, ValidationResult, LayerResult, LayerDecision
from src.domain.entities import Entity, EntityCandidate
from src.shared.logging import get_logger
from config.constants import FeasibilityLevel, ValidationLayer

if TYPE_CHECKING:
    from src.services.llm_service import LLMService
    from src.storage.policy_store import PolicyStore
    from src.storage.domain_dictionary import DomainDictionary

logger = get_logger(__name__)


class EntityValidator(BaseValidator):
    """
    Entity 검증기 - v4.2 Validation Pyramid
    
    L0 (Rule Filter):
    - 최소/최대 길이 검증
    - 숫자만으로 구성된 이름 reject
    - Stopword/대명사 reject
    - 특수문자 비율 검증
    
    L1 (Small Model):
    - "의미 있는 엔티티 후보인지" 분류
    
    L2 (LLM + RL):
    - "도메인 내에서 의미 있는 개념인가?" 검증
    - Domain Dictionary 연동
    """
    
    # L0 Rule: 길이 제한
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    MAX_SPECIAL_CHAR_RATIO = 0.3
    
    # L0 Rule: Stopwords & Pronouns
    STOPWORDS = {
        # English
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "this", "that", "these", "those", "it", "its",
        # Korean
        "것", "이것", "저것", "그것", "등", "및", "또한", "그리고",
        "이", "그", "저", "여기", "거기", "저기"
    }
    
    PRONOUNS = {
        # English
        "i", "you", "he", "she", "it", "we", "they",
        "me", "him", "her", "us", "them",
        "my", "your", "his", "her", "our", "their",
        # Korean
        "나", "너", "그", "그녀", "우리", "그들",
        "저", "제", "자신"
    }
    
    def __init__(
        self,
        llm_service: Optional["LLMService"] = None,
        policy_store: Optional["PolicyStore"] = None,
        domain_dictionary: Optional["DomainDictionary"] = None
    ):
        super().__init__(
            llm_service=llm_service,
            policy_store=policy_store,
            validator_name="EntityValidator"
        )
        
        # v4.2: Domain Dictionary 연동
        self.domain_dictionary = domain_dictionary
    
    # ========== 레거시 호환성 ==========
    
    async def validate_entity(
        self,
        entity: Entity,
        use_llm: bool = True
    ) -> ValidationResult:
        """
        레거시 호환: Entity 검증
        v4.2에서는 validate()로 위임
        """
        if use_llm:
            return await self.validate(entity)
        else:
            # Rule만 사용
            rule_result = await self.rule_check(entity)
            return ValidationResult(
                is_valid=rule_result.decision != LayerDecision.REJECT,
                score=rule_result.score,
                reasons=rule_result.reasons,
                details={
                    "rule_score": rule_result.score,
                    "llm_score": 0.7,
                    "history_score": 0.5,
                    "entity_type": entity.entity_type,
                    **rule_result.details
                },
                layer=ValidationLayer.RULE,
                rejected_early=rule_result.decision == LayerDecision.REJECT
            )
    
    # ========== L0: Rule Check ==========
    
    async def rule_check(self, item: Any) -> LayerResult:
        """
        L0: Rule-based 빠른 필터링
        
        검증 항목:
        - 최소/최대 길이
        - 숫자 전용 이름
        - Stopword/대명사
        - 특수문자 비율
        """
        if not isinstance(item, Entity):
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["Invalid input: expected Entity"],
                details={"error": "type_mismatch"}
            )
        
        entity = item
        name = entity.canonical_name.strip()
        name_lower = name.lower()
        
        score = 1.0
        reasons: List[str] = []
        
        # 1. 길이 검증
        if len(name) < self.MIN_NAME_LENGTH:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"이름 너무 짧음: {len(name)} < {self.MIN_NAME_LENGTH}"],
                details={"rule": "min_length"}
            )
        
        if len(name) > self.MAX_NAME_LENGTH:
            score -= 0.3
            reasons.append(f"이름 너무 김: {len(name)} > {self.MAX_NAME_LENGTH}")
        
        # 2. 숫자 전용 이름 reject
        if name.isdigit():
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["숫자로만 구성된 이름"],
                details={"rule": "digits_only"}
            )
        
        # 3. Stopword reject
        if name_lower in self.STOPWORDS:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"Stopword 엔티티: {name}"],
                details={"rule": "stopword"}
            )
        
        # 4. 대명사 reject
        if name_lower in self.PRONOUNS:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"대명사 엔티티: {name}"],
                details={"rule": "pronoun"}
            )
        
        # 5. 특수문자 비율 체크
        if name:
            special_chars = sum(1 for c in name if not c.isalnum() and c != ' ')
            special_ratio = special_chars / len(name)
            if special_ratio > self.MAX_SPECIAL_CHAR_RATIO:
                score -= 0.3
                reasons.append(f"특수문자 비율 높음: {special_ratio:.2%}")
        
        # 6. 공백 전용 체크
        if not name or name.isspace():
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["빈 이름 또는 공백 전용"],
                details={"rule": "empty_name"}
            )
        
        # 7. v4.2: Domain Dictionary 중복 체크
        if self.domain_dictionary:
            try:
                existing = await self.domain_dictionary.get_canonical(name)
                if existing and existing.entity_id != entity.id:
                    # 이미 존재하는 엔티티 - reject이 아닌 병합 신호
                    score -= 0.1
                    reasons.append(f"Dictionary에 유사 엔티티 존재: {existing.canonical_name}")
            except Exception:
                pass  # Dictionary 오류는 무시
        
        # 결정
        score = max(0.0, score)
        
        if score < self.settings.rule_reject_threshold:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details={"rule": "below_threshold"}
            )
        
        return LayerResult(
            score=score,
            decision=LayerDecision.PASS,
            reasons=reasons,
            details={
                "entity_type": entity.entity_type,
                "name_length": len(name)
            }
        )
    
    # ========== L1: Small Model Check ==========
    
    async def _call_small_model(self, item: Any) -> LayerResult:
        """
        L1: Small Model 검증
        
        "이 용어가 의미 있는 엔티티 후보인가?" 분류
        """
        entity = item
        
        # Small Model endpoint가 없으면 pass-through
        if not self.settings.small_model_endpoint:
            return LayerResult(
                score=0.7,
                decision=LayerDecision.PASS,
                reasons=[],
                details={"small_model": "pass_through"}
            )
        
        # TODO: Small Model API 호출 구현
        # 현재는 휴리스틱으로 대체
        score = 0.7
        reasons = []
        
        # 휴리스틱: 단어 수 기반
        words = entity.canonical_name.split()
        if len(words) > 10:
            score -= 0.2
            reasons.append("엔티티 이름이 문장처럼 김")
        
        # 휴리스틱: 대문자 시작 (영어 고유명사)
        if entity.canonical_name[0].isupper() or not entity.canonical_name[0].isalpha():
            score += 0.1  # 보너스
        
        if score < self.settings.small_model_reject_threshold:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details={"small_model": "heuristic_reject"}
            )
        
        return LayerResult(
            score=min(1.0, score),
            decision=LayerDecision.PASS,
            reasons=reasons,
            details={"small_model": "heuristic_pass"}
        )
    
    # ========== L2: LLM Check ==========
    
    def _build_llm_prompt(self, item: Any) -> str:
        """L2: LLM 검증 프롬프트 생성"""
        entity = item
        return f"""다음 엔티티의 품질을 평가하세요.

Entity 정보:
- 정규 이름: {entity.canonical_name}
- 유형: {entity.entity_type}
- 설명: {entity.description or '없음'}
- 별칭: {', '.join(entity.aliases) if entity.aliases else '없음'}
- 도메인 태그: {', '.join(entity.domain_tags) if entity.domain_tags else '없음'}

평가 기준:
1. 이 이름이 독립적인 개념/엔티티로 의미 있는가?
2. 도메인 내에서 유효한 용어인가?
3. 엔티티 유형이 적절한가?
4. 이름과 설명이 일치하는가?

JSON 형식으로 응답하세요:
{{
    "score": 0.0-1.0,
    "is_valid": true/false,
    "is_domain_term": true/false,
    "issues": ["발견된 문제점 목록"],
    "suggested_type": "더 적절한 엔티티 유형 (선택)",
    "reasoning": "평가 근거"
}}
"""
    
    def _history_score(self, item: Any) -> float:
        """엔티티 유형별 히스토리 점수"""
        entity = item
        
        similar_feedbacks = [
            f for f in self._feedback_history
            if f.get("entity_type") == entity.entity_type
        ]
        
        if not similar_feedbacks:
            return 0.5  # 기본값
        
        approved = sum(1 for f in similar_feedbacks if f.get("approved", False))
        return approved / len(similar_feedbacks)
    
    # ========== Entity Merge Validation ==========
    
    async def validate_merge(
        self,
        existing: Entity,
        candidate: EntityCandidate,
        similarity: float,
        use_llm: bool = True
    ) -> tuple[bool, List[str]]:
        """
        두 엔티티 병합 여부 결정
        
        v4.2: Domain Dictionary 우선 참조
        """
        reasons = []
        
        # 1. Domain Dictionary에서 확인
        if self.domain_dictionary:
            try:
                existing_entry = await self.domain_dictionary.get_canonical(existing.canonical_name)
                candidate_entry = await self.domain_dictionary.get_canonical(candidate.name)
                
                if existing_entry and candidate_entry:
                    if existing_entry.entity_id == candidate_entry.entity_id:
                        return True, ["Dictionary에서 동일 엔티티로 확인됨"]
                    else:
                        return False, ["Dictionary에서 다른 엔티티로 확인됨"]
            except Exception:
                pass
        
        # 2. 기본 임계값 체크
        if similarity < self.settings.entity_similarity_threshold:
            reasons.append(f"유사도 미달: {similarity:.2f} < {self.settings.entity_similarity_threshold}")
            return False, reasons
        
        # 3. 도메인 태그 일치 여부
        if existing.domain_tags and candidate.domain_tags:
            common_tags = set(existing.domain_tags) & set(candidate.domain_tags)
            if not common_tags:
                reasons.append("도메인 태그 불일치")
                return False, reasons
        
        # 4. LLM 기반 병합 검증 (옵션)
        if use_llm and self.llm_service:
            llm_approve, llm_reasons = await self._validate_merge_with_llm(existing, candidate)
            reasons.extend(llm_reasons)
            if not llm_approve:
                return False, reasons
        
        # 5. 히스토리 기반 결정
        merge_history = [
            f for f in self._feedback_history
            if f.get("item_id") == existing.id and "merge" in f.get("reason", "")
        ]
        
        if merge_history:
            wrong_merges = sum(1 for f in merge_history if not f.get("approved", True))
            if wrong_merges > 0:
                if similarity < (self.settings.entity_similarity_threshold + 0.1):
                    reasons.append("이전 잘못된 병합 이력으로 인한 임계값 상향")
                    return False, reasons
        
        return True, reasons
    
    async def _validate_merge_with_llm(
        self,
        existing: Entity,
        candidate: EntityCandidate
    ) -> tuple[bool, List[str]]:
        """LLM 기반 병합 검증"""
        prompt = f"""다음 두 엔티티가 동일한 개념을 나타내는지 분석하세요.

엔티티 1 (기존):
- 이름: {existing.canonical_name}
- 유형: {existing.entity_type}
- 설명: {existing.description or '없음'}
- 별칭: {', '.join(existing.aliases) if existing.aliases else '없음'}

엔티티 2 (후보):
- 이름: {candidate.name}
- 유형: {candidate.entity_type}
- 출처: {candidate.source_context[:200] if candidate.source_context else '없음'}

JSON 형식으로 응답하세요:
{{
    "is_same": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "판단 근거",
    "issues": ["병합 시 주의사항"]
}}
"""
        score, reasons = await self._llm_validation(existing, prompt)
        return score >= 0.7, reasons
    
    # ========== Similarity Calculation ==========
    
    def calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity
    ) -> float:
        """
        두 엔티티 간 유사도 계산
        """
        scores = []
        
        # 1. 이름 유사도
        name_sim = SequenceMatcher(
            None,
            entity1.canonical_name.lower(),
            entity2.canonical_name.lower()
        ).ratio()
        scores.append(name_sim * 0.4)
        
        # 2. 별칭 유사도
        alias_sim = 0.0
        for a1 in [entity1.canonical_name] + entity1.aliases:
            for a2 in [entity2.canonical_name] + entity2.aliases:
                sim = SequenceMatcher(None, a1.lower(), a2.lower()).ratio()
                alias_sim = max(alias_sim, sim)
        scores.append(alias_sim * 0.3)
        
        # 3. 도메인 태그 일치도
        if entity1.domain_tags and entity2.domain_tags:
            common = set(entity1.domain_tags) & set(entity2.domain_tags)
            total = set(entity1.domain_tags) | set(entity2.domain_tags)
            tag_sim = len(common) / len(total) if total else 0.0
        else:
            tag_sim = 0.5  # 태그 없으면 중립
        scores.append(tag_sim * 0.2)
        
        # 4. 엔티티 타입 일치
        type_sim = 1.0 if entity1.entity_type == entity2.entity_type else 0.0
        scores.append(type_sim * 0.1)
        
        return sum(scores)
    
    # ========== Domain Dictionary Integration ==========
    
    async def resolve_to_canonical(
        self,
        entity: Entity
    ) -> Optional[Entity]:
        """
        v4.2: Entity를 Domain Dictionary의 canonical로 해결
        
        Returns:
            정규화된 Entity 또는 None (신규 엔티티)
        """
        if not self.domain_dictionary:
            return None
        
        try:
            canonical = await self.domain_dictionary.get_canonical(entity.canonical_name)
            
            if canonical:
                # 기존 엔티티 찾음 - 별칭으로 추가 가능
                logger.info(
                    "entity_resolved_to_canonical",
                    input_name=entity.canonical_name,
                    canonical_name=canonical.canonical_name,
                    canonical_id=canonical.entity_id
                )
                
                # 새 별칭 추가
                if entity.canonical_name.lower() != canonical.canonical_name.lower():
                    await self.domain_dictionary.add_alias(
                        canonical.entity_id,
                        entity.canonical_name
                    )
                
                # 정규화된 엔티티 반환 (ID는 canonical의 것 사용)
                return Entity(
                    id=canonical.entity_id,
                    canonical_name=canonical.canonical_name,
                    entity_type=entity.entity_type,
                    aliases=list(set(entity.aliases + canonical.aliases)),
                    domain_tags=list(set(entity.domain_tags + canonical.tags)),
                    description=entity.description or canonical.description
                )
            
            return None  # 신규 엔티티
            
        except Exception as e:
            logger.warning("entity_canonical_resolution_failed", error=str(e))
            return None
    
    # ========== Feedback ==========
    
    async def record_entity_feedback(
        self,
        entity_id: str,
        entity_type: str,
        approved: bool,
        reason: Optional[str] = None
    ):
        """Entity 피드백 기록 (RL 학습용)"""
        await self.record_feedback(
            item_id=entity_id,
            approved=approved,
            reason=reason
        )
        
        # 엔티티 유형별 추적
        self._feedback_history[-1]["entity_type"] = entity_type
