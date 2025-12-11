"""
Fragment Validator - v4.2 Validation Pyramid
계획서 2.3: Validator (Rule → Small Model → LLM + RL)

v4.2 핵심:
- L0: 문법/형식 규칙 (SVO 구조, 최소 길이, 토큰 타입)
- L1: Small classifier (관계 기술인가? 잡음인가?)
- L2: LLM semantic validity (인과/사실/조건/결과 분류)
"""
from typing import Any, List, Dict, Optional, TYPE_CHECKING

from config.constants import FragmentType, FeasibilityLevel, ValidationLayer
from src.validators.base import BaseValidator, ValidationResult, LayerResult, LayerDecision
from src.domain.fragments import Fragment
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.services.llm_service import LLMService
    from src.storage.policy_store import PolicyStore

logger = get_logger(__name__)


class FragmentValidator(BaseValidator):
    """
    Fragment 검증기 - v4.2 Validation Pyramid
    
    L0 (Rule Filter):
    - SVO 구조 검증 (Subject-Verb-Object)
    - 최소/최대 길이 검증
    - 필수 필드 존재 검증
    - 신뢰도 임계값 검증
    
    L1 (Small Model):
    - "이 문장이 관계 기술인가?" 분류
    - 잡음 필터링
    
    L2 (LLM + RL):
    - Semantic validity 검증
    - "인과/사실/조건/결과 중 하나로 분류 가능한가?"
    """
    
    # Fragment 유형별 필수 필드
    REQUIRED_FIELDS_BY_TYPE = {
        FragmentType.FACT: ["subject", "predicate", "object"],
        FragmentType.MECHANISM: ["subject", "predicate", "object", "direction"],
        FragmentType.CONDITION: ["subject", "predicate", "object", "condition"],
        FragmentType.OUTCOME: ["subject", "predicate", "object", "condition"],
    }
    
    # v4.2 L0 Rule: 최소/최대 길이
    MIN_FIELD_LENGTH = 2
    MAX_FIELD_LENGTH = 200
    MIN_EVIDENCE_LENGTH = 10
    MIN_CONFIDENCE = 0.3
    
    # L0 Stopwords (reject 대상)
    STOPWORDS = {"the", "a", "an", "is", "are", "것", "이", "그", "저", "등"}
    
    def __init__(
        self,
        llm_service: Optional["LLMService"] = None,
        policy_store: Optional["PolicyStore"] = None
    ):
        super().__init__(
            llm_service=llm_service,
            policy_store=policy_store,
            validator_name="FragmentValidator"
        )
    
    # ========== L0: Rule Check ==========
    
    async def rule_check(self, item: Any) -> LayerResult:
        """
        L0: Rule-based 빠른 필터링
        
        검증 항목:
        - 필수 필드 존재
        - SVO 구조 검증
        - 최소/최대 길이
        - 신뢰도 임계값
        """
        if not isinstance(item, Fragment):
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["Invalid input: expected Fragment"],
                details={"error": "type_mismatch"}
            )
        
        fragment = item
        score = 1.0
        reasons: List[str] = []
        
        # 1. 필수 필드 검증
        required_fields = self.REQUIRED_FIELDS_BY_TYPE.get(
            fragment.fragment_type,
            ["subject", "predicate", "object"]
        )
        
        for field_name in required_fields:
            value = getattr(fragment, field_name, None)
            if not value or (isinstance(value, str) and not value.strip()):
                score -= 0.2
                reasons.append(f"필수 필드 누락: {field_name}")
        
        # 필수 필드 50% 이상 누락이면 즉시 reject
        if score <= 0.6:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details={"rule": "missing_required_fields"}
            )
        
        # 2. SVO 길이 검증
        for field_name in ["subject", "object"]:
            value = getattr(fragment, field_name, None)
            if value:
                if len(value) < self.MIN_FIELD_LENGTH:
                    score -= 0.1
                    reasons.append(f"{field_name} 너무 짧음 (< {self.MIN_FIELD_LENGTH})")
                if len(value) > self.MAX_FIELD_LENGTH:
                    score -= 0.1
                    reasons.append(f"{field_name} 너무 김 (> {self.MAX_FIELD_LENGTH})")
        
        # 3. Subject == Object 동일성 체크 (Self-loop 방지)
        if fragment.subject and fragment.object:
            if fragment.subject.lower().strip() == fragment.object.lower().strip():
                score -= 0.3
                reasons.append("Subject와 Object가 동일함 (Self-loop)")
                
        # 4. Evidence 검증
        if not fragment.evidence or len(fragment.evidence) < self.MIN_EVIDENCE_LENGTH:
            score -= 0.15
            reasons.append(f"Evidence 부족 (< {self.MIN_EVIDENCE_LENGTH}자)")
        
        # 5. Confidence 검증 (LLM 추출 신뢰도)
        if fragment.confidence < self.MIN_CONFIDENCE:
            score -= 0.2
            reasons.append(f"LLM 신뢰도 낮음: {fragment.confidence:.2f} < {self.MIN_CONFIDENCE}")
            
        # 6. Stopword 전용 Subject/Object reject
        if fragment.subject and fragment.subject.lower().strip() in self.STOPWORDS:
            score -= 0.3
            reasons.append(f"Subject가 stopword: {fragment.subject}")
            
        if fragment.object and fragment.object.lower().strip() in self.STOPWORDS:
            score -= 0.3
            reasons.append(f"Object가 stopword: {fragment.object}")
        
        # 7. MECHANISM 타입 방향 검증
        if fragment.fragment_type == FragmentType.MECHANISM:
            if not fragment.direction:
                score -= 0.1
                reasons.append("Mechanism에 방향 정보 없음")
            elif fragment.direction not in ["proportional", "inverse", "neutral"]:
                score -= 0.05
                reasons.append(f"알 수 없는 방향: {fragment.direction}")
        
        # 8. CONDITION/OUTCOME 조건 검증
        if fragment.fragment_type in [FragmentType.CONDITION, FragmentType.OUTCOME]:
            if not fragment.condition:
                score -= 0.1
                reasons.append(f"{fragment.fragment_type.value}에 조건 누락")
        
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
            details={"fragment_type": fragment.fragment_type.value}
        )
    
    # ========== L1: Small Model Check ==========
    
    async def _call_small_model(self, item: Any) -> LayerResult:
        """
        L1: Small Model 검증
        
        "이 문장이 관계 기술인가?" 분류
        점진 도입 가능 - 기본은 pass-through
        """
        fragment = item
        
        # Small Model endpoint가 없으면 pass-through
        if not self.settings.small_model_endpoint:
            return LayerResult(
                score=0.7,
                decision=LayerDecision.PASS,
                reasons=[],
                details={"small_model": "pass_through"}
            )
        
        # TODO: Small Model API 호출 구현
        # 현재는 간단한 휴리스틱으로 대체
        score = 0.7
        reasons = []
        
        # 휴리스틱: predicate가 너무 짧으면 의심
        if fragment.predicate and len(fragment.predicate) < 3:
            score -= 0.2
            reasons.append("Predicate가 너무 짧음 (관계 기술 의심)")
        
        if score < self.settings.small_model_reject_threshold:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details={"small_model": "heuristic_reject"}
            )
        
        return LayerResult(
            score=score,
            decision=LayerDecision.PASS,
            reasons=reasons,
            details={"small_model": "heuristic_pass"}
        )
    
    # ========== L2: LLM Check ==========
    
    def _build_llm_prompt(self, item: Any) -> str:
        """L2: LLM 검증 프롬프트 생성"""
        fragment = item
        return f"""다음 지식 Fragment의 의미적 유효성을 평가하세요.

Fragment 정보:
- 유형: {fragment.fragment_type.value}
- Subject: {fragment.subject}
- Predicate: {fragment.predicate}
- Object: {fragment.object}
- 조건: {fragment.condition or '없음'}
- 방향: {fragment.direction or '없음'}
- 근거: {fragment.evidence}

평가 기준:
1. 이 문장은 인과/사실/조건/결과 중 하나로 분류 가능한가?
2. Subject-Predicate-Object 관계가 의미적으로 일관성 있는가?
3. 근거(Evidence)가 Fragment 내용을 뒷받침하는가?
4. Fragment 유형이 내용과 일치하는가?

JSON 형식으로 응답하세요:
{{
    "score": 0.0-1.0,
    "is_valid": true/false,
    "category": "causal/factual/conditional/outcome/unknown",
    "issues": ["발견된 문제점 목록"],
    "reasoning": "평가 근거"
}}
"""
    
    def _history_score(self, item: Any) -> float:
        """Fragment 유형별 히스토리 점수"""
        fragment = item
        
        # 같은 유형의 피드백 필터
        similar_feedbacks = [
            f for f in self._feedback_history
            if f.get("fragment_type") == fragment.fragment_type.value
        ]
        
        if not similar_feedbacks:
            return 0.5  # 기본값
        
        # 승인률 계산
        approved = sum(1 for f in similar_feedbacks if f.get("approved", False))
        return approved / len(similar_feedbacks)
    
    # ========== Batch Validation ==========
    
    async def validate_batch(
        self,
        fragments: List[Fragment],
        use_pyramid: bool = True,
        use_llm: bool = None  # 레거시 호환성
    ) -> List[ValidationResult]:
        """
        다중 Fragment 검증
        
        Args:
            fragments: 검증할 Fragment 리스트
            use_pyramid: v4.2 Pyramid 사용 여부 (기본 True)
            use_llm: 레거시 파라미터 (use_pyramid=False로 매핑)
        """
        # 레거시 호환성: use_llm=False면 use_pyramid=False로
        if use_llm is not None:
            use_pyramid = use_llm
        
        results = []
        for fragment in fragments:
            if use_pyramid:
                result = await self.validate(fragment)
            else:
                # 레거시: Rule만 사용 (빠른 검증)
                rule_result = await self.rule_check(fragment)
                result = ValidationResult(
                    is_valid=rule_result.decision != LayerDecision.REJECT,
                    score=rule_result.score,
                    reasons=rule_result.reasons,
                    details=rule_result.details,
                    layer=ValidationLayer.RULE,
                    rejected_early=rule_result.decision == LayerDecision.REJECT
                )
            results.append(result)
        return results
    
    # ========== 레거시 호환성 ==========
    
    async def validate_fragment(
        self,
        fragment: Fragment,
        use_llm: bool = True
    ) -> ValidationResult:
        """
        레거시 호환: Fragment 검증
        v4.2에서는 validate()로 위임
        """
        if use_llm:
            return await self.validate(fragment)
        else:
            # Rule만 사용
            rule_result = await self.rule_check(fragment)
            return ValidationResult(
                is_valid=rule_result.decision != LayerDecision.REJECT,
                score=rule_result.score,
                reasons=rule_result.reasons,
                details={
                    "rule_score": rule_result.score,
                    "llm_score": 0.7,
                    "history_score": 0.5,
                    **rule_result.details
                },
                layer=ValidationLayer.RULE,
                rejected_early=rule_result.decision == LayerDecision.REJECT
            )
    
    # ========== Feedback ==========
    
    async def record_fragment_feedback(
        self,
        fragment_id: str,
        fragment_type: FragmentType,
        approved: bool,
        reason: Optional[str] = None
    ):
        """
        Fragment 피드백 기록 (RL 학습용)
        """
        await self.record_feedback(
            item_id=fragment_id,
            approved=approved,
            reason=reason
        )
        
        # Fragment 유형별 추적
        self._feedback_history[-1]["fragment_type"] = fragment_type.value


# ========== 하위 호환성 ==========

async def validate_fragment_legacy(
    fragment: Fragment,
    llm_service: Optional["LLMService"] = None
) -> ValidationResult:
    """레거시 함수 호환성 유지"""
    validator = FragmentValidator(llm_service=llm_service)
    return await validator.validate(fragment)
