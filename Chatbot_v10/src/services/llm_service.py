"""
LLM 서비스 - Ollama 연동
원칙 4: 단일 책임 원칙 - LLM 호출만 담당
"""
import json
from typing import Optional, Dict, Any, List, AsyncGenerator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import get_settings
from config.constants import PROMPT_TEMPLATES
from src.shared.errors import LLMError
from src.shared.logging import get_logger, log_error

logger = get_logger(__name__)


class LLMService:
    """
    Ollama LLM 서비스
    역할: Generator - 생성만 담당, 검증은 하지 않음
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_host
        self.model = self.settings.ollama_model
        self.embedding_model = self.settings.ollama_embedding_model
        self.timeout = self.settings.ollama_timeout
    
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """Ollama API 요청"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if stream:
                    # 스트리밍 응답
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        full_response = ""
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                if "response" in data:
                                    full_response += data["response"]
                        return {"response": full_response}
                else:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.TimeoutException as e:
                log_error(logger, e, {"endpoint": endpoint, "model": self.model})
                raise LLMError(
                    message="Ollama 요청 타임아웃",
                    model=self.model,
                    prompt_type=endpoint
                )
            except httpx.HTTPStatusError as e:
                log_error(logger, e, {"endpoint": endpoint, "status": e.response.status_code})
                raise LLMError(
                    message=f"Ollama HTTP 에러: {e.response.status_code}",
                    model=self.model,
                    prompt_type=endpoint
                )
            except Exception as e:
                log_error(logger, e, {"endpoint": endpoint})
                raise LLMError(
                    message=f"Ollama 요청 실패: {str(e)}",
                    model=self.model,
                    prompt_type=endpoint
                )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False
    ) -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            json_mode: JSON 응답 모드
        
        Returns:
            생성된 텍스트
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if json_mode:
            payload["format"] = "json"
        
        logger.debug("llm_generate_request", model=self.model, prompt_length=len(prompt))
        
        result = await self._make_request("/api/generate", payload)
        response = result.get("response", "")
        
        logger.debug("llm_generate_response", response_length=len(response))
        
        return response
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """스트리밍 생성"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.base_url}/api/generate"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            임베딩 벡터
        """
        payload = {
            "model": self.embedding_model,
            "input": text,
        }
        
        result = await self._make_request("/api/embed", payload)
        
        # Ollama의 응답 형식에 맞게 처리
        embeddings = result.get("embeddings", result.get("embedding", []))
        if isinstance(embeddings, list) and len(embeddings) > 0:
            if isinstance(embeddings[0], list):
                return embeddings[0]
            return embeddings
        
        raise LLMError(
            message="임베딩 생성 실패: 빈 응답",
            model=self.embedding_model
        )
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 생성"""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
    
    # === 템플릿 기반 메서드들 (Generator 역할) ===
    
    async def extract_fragments(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 Fragment 추출 (Generator)
        Validator가 검증하기 전 후보 생성
        """
        prompt = PROMPT_TEMPLATES["fragment_extraction"].format(text=text)
        
        response = await self.generate(prompt, json_mode=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 빈 결과 반환
            logger.warning("fragment_extraction_json_parse_failed", response=response[:200])
            return {"fragments": []}
    
    async def resolve_entities(
        self,
        entity1: str,
        context1: str,
        entity2: str,
        context2: str
    ) -> Dict[str, Any]:
        """
        두 엔티티가 동일한지 판단 (Generator)
        """
        prompt = PROMPT_TEMPLATES["entity_resolution"].format(
            entity1=entity1,
            context1=context1,
            entity2=entity2,
            context2=context2
        )
        
        response = await self.generate(prompt, json_mode=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_same": False, "confidence": 0.0, "reasoning": "파싱 실패"}
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        사용자 질의 의도 분류 (Generator)
        """
        prompt = PROMPT_TEMPLATES["intent_classification"].format(query=query)
        
        response = await self.generate(prompt, json_mode=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "intent": "RETRIEVAL",
                "confidence": 0.5,
                "entities": [],
                "keywords": []
            }
    
    async def generate_action(
        self,
        query: str,
        intent: str,
        entities: List[str],
        relations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Action 생성 (Generator)
        """
        prompt = PROMPT_TEMPLATES["action_generation"].format(
            query=query,
            intent=intent,
            entities=json.dumps(entities, ensure_ascii=False),
            relations=json.dumps(relations, ensure_ascii=False)
        )
        
        response = await self.generate(prompt, json_mode=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "action_type": "RETRIEVE",
                "name": "default_retrieval",
                "description": "기본 정보 조회",
                "parameters": {},
                "confidence": 0.5
            }
    
    async def generate_rag_response(
        self,
        query: str,
        ontology_context: str
    ) -> str:
        """
        온톨로지 기반 RAG 응답 생성
        계획서 목표: RAG를 통한 온톨로지 기반 LLM 답변 생성
        """
        prompt = PROMPT_TEMPLATES["rag_response"].format(
            query=query,
            ontology_context=ontology_context
        )
        
        return await self.generate(prompt, temperature=0.3)
    
    async def health_check(self) -> bool:
        """Ollama 서버 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
