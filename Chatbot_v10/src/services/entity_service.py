"""
Entity Resolution 서비스
계획서 2.3: Generator + Validator 구조
"""
from typing import List, Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

from config.settings import get_settings
from config.constants import ValidationStatus
from src.domain.entities import Entity, EntityCandidate
from src.services.llm_service import LLMService
from src.validators.entity_validator import EntityValidator
from src.shared.logging import get_logger, log_error
from src.shared.types import Result

logger = get_logger(__name__)


class EntityService:
    """
    Entity Resolution 서비스
    
    Generator(LLM) + Validator(RL + 규칙 기반) 구조

    계획서 2.3:
    1) Generator (LLM): 엔티티 후보 추출, 동일 엔티티 후보 리스트 생성
    2) Validator (RL + 규칙): Entity Resolution Score 계산
    
    원칙 4: 단일 책임 - Entity Resolution만 담당
    """
    
    def __init__(self, llm_service: LLMService, validator: EntityValidator):
        self.llm = llm_service
        self.validator = validator
        self.settings = get_settings()
        
        # 정규화된 엔티티 저장소 (One Source of Truth)
        self._entities: Dict[str, Entity] = {}
        self._name_index: Dict[str, str] = {}  # name/alias -> entity_id
    
    async def resolve_candidates(
        self,
        candidates: List[EntityCandidate]
    ) -> Result[List[Entity]]:
        """
        Entity 후보들을 정규화된 Entity로 변환
        
        Args:
            candidates: Entity 후보 리스트
        
        Returns:
            Result[List[Entity]]: 정규화된 Entity 리스트
        """
        resolved_entities: List[Entity] = []
        
        try:
            for candidate in candidates:
                # 기존 엔티티와 매칭 시도
                match_result = await self._find_matching_entity(candidate)
                
                if match_result:
                    existing_entity, confidence = match_result
                    
                    # Validator로 병합 여부 결정
                    should_merge = await self.validator.validate_merge(
                        existing_entity, candidate, confidence
                    )
                    
                    if should_merge:
                        # 기존 엔티티에 병합
                        existing_entity.add_alias(candidate.name)
                        existing_entity.mention_count += 1
                        resolved_entities.append(existing_entity)
                        continue
                
                # 새 엔티티 생성
                new_entity = await self._create_entity(candidate)
                
                # Validator로 검증
                validation_result = await self.validator.validate_entity(new_entity)
                # ValidationResult 객체에서 score와 is_valid 추출
                new_entity.validation_score = validation_result.score
                new_entity.validation_status = (
                    ValidationStatus.APPROVED if validation_result.is_valid
                    else ValidationStatus.NEEDS_REVIEW
                )
                
                # 저장
                self._entities[new_entity.id] = new_entity
                self._name_index[new_entity.canonical_name.lower()] = new_entity.id
                for alias in new_entity.aliases:
                    self._name_index[alias.lower()] = new_entity.id
                
                resolved_entities.append(new_entity)
            
            logger.info(
                "entities_resolved",
                candidate_count=len(candidates),
                resolved_count=len(resolved_entities)
            )
            
            return Result.ok(resolved_entities)
            
        except Exception as e:
            log_error(logger, e, {"candidate_count": len(candidates)})
            return Result.fail(
                error=str(e),
                error_code="ENTITY_RESOLUTION_FAILED"
            )
    
    async def _find_matching_entity(
        self,
        candidate: EntityCandidate
    ) -> Optional[Tuple[Entity, float]]:
        """
        후보와 매칭되는 기존 엔티티 찾기
        
        Returns:
            (Entity, confidence) or None
        """
        name_lower = candidate.name.lower()
        
        # 1. 정확한 이름 매칭
        if name_lower in self._name_index:
            entity_id = self._name_index[name_lower]
            entity = self._entities.get(entity_id)
            if entity:
                return (entity, 1.0)
        
        # 2. 문자열 유사도 기반 매칭
        best_match: Optional[Tuple[Entity, float]] = None
        
        for entity in self._entities.values():
            # 이름 유사도
            name_sim = self._calculate_string_similarity(
                name_lower, entity.canonical_name.lower()
            )
            
            # 별칭 유사도
            alias_sim = max(
                (self._calculate_string_similarity(name_lower, alias.lower())
                 for alias in entity.aliases),
                default=0.0
            )
            
            max_sim = max(name_sim, alias_sim)
            
            if max_sim >= self.settings.entity_similarity_threshold:
                if best_match is None or max_sim > best_match[1]:
                    best_match = (entity, max_sim)
        
        if best_match:
            # LLM으로 추가 검증
            llm_result = await self.llm.resolve_entities(
                entity1=candidate.name,
                context1=candidate.context,
                entity2=best_match[0].canonical_name,
                context2=best_match[0].description or ""
            )
            
            if llm_result.get("is_same", False):
                llm_confidence = llm_result.get("confidence", 0.5)
                # 문자열 유사도와 LLM 신뢰도 결합
                combined_confidence = (best_match[1] + llm_confidence) / 2
                return (best_match[0], combined_confidence)
        
        return None
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """문자열 유사도 계산 (SequenceMatcher)"""
        return SequenceMatcher(None, s1, s2).ratio()
    
    async def _create_entity(self, candidate: EntityCandidate) -> Entity:
        """후보에서 Entity 생성"""
        return Entity(
            canonical_name=candidate.name,
            aliases=candidate.aliases.copy(),
            entity_type=candidate.entity_type or "concept",  # 기본값 설정
            domain_tags=candidate.domain_tags.copy(),
            description=candidate.context[:200] if candidate.context else None,
            mention_count=1,
        )
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """ID로 엔티티 조회"""
        return self._entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """이름으로 엔티티 조회 (별칭 포함)"""
        entity_id = self._name_index.get(name.lower())
        if entity_id:
            return self._entities.get(entity_id)
        return None
    
    def get_all_entities(self) -> List[Entity]:
        """모든 엔티티 조회"""
        return list(self._entities.values())
    
    async def merge_entities(
        self,
        primary_id: str,
        secondary_id: str
    ) -> Result[Entity]:
        """
        두 엔티티 수동 병합 (Admin 기능)
        """
        primary = self._entities.get(primary_id)
        secondary = self._entities.get(secondary_id)
        
        if not primary or not secondary:
            return Result.fail(
                error="엔티티를 찾을 수 없습니다",
                error_code="ENTITY_NOT_FOUND"
            )
        
        # 병합
        primary.merge_with(secondary)
        
        # 인덱스 업데이트
        for alias in secondary.aliases + [secondary.canonical_name]:
            self._name_index[alias.lower()] = primary_id
        
        # secondary 삭제
        del self._entities[secondary_id]
        
        logger.info(
            "entities_merged",
            primary_id=primary_id,
            secondary_id=secondary_id
        )
        
        return Result.ok(primary)
    
    async def update_entity(
        self,
        entity_id: str,
        updates: Dict[str, Any]
    ) -> Result[Entity]:
        """
        엔티티 업데이트 (Admin 기능)
        """
        entity = self._entities.get(entity_id)
        if not entity:
            return Result.fail(
                error="엔티티를 찾을 수 없습니다",
                error_code="ENTITY_NOT_FOUND"
            )
        
        # 허용된 필드만 업데이트
        allowed_fields = {"canonical_name", "entity_type", "domain_tags", "description"}
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(entity, field, value)
        
        # 이름 변경 시 인덱스 업데이트
        if "canonical_name" in updates:
            # 기존 인덱스 삭제 후 재등록
            for name, eid in list(self._name_index.items()):
                if eid == entity_id:
                    del self._name_index[name]
            
            self._name_index[entity.canonical_name.lower()] = entity_id
            for alias in entity.aliases:
                self._name_index[alias.lower()] = entity_id
        
        return Result.ok(entity)
