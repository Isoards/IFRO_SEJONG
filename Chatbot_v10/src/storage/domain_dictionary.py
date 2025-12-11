"""
Domain Dictionary - v4.2
엔티티 정규화 및 별칭 관리

역할:
- canonical_name, alias, tags 관리
- Entity 생성/검증 시 항상 참조
- 약어/국가별 명칭/동의어 문제 해결
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
import json

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from config.settings import get_settings
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.services.llm_service import LLMService

logger = get_logger(__name__)
Base = declarative_base()


@dataclass
class CanonicalEntry:
    """정규화된 엔티티 항목"""
    entity_id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class DictionaryEntryModel(Base):
    """Domain Dictionary DB 모델"""
    __tablename__ = "domain_dictionary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String(36), unique=True, nullable=False, index=True)
    canonical_name = Column(String(255), nullable=False, index=True)
    aliases = Column(Text, nullable=True)  # JSON array
    tags = Column(Text, nullable=True)  # JSON array
    domain = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DomainDictionary:
    """
    Domain Dictionary - v4.2
    
    기능:
    - 정규 이름(canonical_name) 관리
    - 별칭(alias) 매핑
    - 도메인 태그 관리
    - 중복 엔티티 탐지
    
    사용 예:
    - "BOK" → "Bank of Korea"
    - "한국은행" → "Bank of Korea"
    - "Fed" → "Federal Reserve"
    """
    
    def __init__(self, db_url: Optional[str] = None):
        settings = get_settings()
        self.db_url = db_url or settings.database_url
        self._engine = None
        self._session_factory = None
        
        # 메모리 캐시 (빠른 조회용)
        self._cache: Dict[str, CanonicalEntry] = {}
        self._alias_index: Dict[str, str] = {}  # alias -> entity_id
    
    async def initialize(self):
        """데이터베이스 초기화"""
        self._engine = create_async_engine(self.db_url, echo=False)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 캐시 로드
        await self._load_cache()
        
        logger.info("domain_dictionary_initialized", entries=len(self._cache))
    
    async def _load_cache(self):
        """DB에서 캐시 로드"""
        async with self._session_factory() as session:
            result = await session.execute(select(DictionaryEntryModel))
            entries = result.scalars().all()
            
            for entry in entries:
                canonical = CanonicalEntry(
                    entity_id=entry.entity_id,
                    canonical_name=entry.canonical_name,
                    aliases=json.loads(entry.aliases) if entry.aliases else [],
                    tags=json.loads(entry.tags) if entry.tags else [],
                    domain=entry.domain,
                    description=entry.description,
                    created_at=entry.created_at
                )
                
                self._cache[entry.entity_id] = canonical
                
                # Alias 인덱스 구축
                self._alias_index[entry.canonical_name.lower()] = entry.entity_id
                for alias in canonical.aliases:
                    self._alias_index[alias.lower()] = entry.entity_id
    
    async def get_canonical(self, term: str) -> Optional[CanonicalEntry]:
        """
        용어로 정규 엔티티 조회
        
        Args:
            term: 검색할 용어 (이름 또는 별칭)
            
        Returns:
            CanonicalEntry 또는 None
        """
        term_lower = term.lower().strip()
        
        # 1. Alias 인덱스에서 검색
        entity_id = self._alias_index.get(term_lower)
        if entity_id:
            return self._cache.get(entity_id)
        
        # 2. 부분 매칭 시도
        for alias, eid in self._alias_index.items():
            if term_lower in alias or alias in term_lower:
                return self._cache.get(eid)
        
        return None
    
    async def get_by_id(self, entity_id: str) -> Optional[CanonicalEntry]:
        """ID로 정규 엔티티 조회"""
        return self._cache.get(entity_id)
    
    async def add_entry(
        self,
        entity_id: str,
        canonical_name: str,
        aliases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        description: Optional[str] = None
    ) -> CanonicalEntry:
        """
        새 엔트리 추가
        
        Args:
            entity_id: 엔티티 ID
            canonical_name: 정규 이름
            aliases: 별칭 리스트
            tags: 태그 리스트
            domain: 도메인 분류
            description: 설명
            
        Returns:
            생성된 CanonicalEntry
        """
        aliases = aliases or []
        tags = tags or []
        
        # DB 저장
        async with self._session_factory() as session:
            entry = DictionaryEntryModel(
                entity_id=entity_id,
                canonical_name=canonical_name,
                aliases=json.dumps(aliases, ensure_ascii=False),
                tags=json.dumps(tags, ensure_ascii=False),
                domain=domain,
                description=description
            )
            session.add(entry)
            await session.commit()
        
        # 캐시 업데이트
        canonical = CanonicalEntry(
            entity_id=entity_id,
            canonical_name=canonical_name,
            aliases=aliases,
            tags=tags,
            domain=domain,
            description=description,
            created_at=datetime.utcnow()
        )
        
        self._cache[entity_id] = canonical
        self._alias_index[canonical_name.lower()] = entity_id
        for alias in aliases:
            self._alias_index[alias.lower()] = entity_id
        
        logger.info(
            "dictionary_entry_added",
            entity_id=entity_id,
            canonical_name=canonical_name,
            aliases_count=len(aliases)
        )
        
        return canonical
    
    async def add_alias(self, entity_id: str, alias: str) -> bool:
        """
        기존 엔티티에 별칭 추가
        
        Args:
            entity_id: 엔티티 ID (canonical_id)
            alias: 추가할 별칭
            
        Returns:
            성공 여부
        """
        if entity_id not in self._cache:
            logger.warning("dictionary_alias_add_failed", reason="entity_not_found")
            return False
        
        canonical = self._cache[entity_id]
        alias_lower = alias.lower()
        
        # 이미 존재하는 별칭인지 확인
        if alias_lower in self._alias_index:
            existing_id = self._alias_index[alias_lower]
            if existing_id != entity_id:
                logger.warning(
                    "dictionary_alias_conflict",
                    alias=alias,
                    existing_entity=existing_id,
                    requested_entity=entity_id
                )
                return False
            return True  # 이미 같은 엔티티에 등록됨
        
        # DB 업데이트
        async with self._session_factory() as session:
            result = await session.execute(
                select(DictionaryEntryModel).where(
                    DictionaryEntryModel.entity_id == entity_id
                )
            )
            entry = result.scalar_one_or_none()
            
            if entry:
                aliases = json.loads(entry.aliases) if entry.aliases else []
                if alias not in aliases:
                    aliases.append(alias)
                    entry.aliases = json.dumps(aliases, ensure_ascii=False)
                    await session.commit()
        
        # 캐시 업데이트
        canonical.aliases.append(alias)
        self._alias_index[alias_lower] = entity_id
        
        logger.info("dictionary_alias_added", entity_id=entity_id, alias=alias)
        return True
    
    async def suggest_aliases(
        self,
        entity_name: str,
        llm_service: Optional["LLMService"] = None
    ) -> List[str]:
        """
        LLM을 사용해 별칭 후보 생성
        
        Args:
            entity_name: 엔티티 이름
            llm_service: LLM 서비스 (옵션)
            
        Returns:
            별칭 후보 리스트 (사용자 검수 필요)
        """
        if not llm_service:
            return []
        
        try:
            prompt = f"""다음 엔티티의 가능한 별칭(약어, 다른 명칭, 번역명 등)을 생성하세요.

