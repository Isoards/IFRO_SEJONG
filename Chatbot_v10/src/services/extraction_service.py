"""
Fragment 추출 서비스 - Extraction Layer
계획서 2.2: Fragment Schema 기반 LLM 추출 (Generator)
"""
from typing import List, Optional
from datetime import datetime

from config.constants import FragmentType, ValidationStatus
from src.domain.fragments import Fragment, StructuredDoc, Block
from src.domain.entities import EntityCandidate
from src.services.llm_service import LLMService
from src.shared.logging import get_logger, log_error
from src.shared.types import Result

logger = get_logger(__name__)


class ExtractionService:
    """
    Extraction Layer - Fragment Schema 기반 LLM 추출
    
    역할: Generator - 후보 생성만 담당
    검증은 Validator가 수행
    
    원칙 4: 단일 책임 - Fragment/Entity 추출만 담당
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def extract_from_document(
        self,
        doc: StructuredDoc
    ) -> Result[tuple[List[Fragment], List[EntityCandidate]]]:
        """
        문서에서 Fragment와 Entity 후보 추출
        
        Args:
            doc: 구조화된 문서
        
        Returns:
            Result[(fragments, entity_candidates)]
        """
        all_fragments: List[Fragment] = []
        all_entities: List[EntityCandidate] = []
        
        try:
            for block in doc.blocks:
                # 블록 단위로 추출
                result = await self.extract_from_block(block, doc.id)
                
                if result.success and result.data:
                    fragments, entities = result.data
                    all_fragments.extend(fragments)
                    all_entities.extend(entities)
            
            # 문서의 fragment 수 업데이트
            doc.fragment_count = len(all_fragments)
            
            logger.info(
                "extraction_complete",
                document_id=doc.id,
                fragment_count=len(all_fragments),
                entity_count=len(all_entities)
            )
            
            return Result.ok((all_fragments, all_entities))
            
        except Exception as e:
            log_error(logger, e, {"document_id": doc.id})
            return Result.fail(
                error=str(e),
                error_code="EXTRACTION_FAILED"
            )
    
    async def extract_from_block(
        self,
        block: Block,
        document_id: str
    ) -> Result[tuple[List[Fragment], List[EntityCandidate]]]:
        """
        블록에서 Fragment와 Entity 추출
        
        Args:
            block: 문서 블록
            document_id: 문서 ID
        
        Returns:
            Result[(fragments, entity_candidates)]
        """
        fragments: List[Fragment] = []
        entities: List[EntityCandidate] = []
        
        # 내용이 너무 짧으면 스킵
        if len(block.content) < 20:
            return Result.ok((fragments, entities))
        
        try:
            # LLM으로 Fragment 추출
            extraction_result = await self.llm.extract_fragments(block.content)
            
            raw_fragments = extraction_result.get("fragments", [])
            
            for raw in raw_fragments:
                # Fragment 생성
                fragment = self._create_fragment(raw, block, document_id)
                if fragment:
                    fragments.append(fragment)
                    
                    # Fragment에서 Entity 후보 추출
                    entity_candidates = self._extract_entity_candidates(
                        fragment, block, document_id
                    )
                    entities.extend(entity_candidates)
            
            return Result.ok((fragments, entities))
            
        except Exception as e:
            log_error(logger, e, {"block_id": block.id})
            return Result.fail(
                error=str(e),
                error_code="BLOCK_EXTRACTION_FAILED"
            )
    
    def _create_fragment(
        self,
        raw: dict,
        block: Block,
        document_id: str
    ) -> Optional[Fragment]:
        """
        LLM 응답에서 Fragment 객체 생성
        """
        try:
            # Fragment 유형 매핑
            fragment_type_str = raw.get("type", "fact").lower()
            fragment_type_map = {
                "fact": FragmentType.FACT,
                "mechanism": FragmentType.MECHANISM,
                "condition": FragmentType.CONDITION,
                "outcome": FragmentType.OUTCOME,
            }
            fragment_type = fragment_type_map.get(fragment_type_str, FragmentType.FACT)
            
            # LLM이 리스트를 반환하는 경우 문자열로 변환
            def to_string(value) -> str:
                if value is None:
                    return ""
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return str(value)
            
            subject = to_string(raw.get("subject", ""))
            predicate = to_string(raw.get("predicate", ""))
            obj = to_string(raw.get("object", ""))
            condition = raw.get("condition")
            if isinstance(condition, list):
                condition = ", ".join(str(c) for c in condition)
            
            fragment = Fragment(
                fragment_type=fragment_type,
                subject=subject,
                predicate=predicate,
                object=obj,
                condition=condition,
                direction=raw.get("direction"),
                magnitude=raw.get("magnitude"),
                source_document_id=document_id,
                source_block_id=block.id,
                evidence=raw.get("evidence", block.content[:200]),
                confidence=float(raw.get("confidence", 0.5)),
                validation_status=ValidationStatus.PENDING,
            )
            
            # 유효성 검사
            if not fragment.subject or not fragment.object:
                return None
            
            return fragment
            
        except Exception as e:
            logger.warning("fragment_creation_failed", error=str(e), raw=raw)
            return None
    
    def _extract_entity_candidates(
        self,
        fragment: Fragment,
        block: Block,
        document_id: str
    ) -> List[EntityCandidate]:
        """
        Fragment에서 Entity 후보 추출
        """
        candidates: List[EntityCandidate] = []
        
        # Subject 엔티티
        if fragment.subject:
            candidates.append(EntityCandidate(
                name=fragment.subject,
                context=fragment.evidence,
                source_document_id=document_id,
                source_block_id=block.id,
                confidence=fragment.confidence,
            ))
        
        # Object 엔티티
        if fragment.object:
            candidates.append(EntityCandidate(
                name=fragment.object,
                context=fragment.evidence,
                source_document_id=document_id,
                source_block_id=block.id,
                confidence=fragment.confidence,
            ))
        
        # Condition 엔티티 (있는 경우)
        if fragment.condition:
            candidates.append(EntityCandidate(
                name=fragment.condition,
                context=fragment.evidence,
                source_document_id=document_id,
                source_block_id=block.id,
                confidence=fragment.confidence * 0.8,  # 조건은 신뢰도 낮게
            ))
        
        return candidates
    
    async def extract_from_text(
        self,
        text: str,
        source_name: str = "direct_input"
    ) -> Result[tuple[List[Fragment], List[EntityCandidate]]]:
        """
        텍스트에서 직접 추출
        
        Args:
            text: 원본 텍스트
            source_name: 출처 이름
        
        Returns:
            Result[(fragments, entity_candidates)]
        """
        # 임시 블록 생성
        block = Block(
            block_type="paragraph",
            content=text,
            order=0
        )
        
        return await self.extract_from_block(block, source_name)
