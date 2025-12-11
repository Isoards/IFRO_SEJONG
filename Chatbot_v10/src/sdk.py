"""
Ontology Platform SDK
서버 없이 직접 라이브러리로 사용할 수 있는 클라이언트

사용 예시:
    from src.sdk import OntologyPlatform
    
    # 플랫폼 초기화
    platform = OntologyPlatform()
    
    # 텍스트 학습
    await platform.learn_text("금리가 인상되면 주식 시장은 하락한다.")
    
    # RAG 질의
    response = await platform.query("금리와 주식의 관계는?")
    print(response)
"""
import asyncio
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from config.settings import get_settings
from config.constants import ActionType, IntentType
from src.domain.entities import Entity
from src.domain.fragments import Fragment, StructuredDoc
from src.domain.relations import Relation
from src.domain.actions import Action, ActionResult
from src.services.llm_service import LLMService
from src.services.parser_service import ParserService
from src.services.extraction_service import ExtractionService
from src.services.entity_service import EntityService
from src.services.ontology_service import OntologyService
from src.services.query_service import QueryService
from src.services.action_service import ActionService
from src.validators.entity_validator import EntityValidator
from src.validators.relation_validator import RelationValidator
from src.validators.action_validator import ActionValidator
from src.shared.logging import get_logger
from src.shared.types import Result

logger = get_logger(__name__)


