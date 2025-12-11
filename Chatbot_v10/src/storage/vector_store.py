"""
Vector Store - ChromaDB 기반 벡터 저장소
임베딩 기반 의미적 검색

원칙 1: One Source of Truth - 벡터 데이터의 단일 저장소
원칙 4: 단일 책임 - 벡터 검색만 담당
"""
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import chromadb

from config.settings import get_settings
from src.storage.base import BaseStore, StoreError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class VectorStore(BaseStore[Dict[str, Any]]):
    """
    ChromaDB 기반 벡터 저장소
    
    기능:
    - 엔티티/Fragment 임베딩 저장
    - 의미적 유사도 검색
    - 다중 컬렉션 관리
    """
    
    # 컬렉션 이름 상수
    COLLECTION_ENTITIES = "entities"
    COLLECTION_FRAGMENTS = "fragments"
    COLLECTION_DOCUMENTS = "documents"
    
    def __init__(self, persist_dir: Optional[str] = None):
        super().__init__("vector")
        self.persist_dir = persist_dir or get_settings().chroma_persist_dir
        self.client = None
        self._collections: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """ChromaDB 초기화"""
        try:
            persist_path = Path(self.persist_dir)
            persist_path.mkdir(parents=True, exist_ok=True)
            
            # 새 ChromaDB API: PersistentClient 사용
            self.client = chromadb.PersistentClient(path=str(persist_path))
            
            # 컬렉션 초기화
            for collection_name in [
                self.COLLECTION_ENTITIES,
                self.COLLECTION_FRAGMENTS,
                self.COLLECTION_DOCUMENTS
            ]:
                self._collections[collection_name] = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            self._initialized = True
            logger.info("vector_store_initialized", persist_dir=self.persist_dir)
            
        except Exception as e:
            raise self._handle_error(e, "initialize")
    
    async def add_embedding(
        self,
        collection_name: str,
        item_id: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        document: Optional[str] = None
    ) -> str:
        """임베딩 추가"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            
            # 메타데이터에서 복잡한 타입 제거 (ChromaDB 제약)
            clean_metadata = {}
            if metadata:
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_metadata[k] = v
                    elif isinstance(v, list) and all(isinstance(i, str) for i in v):
                        clean_metadata[k] = ",".join(v)
            
            collection.add(
                ids=[item_id],
                embeddings=[embedding],
                metadatas=[clean_metadata] if clean_metadata else None,
                documents=[document] if document else None
            )
            
            logger.debug(
                "embedding_added",
                collection=collection_name,
                item_id=item_id
            )
            return item_id
            
        except Exception as e:
            raise self._handle_error(e, "add_embedding")
    
    async def update_embedding(
        self,
        collection_name: str,
        item_id: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        document: Optional[str] = None
    ) -> bool:
        """임베딩 업데이트"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            
            # 기존 항목 삭제 후 추가
            try:
                collection.delete(ids=[item_id])
            except Exception:
                pass  # 없어도 무시
            
            await self.add_embedding(
                collection_name, item_id, embedding, metadata, document
            )
            return True
            
        except Exception as e:
            raise self._handle_error(e, "update_embedding")
    
    async def search_similar(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        유사도 검색
        
        Returns:
            List[(item_id, similarity_score, metadata)]
        """
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata if filter_metadata else None,
                include=["metadatas", "distances", "documents"]
            )
            
            # 결과 파싱
            items = []
            if results["ids"] and results["ids"][0]:
                for i, item_id in enumerate(results["ids"][0]):
                    # ChromaDB는 distance를 반환, similarity로 변환
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - distance  # cosine distance to similarity
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    
                    items.append((item_id, similarity, metadata))
            
            logger.debug(
                "similarity_search",
                collection=collection_name,
                top_k=top_k,
                results_count=len(items)
            )
            return items
            
        except Exception as e:
            raise self._handle_error(e, "search_similar")
    
    async def search_by_text(
        self,
        collection_name: str,
        query_text: str,
        embedding_fn,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        텍스트로 유사도 검색 (임베딩 함수 필요)
        
        Args:
            collection_name: 컬렉션 이름
            query_text: 검색 텍스트
            embedding_fn: 임베딩 생성 함수 (async)
            top_k: 반환할 결과 수
        """
        embedding = await embedding_fn(query_text)
        return await self.search_similar(collection_name, embedding, top_k)
    
    async def get_embedding(
        self,
        collection_name: str,
        item_id: str
    ) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """임베딩 조회"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            
            results = collection.get(
                ids=[item_id],
                include=["embeddings", "metadatas"]
            )
            
            if results["ids"]:
                embedding = results["embeddings"][0] if results["embeddings"] else []
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                return (embedding, metadata)
            
            return None
            
        except Exception as e:
            raise self._handle_error(e, "get_embedding")
    
    async def delete_embedding(
        self,
        collection_name: str,
        item_id: str
    ) -> bool:
        """임베딩 삭제"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            collection.delete(ids=[item_id])
            return True
        except Exception as e:
            raise self._handle_error(e, "delete_embedding")
    
    async def get_collection_count(self, collection_name: str) -> int:
        """컬렉션 항목 수"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(collection_name)
            return collection.count()
        except Exception as e:
            raise self._handle_error(e, "get_collection_count")
    
    def _get_collection(self, name: str):
        """컬렉션 가져오기"""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name)
        return self._collections[name]
    
    # BaseStore 추상 메서드 구현
    
    async def save(self, item: Dict[str, Any]) -> str:
        """항목 저장 (add_embedding 래퍼)"""
        return await self.add_embedding(
            collection_name=item.get("collection", self.COLLECTION_ENTITIES),
            item_id=item["id"],
            embedding=item["embedding"],
            metadata=item.get("metadata"),
            document=item.get("document")
        )
    
    async def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """항목 조회"""
        for collection_name in self._collections:
            result = await self.get_embedding(collection_name, item_id)
            if result:
                return {
                    "id": item_id,
                    "embedding": result[0],
                    "metadata": result[1],
                    "collection": collection_name
                }
        return None
    
    async def delete(self, item_id: str) -> bool:
        """항목 삭제"""
        for collection_name in self._collections:
            try:
                await self.delete_embedding(collection_name, item_id)
                return True
            except Exception:
                pass
        return False
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """모든 항목 조회 (entity 컬렉션)"""
        self._ensure_initialized()
        
        try:
            collection = self._get_collection(self.COLLECTION_ENTITIES)
            results = collection.peek(limit=limit)  # ChromaDB peek 사용
            
            items = []
            if results["ids"]:
                for i, item_id in enumerate(results["ids"]):
                    items.append({
                        "id": item_id,
                        "embedding": results["embeddings"][i] if results.get("embeddings") else [],
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                    })
            return items
        except Exception as e:
            raise self._handle_error(e, "list_all")
    
    async def close(self) -> None:
        """연결 종료 및 영속화"""
        # 새 API에서는 PersistentClient가 자동으로 영속화
        if self.client:
            pass  # PersistentClient는 자동 저장
        self._initialized = False
        logger.info("vector_store_closed")
