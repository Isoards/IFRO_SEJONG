"""
엔티티 정의
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from config.constants import ValidationStatus


class EntityCandidate(BaseModel):
    """엔티티 후보 - Generator(LLM)가 생성"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description="엔티티 이름")
    aliases: List[str] = Field(default_factory=list, description="별칭들")
    context: str = Field(description="추출된 문맥")
    source_document_id: str = Field(description="출처 문서 ID")
    source_block_id: str = Field(description="출처 블록 ID")
    
    # LLM이 생성한 메타데이터
    entity_type: Optional[str] = Field(default=None, description="엔티티 유형 (개념/인물/조직 등)")
    domain_tags: List[str] = Field(default_factory=list, description="도메인 태그")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="LLM 신뢰도")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    """
    v5.2 검증된 엔티티
    One Source of Truth: 동일 개념은 하나의 Entity만 존재
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    canonical_name: str = Field(description="정규화된 이름")
    aliases: List[str] = Field(default_factory=list, description="모든 별칭들")
    entity_type: Optional[str] = Field(default=None, description="엔티티 유형")
    domain_tags: List[str] = Field(default_factory=list, description="도메인 태그")
    
    # v5.2: 임베딩
    embedding: Optional[List[float]] = Field(default=None, description="벡터 임베딩")
    
    # v5.2: 안정성 점수 (0~1)
    stability_score: float = Field(default=0.5, ge=0.0, le=1.0, description="엔티티 안정성")
    
    # 검증 정보
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    validation_score: float = Field(default=0.0, description="RL Validator 점수")
    merged_from: List[str] = Field(default_factory=list, description="병합된 후보 ID들")
    
    # v5.2: 병합 이력 (상세)
    merge_history: List[Dict[str, Any]] = Field(default_factory=list, description="병합 이력")
    
    # 메타데이터
    description: Optional[str] = Field(default=None, description="엔티티 설명")
    properties: Dict[str, Any] = Field(default_factory=dict, description="추가 속성")
    
    # 통계
    mention_count: int = Field(default=0, description="언급 횟수")
    relation_count: int = Field(default=0, description="관계 수")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_alias(self, alias: str) -> None:
        """별칭 추가 (중복 제거)"""
        if alias not in self.aliases and alias != self.canonical_name:
            self.aliases.append(alias)
            self.updated_at = datetime.utcnow()
    
    def merge_with(self, other: "Entity") -> None:
        """v5.2: 다른 엔티티와 병합 (이력 기록)"""
        self.aliases.append(other.canonical_name)
        self.aliases.extend(other.aliases)
        self.aliases = list(set(self.aliases))  # 중복 제거
        
        # 도메인 태그 병합
        self.domain_tags = list(set(self.domain_tags + other.domain_tags))
        
        # 통계 업데이트
        self.mention_count += other.mention_count
        self.relation_count += other.relation_count
        
        self.merged_from.append(other.id)
        
        # v5.2: 병합 이력 기록
        self.merge_history.append({
            "merged_entity_id": other.id,
            "merged_entity_name": other.canonical_name,
            "timestamp": datetime.utcnow().isoformat(),
            "aliases_added": other.aliases
        })
        
        # v5.2: 안정성 점수 조정 (병합 시 약간 감소)
        self.stability_score = max(0.0, self.stability_score - 0.05)
        
        self.updated_at = datetime.utcnow()
