"""
Query 처리 서비스
계획서 4: Question Processing & Routing
"""
from typing import List, Optional, Dict, Any

from config.constants import IntentType, ActionType
from src.domain.actions import Action, ActionTrace
from src.services.llm_service import LLMService
from src.services.ontology_service import OntologyService
from src.shared.logging import get_logger
from src.shared.types import Result

logger = get_logger(__name__)


class QueryService:
    """
    질의 처리 및 라우팅 서비스
    
    계획서 4.1: Intent 분류
    계획서 4.2: Ontology 기반 라우팅
    
    원칙 4: 단일 책임 - 질의 처리/라우팅만 담당
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        ontology_service: OntologyService
    ):
        self.llm = llm_service
        self.ontology = ontology_service
    
    async def process_query(
        self,
        query: str
    ) -> Result[Dict[str, Any]]:
        """
        사용자 질의 처리
        
        1. Intent 분류
        2. 관련 엔티티 추출
        3. 온톨로지 서브그래프 추출
        4. Action 후보 또는 RAG 컨텍스트 반환
        
        Args:
            query: 사용자 질의
        
        Returns:
            Result[Dict]: 처리 결과
        """
        try:
            # 1. Intent 분류 (LLM Generator)
            intent_result = await self.llm.classify_intent(query)
            
            intent_type = self._parse_intent_type(intent_result.get("intent", "RETRIEVAL"))
            confidence = intent_result.get("confidence", 0.5)
            entities = intent_result.get("entities", [])
            keywords = intent_result.get("keywords", [])
            
            logger.info(
                "query_intent_classified",
                query=query[:100],
                intent=intent_type.value,
                confidence=confidence
            )
            
            # 2. 온톨로지에서 관련 엔티티 서브그래프 추출
            search_terms = entities + keywords
            subgraph = self.ontology.get_subgraph(search_terms, depth=2)
            
            # 3. 관련 메커니즘/관계 조회
            mechanisms = []
            for entity_name in entities:
                mechanisms.extend(self.ontology.get_related_mechanisms(entity_name))
            
            # 4. Intent에 따른 처리
            result = {
                "query": query,
                "intent": intent_type.value,
                "confidence": confidence,
                "entities": entities,
                "keywords": keywords,
                "subgraph": subgraph.to_dict() if subgraph.node_count > 0 else None,
                "mechanisms": mechanisms,
            }
            
            # Intent별 추가 처리
            if intent_type == IntentType.RETRIEVAL:
                # 정보 조회 - RAG 컨텍스트 준비
                result["action_type"] = ActionType.RETRIEVE.value
                result["ontology_context"] = self.ontology.to_context_string(search_terms)
                
            elif intent_type == IntentType.ANALYSIS:
                # 분석/추론 - 인과 체인 추출
                result["action_type"] = ActionType.REASON.value
                causal_chains = []
                for entity_name in entities:
                    chains = self.ontology.get_causal_chain(entity_name)
                    causal_chains.extend(chains)
                result["causal_chains"] = causal_chains
                result["ontology_context"] = self.ontology.to_context_string(search_terms)
                
            elif intent_type == IntentType.EXECUTION:
                # 실행 요청 - Action 후보 생성
                result["action_type"] = ActionType.EXECUTE.value
                action = await self._generate_action_candidate(
                    query, intent_type, entities, mechanisms
                )
                result["action_candidate"] = action
                
            elif intent_type == IntentType.CREATION:
                # Action 생성 요청
                result["action_type"] = ActionType.EXECUTE.value
                result["requires_admin_approval"] = True
                action = await self._generate_action_candidate(
                    query, intent_type, entities, mechanisms
                )
                result["action_candidate"] = action
            
            return Result.ok(result)
            
        except Exception as e:
            logger.error("query_processing_failed", error=str(e), query=query[:100])
            return Result.fail(
                error=str(e),
                error_code="QUERY_PROCESSING_FAILED"
            )
    
    def _parse_intent_type(self, intent_str: str) -> IntentType:
        """Intent 문자열을 Enum으로 변환"""
        intent_map = {
            "RETRIEVAL": IntentType.RETRIEVAL,
            "ANALYSIS": IntentType.ANALYSIS,
            "EXECUTION": IntentType.EXECUTION,
            "CREATION": IntentType.CREATION,
        }
        return intent_map.get(intent_str.upper(), IntentType.RETRIEVAL)
    
    async def _generate_action_candidate(
        self,
        query: str,
        intent_type: IntentType,
        entities: List[str],
        mechanisms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Action 후보 생성 (LLM Generator)
        """
        action_result = await self.llm.generate_action(
            query=query,
            intent=intent_type.value,
            entities=entities,
            relations=mechanisms
        )
        
        return action_result
    
    async def generate_rag_response(
        self,
        query: str,
        ontology_context: Optional[str] = None
    ) -> Result[str]:
        """
        RAG 기반 응답 생성
        계획서 목표: RAG를 통한 온톨로지 기반 LLM 답변 생성
        """
        try:
            # 컨텍스트가 없으면 쿼리 처리해서 생성
            if not ontology_context:
                process_result = await self.process_query(query)
                if process_result.success:
                    ontology_context = process_result.data.get("ontology_context", "")
                else:
                    ontology_context = ""
            
            # LLM으로 응답 생성
            response = await self.llm.generate_rag_response(query, ontology_context)
            
            return Result.ok(response)
            
        except Exception as e:
            logger.error("rag_response_failed", error=str(e))
            return Result.fail(error=str(e), error_code="RAG_FAILED")