엔티티: {entity_name}

JSON 형식으로 응답하세요:
{{
    "aliases": ["별칭1", "별칭2", "약어", ...],
    "reasoning": "별칭 선정 근거"
}}

주의: 실제로 사용되는 별칭만 제안하세요.
"""
            
            response = await llm_service.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.3
            )
            
            result = json.loads(response)
            return result.get("aliases", [])
            
        except Exception as e:
            logger.warning("dictionary_alias_suggestion_failed", error=str(e))
            return []
    
    async def find_duplicates(self, name: str, threshold: float = 0.8) -> List[CanonicalEntry]:
        """
        잠재적 중복 엔티티 탐지
        
        Args:
            name: 검색할 이름
            threshold: 유사도 임계값
            
        Returns:
            유사한 엔티티 리스트
        """
        from difflib import SequenceMatcher
        
        duplicates = []
        name_lower = name.lower()
        
        for entry in self._cache.values():
            # 정규 이름과 비교
            similarity = SequenceMatcher(
                None, name_lower, entry.canonical_name.lower()
            ).ratio()
            
            if similarity >= threshold:
                duplicates.append(entry)
                continue
            
            # 별칭과 비교
            for alias in entry.aliases:
                similarity = SequenceMatcher(None, name_lower, alias.lower()).ratio()
                if similarity >= threshold:
                    duplicates.append(entry)
                    break
        
        return duplicates
    
    async def list_by_domain(self, domain: str) -> List[CanonicalEntry]:
        """도메인별 엔티티 조회"""
        return [
            entry for entry in self._cache.values()
            if entry.domain == domain
        ]
    
    async def list_by_tag(self, tag: str) -> List[CanonicalEntry]:
        """태그별 엔티티 조회"""
        return [
            entry for entry in self._cache.values()
            if tag in entry.tags
        ]
    
    async def search(self, query: str, limit: int = 10) -> List[CanonicalEntry]:
        """전체 검색"""
        from difflib import SequenceMatcher
        
        query_lower = query.lower()
        scored_entries = []
        
        for entry in self._cache.values():
            max_score = SequenceMatcher(
                None, query_lower, entry.canonical_name.lower()
            ).ratio()
            
            for alias in entry.aliases:
                score = SequenceMatcher(None, query_lower, alias.lower()).ratio()
                max_score = max(max_score, score)
            
            if max_score > 0.3:
                scored_entries.append((max_score, entry))
        
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        total_entries = len(self._cache)
        total_aliases = sum(len(e.aliases) for e in self._cache.values())
        domains = set(e.domain for e in self._cache.values() if e.domain)
        tags = set()
        for e in self._cache.values():
            tags.update(e.tags)
        
        return {
            "total_entries": total_entries,
            "total_aliases": total_aliases,
            "unique_domains": len(domains),
            "unique_tags": len(tags),
            "domains": list(domains),
            "top_tags": list(tags)[:20]
        }
    
    async def close(self):
        """연결 종료"""
        if self._engine:
            await self._engine.dispose()
            logger.info("domain_dictionary_closed")
