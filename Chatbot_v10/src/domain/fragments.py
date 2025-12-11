"""
Fragment Schema 정의
계획서 2.2: Extraction Layer – Fragment Schema 기반 LLM 추출
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from config.constants import FragmentType, ValidationStatus


class Block(BaseModel):
    """문서의 구조적 단위 (섹션, 단락, 표 등)"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    block_type: str = Field(description="블록 유형 (paragraph, table, list, heading 등)")
    content: str = Field(description="블록 내용")
    order: int = Field(description="문서 내 순서")
    level: int = Field(default=0, description="계층 수준 (heading의 경우)")
    
    # 메타데이터
    parent_id: Optional[str] = Field(default=None, description="부모 블록 ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructuredDoc(BaseModel):
    """
    구조화된 문서 - Boundary Layer 출력
    계획서 2.1: 구조 보존형 Parser 결과
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # 문서 정보
    source_path: str = Field(description="원본 파일 경로")
    source_type: str = Field(description="파일 유형 (pdf, docx, html 등)")
    title: Optional[str] = Field(default=None, description="문서 제목")
    
    # 구조화된 블록들
    blocks: List[Block] = Field(default_factory=list, description="문서 블록들")
    
    # 메타데이터 (계획서 2.1: 작성자/날짜/출처)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="문서 메타데이터")
    
    # 처리 상태
    processed: bool = Field(default=False, description="처리 완료 여부")
    fragment_count: int = Field(default=0, description="추출된 Fragment 수")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_block_by_id(self, block_id: str) -> Optional[Block]:
        """ID로 블록 조회"""
        for block in self.blocks:
            if block.id == block_id:
                return block
        return None


class Fragment(BaseModel):
    """
    v5.2 지식 Fragment - LLM이 생성한 지식 조각
    
    Fragment 유형:
    - FACT: A == B (사실 관계)
    - MECHANISM: A ↗ B ↘ (인과성/비례/반비례)
    - CONDITION: X일 때 A는 B로 변화
    - OUTCOME: 조건 충족 시 C 발생
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Fragment Schema 핵심 필드
    fragment_type: FragmentType = Field(description="Fragment 유형")
    subject: str = Field(description="주제 엔티티")
    predicate: str = Field(description="관계/동작")
    object: str = Field(description="대상 엔티티")
    
    # CONDITION/OUTCOME 용 추가 필드
    condition: Optional[str] = Field(default=None, description="조건 (CONDITION/OUTCOME)")
    
    # v5.2: 조건 목록 (복수 조건 지원)
    conditions: List[str] = Field(default_factory=list, description="조건 목록")
    
    # MECHANISM 용 추가 필드 (레거시)
    direction: Optional[str] = Field(default=None, description="영향 방향 (proportional/inverse)")
    magnitude: Optional[str] = Field(default=None, description="영향 크기 (high/medium/low)")
    
    # v5.2: 정규화된 direction (-1, 0, +1)
    direction_normalized: int = Field(default=0, ge=-1, le=1, description="정규화된 방향")
    
    # 출처 정보
    source_document_id: str = Field(description="출처 문서 ID")
    source_block_id: str = Field(description="출처 블록 ID")
    evidence: str = Field(description="근거 텍스트")
    
    # LLM 신뢰도 (v5.2: confidence_raw)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 검증 상태
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    validation_score: float = Field(default=0.0, description="Validator 점수")
    validation_notes: List[str] = Field(default_factory=list, description="검증 메모")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def normalize_direction(self):
        """v5.2: direction 필드에서 direction_normalized 계산"""
        if self.direction in {'inverse', '-', 'negative', 'decreases'}:
            self.direction_normalized = -1
        elif self.direction in {'proportional', '+', 'positive', 'increases'}:
            self.direction_normalized = 1
        else:
            self.direction_normalized = 0
    
    def to_triple(self) -> tuple[str, str, str]:
        """SPO 트리플로 변환"""
        return (self.subject, self.predicate, self.object)
    
    def get_entities(self) -> List[str]:
        """관련 엔티티 목록 반환"""
        entities = [self.subject, self.object]
        if self.condition:
            entities.append(self.condition)
        return entities
