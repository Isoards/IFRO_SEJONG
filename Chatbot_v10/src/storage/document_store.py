"""
Document Store - 문서/Fragment 저장소
SQLite 기반

원칙 1: One Source of Truth - 문서 데이터의 단일 저장소
원칙 4: 단일 책임 - 문서 영속화만 담당
"""
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, Boolean, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select

from config.settings import get_settings
from config.constants import FragmentType, ValidationStatus
from src.domain.fragments import StructuredDoc, Block, Fragment
from src.storage.base import BaseStore, StoreError
from src.shared.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class StructuredDocModel(Base):
    """StructuredDoc DB 모델"""
    __tablename__ = "structured_docs"
    
    id = Column(String(36), primary_key=True)
    source_path = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=True)
    blocks = Column(Text, nullable=True)  # JSON array
    extra_metadata = Column(Text, nullable=True)  # JSON object
    processed = Column(Boolean, default=False)
    fragment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class FragmentModel(Base):
    """Fragment DB 모델"""
    __tablename__ = "fragments"
    
    id = Column(String(36), primary_key=True)
    fragment_type = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=False, index=True)
    predicate = Column(String(255), nullable=False)
    object = Column(String(255), nullable=False, index=True)
    condition = Column(Text, nullable=True)
    direction = Column(String(50), nullable=True)
    magnitude = Column(String(50), nullable=True)
    source_document_id = Column(String(36), nullable=False, index=True)
    source_block_id = Column(String(36), nullable=False)
    evidence = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default="pending")
    validation_score = Column(Float, default=0.0)
    validation_notes = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentStore(BaseStore[StructuredDoc]):
    """
    SQLite 기반 문서 저장소
    
    기능:
    - StructuredDoc 영속화
    - Fragment 영속화
    - 문서별 Fragment 조회
    """
    
    def __init__(self, db_url: Optional[str] = None):
        super().__init__("document")
        self.db_url = db_url or get_settings().database_url
        self.engine = None
        self.async_session = None
    
    async def initialize(self) -> None:
        """데이터베이스 초기화"""
        try:
            self.engine = create_async_engine(
                self.db_url,
                echo=False,
                future=True
            )
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("document_store_initialized", db_url=self.db_url)
            
        except Exception as e:
            raise self._handle_error(e, "initialize")
    
    async def save(self, doc: StructuredDoc) -> str:
        """문서 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    model = StructuredDocModel(
                        id=doc.id,
                        source_path=doc.source_path,
                        source_type=doc.source_type,
                        title=doc.title,
                        blocks=json.dumps(
                            [b.model_dump() for b in doc.blocks],
                            ensure_ascii=False
                        ),
                        extra_metadata=json.dumps(doc.metadata, ensure_ascii=False),
                        processed=doc.processed,
                        fragment_count=doc.fragment_count,
                    )
                    await session.merge(model)
            
            logger.info("document_saved", doc_id=doc.id, title=doc.title)
            return doc.id
            
        except Exception as e:
            raise self._handle_error(e, "save")
    
    async def get(self, doc_id: str) -> Optional[StructuredDoc]:
        """문서 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(StructuredDocModel).where(StructuredDocModel.id == doc_id)
                )
                model = result.scalar_one_or_none()
                
                if not model:
                    return None
                
                blocks_data = json.loads(model.blocks) if model.blocks else []
                blocks = [Block(**b) for b in blocks_data]
                
                return StructuredDoc(
                    id=model.id,
                    source_path=model.source_path,
                    source_type=model.source_type,
                    title=model.title,
                    blocks=blocks,
                    metadata=json.loads(model.extra_metadata) if model.extra_metadata else {},
                    processed=model.processed,
                    fragment_count=model.fragment_count,
                )
        except Exception as e:
            raise self._handle_error(e, "get")
    
    async def save_fragment(self, fragment: Fragment) -> str:
        """Fragment 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    model = FragmentModel(
                        id=fragment.id,
                        fragment_type=fragment.fragment_type.value,
                        subject=fragment.subject,
                        predicate=fragment.predicate,
                        object=fragment.object,
                        condition=fragment.condition,
                        direction=fragment.direction,
                        magnitude=fragment.magnitude,
                        source_document_id=fragment.source_document_id,
                        source_block_id=fragment.source_block_id,
                        evidence=fragment.evidence,
                        confidence=fragment.confidence,
                        validation_status=fragment.validation_status.value,
                        validation_score=fragment.validation_score,
                        validation_notes=json.dumps(fragment.validation_notes, ensure_ascii=False),
                    )
                    await session.merge(model)
            
            logger.debug("fragment_saved", fragment_id=fragment.id)
            return fragment.id
            
        except Exception as e:
            raise self._handle_error(e, "save_fragment")
    
    async def save_fragments(self, fragments: List[Fragment]) -> List[str]:
        """다중 Fragment 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    for fragment in fragments:
                        model = FragmentModel(
                            id=fragment.id,
                            fragment_type=fragment.fragment_type.value,
                            subject=fragment.subject,
                            predicate=fragment.predicate,
                            object=fragment.object,
                            condition=fragment.condition,
                            direction=fragment.direction,
                            magnitude=fragment.magnitude,
                            source_document_id=fragment.source_document_id,
                            source_block_id=fragment.source_block_id,
                            evidence=fragment.evidence,
                            confidence=fragment.confidence,
                            validation_status=fragment.validation_status.value,
                            validation_score=fragment.validation_score,
                            validation_notes=json.dumps(fragment.validation_notes, ensure_ascii=False),
                        )
                        await session.merge(model)
            
            logger.info("fragments_saved", count=len(fragments))
            return [f.id for f in fragments]
            
        except Exception as e:
            raise self._handle_error(e, "save_fragments")
    
    async def get_fragment(self, fragment_id: str) -> Optional[Fragment]:
        """Fragment 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(FragmentModel).where(FragmentModel.id == fragment_id)
                )
                model = result.scalar_one_or_none()
                
                if not model:
                    return None
                
                return self._model_to_fragment(model)
        except Exception as e:
            raise self._handle_error(e, "get_fragment")
    
    async def get_fragments_by_document(self, doc_id: str) -> List[Fragment]:
        """문서별 Fragment 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(FragmentModel).where(FragmentModel.source_document_id == doc_id)
                )
                models = result.scalars().all()
                return [self._model_to_fragment(m) for m in models]
        except Exception as e:
            raise self._handle_error(e, "get_fragments_by_document")
    
    async def get_fragments_by_status(
        self,
        status: ValidationStatus,
        limit: int = 100
    ) -> List[Fragment]:
        """상태별 Fragment 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(FragmentModel)
                    .where(FragmentModel.validation_status == status.value)
                    .limit(limit)
                )
                models = result.scalars().all()
                return [self._model_to_fragment(m) for m in models]
        except Exception as e:
            raise self._handle_error(e, "get_fragments_by_status")
    
    async def update_fragment_status(
        self,
        fragment_id: str,
        status: ValidationStatus,
        score: float,
        notes: Optional[List[str]] = None
    ) -> bool:
        """Fragment 검증 상태 업데이트"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(FragmentModel).where(FragmentModel.id == fragment_id)
                    )
                    model = result.scalar_one_or_none()
                    
                    if model:
                        model.validation_status = status.value
                        model.validation_score = score
                        if notes:
                            model.validation_notes = json.dumps(notes, ensure_ascii=False)
                        return True
                    return False
        except Exception as e:
            raise self._handle_error(e, "update_fragment_status")
    
    def _model_to_fragment(self, model: FragmentModel) -> Fragment:
        """모델을 Fragment로 변환"""
        return Fragment(
            id=model.id,
            fragment_type=FragmentType(model.fragment_type),
            subject=model.subject,
            predicate=model.predicate,
            object=model.object,
            condition=model.condition,
            direction=model.direction,
            magnitude=model.magnitude,
            source_document_id=model.source_document_id,
            source_block_id=model.source_block_id,
            evidence=model.evidence,
            confidence=model.confidence,
            validation_status=ValidationStatus(model.validation_status),
            validation_score=model.validation_score,
            validation_notes=json.loads(model.validation_notes) if model.validation_notes else [],
        )
    
    async def delete(self, item_id: str) -> bool:
        """문서 또는 Fragment 삭제"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    # 문서 삭제 시도
                    result = await session.execute(
                        select(StructuredDocModel).where(StructuredDocModel.id == item_id)
                    )
                    doc = result.scalar_one_or_none()
                    if doc:
                        await session.delete(doc)
                        # 관련 Fragment도 삭제
                        fragments = await session.execute(
                            select(FragmentModel).where(FragmentModel.source_document_id == item_id)
                        )
                        for f in fragments.scalars().all():
                            await session.delete(f)
                        return True
                    
                    # Fragment 삭제 시도
                    result = await session.execute(
                        select(FragmentModel).where(FragmentModel.id == item_id)
                    )
                    fragment = result.scalar_one_or_none()
                    if fragment:
                        await session.delete(fragment)
                        return True
            
            return False
        except Exception as e:
            raise self._handle_error(e, "delete")
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[StructuredDoc]:
        """모든 문서 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(StructuredDocModel).offset(offset).limit(limit)
                )
                models = result.scalars().all()
                
                docs = []
                for model in models:
                    blocks_data = json.loads(model.blocks) if model.blocks else []
                    blocks = [Block(**b) for b in blocks_data]
                    
                    docs.append(StructuredDoc(
                        id=model.id,
                        source_path=model.source_path,
                        source_type=model.source_type,
                        title=model.title,
                        blocks=blocks,
                        metadata=json.loads(model.extra_metadata) if model.extra_metadata else {},
                        processed=model.processed,
                        fragment_count=model.fragment_count,
                    ))
                return docs
        except Exception as e:
            raise self._handle_error(e, "list_all")
    
    async def close(self) -> None:
        """연결 종료"""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("document_store_closed")