class OntologyPlatform:
    """
    Ontology-driven Reasoning & Action Platform SDK
    
    서버 없이 직접 사용할 수 있는 통합 인터페이스
    
    Features:
        - 문서/텍스트 학습
        - 엔티티/관계 관리
        - RAG 기반 질의 응답
        - Action 생성 및 실행
    
    Example:
        ```python
        from src.sdk import OntologyPlatform
        
        async def main():
            platform = OntologyPlatform()
            
            # 텍스트 학습
            result = await platform.learn_text('''
                금리가 인상되면 주식 시장은 하락하는 경향이 있다.
                이는 기업의 차입 비용 증가 때문이다.
            ''')
            
            # RAG 질의
            response = await platform.query("금리 인상이 주식에 미치는 영향은?")
            print(response)
        
        asyncio.run(main())
        ```
    """
    
    def __init__(self, ollama_model: Optional[str] = None):
        """
        플랫폼 초기화
        
        Args:
            ollama_model: 사용할 Ollama 모델 (기본값: 설정 파일에서 로드)
        """
        self.settings = get_settings()
        
        # 모델 오버라이드
        if ollama_model:
            self.settings.ollama_model = ollama_model
        
        # 서비스 초기화
        self._llm = LLMService()
        self._parser = ParserService()
        
        # Validators
        self._entity_validator = EntityValidator()
        self._relation_validator = RelationValidator()
        self._action_validator = ActionValidator()
        
        # Services
        self._extraction = ExtractionService(self._llm)
        self._entity_service = EntityService(self._llm, self._entity_validator)
        self._ontology = OntologyService(self._relation_validator)
        self._query_service = QueryService(self._llm, self._ontology)
        self._action_service = ActionService(self._llm, self._ontology, self._action_validator)
        
        # 학습된 문서 추적
        self._documents: Dict[str, StructuredDoc] = {}
        
        logger.info("platform_initialized", model=self.settings.ollama_model)
    
    # === 학습 (Learning) ===
    
    async def learn_text(
        self,
        text: str,
        source_name: str = "direct_input"
    ) -> Dict[str, Any]:
        """
        텍스트에서 지식 추출 및 온톨로지 구축
        
        Args:
            text: 학습할 텍스트
            source_name: 출처 이름
        
        Returns:
            학습 결과 (fragment_count, entity_count, relation_count)
        
        Example:
            ```python
            result = await platform.learn_text('''
                인플레이션이 상승하면 중앙은행은 금리를 인상한다.
                금리 인상은 기업의 차입 비용을 증가시킨다.
            ''')
            print(f"추출된 Fragment: {result['fragment_count']}")
            ```
        """
        # 1. 텍스트 파싱
        parse_result = await self._parser.parse_text_content(text, source_name)
        if not parse_result.success:
            return {"success": False, "error": parse_result.error}
        
        doc = parse_result.data
        self._documents[doc.id] = doc
        
        # 2. Fragment/Entity 추출
        extraction_result = await self._extraction.extract_from_document(doc)
        if not extraction_result.success:
            return {"success": False, "error": extraction_result.error}
        
        fragments, entity_candidates = extraction_result.data
        
        # 3. Entity Resolution
        entity_result = await self._entity_service.resolve_candidates(entity_candidates)
        entities = entity_result.data if entity_result.success else []
        
        # 4. 온톨로지에 엔티티 추가
        entity_map = {}
        for entity in entities:
            await self._ontology.add_entity(entity)
            entity_map[entity.canonical_name.lower()] = entity
            for alias in entity.aliases:
                entity_map[alias.lower()] = entity
        
        # 5. Fragment에서 Relation 구축
        relation_result = await self._ontology.build_relations_from_fragments(
            fragments, entity_map
        )
        relations = relation_result.data if relation_result.success else []
        
        return {
            "success": True,
            "document_id": doc.id,
            "fragment_count": len(fragments),
            "entity_count": len(entities),
            "relation_count": len(relations),
        }
    
    async def learn_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일에서 지식 추출 및 온톨로지 구축
        
        Args:
            file_path: 파일 경로 (PDF, DOCX, HTML, MD, TXT 지원)
        
        Returns:
            학습 결과
        
        Example:
            ```python
            result = await platform.learn_file("./documents/report.pdf")
            ```
        """
        # 1. 파일 파싱
        parse_result = await self._parser.parse_file(file_path)
        if not parse_result.success:
            return {"success": False, "error": parse_result.error}
        
        doc = parse_result.data
        self._documents[doc.id] = doc
        
        # 2. Fragment/Entity 추출
        extraction_result = await self._extraction.extract_from_document(doc)
        if not extraction_result.success:
            return {"success": False, "error": extraction_result.error}
        
        fragments, entity_candidates = extraction_result.data
        
        # 3. Entity Resolution
        entity_result = await self._entity_service.resolve_candidates(entity_candidates)
        entities = entity_result.data if entity_result.success else []
        
        # 4. 온톨로지에 엔티티 추가
        entity_map = {}
        for entity in entities:
            await self._ontology.add_entity(entity)
            entity_map[entity.canonical_name.lower()] = entity
            for alias in entity.aliases:
                entity_map[alias.lower()] = entity
        
        # 5. Relation 구축
        relation_result = await self._ontology.build_relations_from_fragments(
            fragments, entity_map
        )
        relations = relation_result.data if relation_result.success else []
        
        return {
            "success": True,
            "document_id": doc.id,
            "title": doc.title,
            "fragment_count": len(fragments),
            "entity_count": len(entities),
            "relation_count": len(relations),
        }
    
    # === 질의 (Query) ===
    
    async def query(
        self,
        question: str,
        include_trace: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        RAG 기반 질의 응답
        
        Args:
            question: 질문
            include_trace: 추론 근거 포함 여부
        
        Returns:
            답변 문자열 또는 상세 결과 (include_trace=True인 경우)
        
        Example:
            ```python
            answer = await platform.query("금리와 주식의 관계는?")
            print(answer)
            
            # 상세 정보 포함
            result = await platform.query("금리와 주식의 관계는?", include_trace=True)
            print(result["response"])
            print(result["entities"])
            ```
        """
        # 질의 처리
        process_result = await self._query_service.process_query(question)
        
        if not process_result.success:
            if include_trace:
                return {"success": False, "error": process_result.error}
            return f"오류: {process_result.error}"
        
        data = process_result.data
        
        # RAG 응답 생성
        rag_result = await self._query_service.generate_rag_response(
            question,
            data.get("ontology_context", "")
        )
        
        response = rag_result.data if rag_result.success else "응답 생성 실패"
        
        if include_trace:
            return {
                "success": True,
                "response": response,
                "intent": data.get("intent"),
                "entities": data.get("entities", []),
                "keywords": data.get("keywords", []),
                "mechanisms": data.get("mechanisms", []),
                "ontology_context": data.get("ontology_context"),
            }
        
        return response
    
    async def query_stream(self, question: str):
        """
        스트리밍 RAG 응답
        
        Args:
            question: 질문
        
        Yields:
            응답 청크
        
        Example:
            ```python
            async for chunk in platform.query_stream("금리란 무엇인가요?"):
                print(chunk, end="", flush=True)
            ```
        """
        # 컨텍스트 생성
        process_result = await self._query_service.process_query(question)
        
        if not process_result.success:
            yield f"오류: {process_result.error}"
            return
        
        ontology_context = process_result.data.get("ontology_context", "")
        
        # 프롬프트 생성
        from config.constants import PROMPT_TEMPLATES
        prompt = PROMPT_TEMPLATES["rag_response"].format(
            query=question,
            ontology_context=ontology_context
        )
        
        # 스트리밍 생성
        async for chunk in self._llm.generate_stream(prompt, temperature=0.3):
            yield chunk
    
    # === 온톨로지 (Ontology) ===
    
    def get_entities(self) -> List[Entity]:
        """모든 엔티티 조회"""
        return self._ontology.graph.entities
    
    def get_entity(self, name: str) -> Optional[Entity]:
        """이름으로 엔티티 조회"""
        return self._ontology.graph.get_entity_by_name(name)
    
    def get_relations(self, entity_name: Optional[str] = None) -> List[Relation]:
        """관계 조회"""
        relations = self._ontology.graph.relations
        
        if entity_name:
            entity = self._ontology.graph.get_entity_by_name(entity_name)
            if entity:
                relations = [
                    r for r in relations
                    if r.source_entity_id == entity.id or r.target_entity_id == entity.id
                ]
        
        return relations
    
    def get_mechanisms(self, entity_name: str) -> List[Dict[str, Any]]:
        """엔티티 관련 메커니즘 조회"""
        return self._ontology.get_related_mechanisms(entity_name)
    
    def get_causal_chain(
        self,
        entity_name: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """인과 관계 체인 조회"""
        return self._ontology.get_causal_chain(entity_name, max_depth)
    
    async def add_entity(
        self,
        name: str,
        entity_type: Optional[str] = None,
        description: Optional[str] = None,
        domain_tags: Optional[List[str]] = None
    ) -> Entity:
        """엔티티 수동 추가"""
        from config.constants import ValidationStatus
        
        entity = Entity(
            canonical_name=name,
            entity_type=entity_type,
            description=description,
            domain_tags=domain_tags or [],
            validation_status=ValidationStatus.APPROVED,
        )
        
        await self._ontology.add_entity(entity)
        return entity
    
    async def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        label: str
    ) -> Optional[Relation]:
        """관계 수동 추가"""
        from config.constants import RelationType
        
        source = self._ontology.graph.get_entity_by_name(source_name)
        target = self._ontology.graph.get_entity_by_name(target_name)
        
        if not source or not target:
            return None
        
        relation = Relation(
            source_entity_id=source.id,
            target_entity_id=target.id,
            relation_type=RelationType(relation_type),
            label=label,
        )
        
        result = await self._ontology.add_relation(relation)
        return result.data if result.success else None
    
    # === Action ===
    
    async def create_action(
        self,
        name: str,
        description: str,
        action_type: str = "retrieve",
        handler: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Action:
        """Action 생성"""
        result = await self._action_service.create_action(
            name=name,
            description=description,
            action_type=ActionType(action_type),
            handler=handler,
            parameters=parameters,
        )
        return result.data if result.success else None
    
    async def execute_action(
        self,
        action_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Action 실행"""
        result = await self._action_service.execute_action(action_id, parameters)
        return result.data if result.success else None
    
    def get_actions(self) -> List[Action]:
        """모든 Action 조회"""
        return self._action_service.get_all_actions()
    
    # === 유틸리티 ===
    
    async def health_check(self) -> Dict[str, Any]:
        """시스템 상태 확인"""
        ollama_ok = await self._llm.health_check()
        
        return {
            "ollama_connected": ollama_ok,
            "ollama_model": self.settings.ollama_model,
            "entity_count": self._ontology.graph.node_count,
            "relation_count": self._ontology.graph.edge_count,
            "action_count": len(self._action_service.get_all_actions()),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """온톨로지 통계"""
        return self._ontology.get_statistics()
    
    def export_ontology(self) -> Dict[str, Any]:
        """온톨로지 내보내기"""
        return self._ontology.graph.to_dict()


# === 동기 래퍼 (Synchronous Wrapper) ===

class OntologyPlatformSync:
    """
    동기식 래퍼 - asyncio 없이 사용 가능
    
    Example:
        ```python
        from src.sdk import OntologyPlatformSync
        
        platform = OntologyPlatformSync()
        
        # 학습
        platform.learn_text("금리가 오르면 주식이 떨어진다.")
        
        # 질의
        answer = platform.query("금리와 주식의 관계는?")
        print(answer)
        ```
    """
    
    def __init__(self, ollama_model: Optional[str] = None):
        self._platform = OntologyPlatform(ollama_model)
        self._loop = asyncio.new_event_loop()
    
    def _run(self, coro):
        """코루틴 실행"""
        return self._loop.run_until_complete(coro)
    
    def learn_text(self, text: str, source_name: str = "direct_input") -> Dict[str, Any]:
        """텍스트 학습"""
        return self._run(self._platform.learn_text(text, source_name))
    
    def learn_file(self, file_path: str) -> Dict[str, Any]:
        """파일 학습"""
        return self._run(self._platform.learn_file(file_path))
    
    def query(self, question: str, include_trace: bool = False) -> Union[str, Dict[str, Any]]:
        """RAG 질의"""
        return self._run(self._platform.query(question, include_trace))
    
    def get_entities(self) -> List[Entity]:
        return self._platform.get_entities()
    
    def get_entity(self, name: str) -> Optional[Entity]:
        return self._platform.get_entity(name)
    
    def get_relations(self, entity_name: Optional[str] = None) -> List[Relation]:
        return self._platform.get_relations(entity_name)
    
    def get_mechanisms(self, entity_name: str) -> List[Dict[str, Any]]:
        return self._platform.get_mechanisms(entity_name)
    
    def get_causal_chain(self, entity_name: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        return self._platform.get_causal_chain(entity_name, max_depth)
    
    def add_entity(
        self,
        name: str,
        entity_type: Optional[str] = None,
        description: Optional[str] = None,
        domain_tags: Optional[List[str]] = None
    ) -> Entity:
        return self._run(self._platform.add_entity(name, entity_type, description, domain_tags))
    
    def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        label: str
    ) -> Optional[Relation]:
        return self._run(self._platform.add_relation(source_name, target_name, relation_type, label))
    
    def health_check(self) -> Dict[str, Any]:
        return self._run(self._platform.health_check())
    
    def get_stats(self) -> Dict[str, Any]:
        return self._platform.get_stats()
    
    def export_ontology(self) -> Dict[str, Any]:
        return self._platform.export_ontology()
    
    def close(self):
        """이벤트 루프 종료"""
        self._loop.close()
