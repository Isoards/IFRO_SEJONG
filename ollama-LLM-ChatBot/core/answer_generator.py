"""
로컬 LLM을 사용한 답변 생성 모듈 (최적화 버전)

빠른 응답을 위한 간소화된 답변 생성기
"""

import os
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 로컬 LLM 라이브러리
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama 라이브러리를 찾을 수 없습니다.")

from .pdf_processor import TextChunk
from .question_analyzer import AnalyzedQuestion
from .fast_cache import get_question_cache

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """지원하는 모델 타입"""
    OLLAMA = "ollama"

@dataclass
class GenerationConfig:
    """텍스트 생성 설정 (속도 최적화)"""
    max_length: int = 128  # 짧은 답변으로 속도 향상
    temperature: float = 0.3  # 빠른 생성을 위해 낮은 값
    top_p: float = 0.8  # 빠른 추론을 위해 범위 축소
    top_k: int = 20  # 빠른 추론을 위해 범위 축소
    repetition_penalty: float = 1.1  # 반복 방지 최소화
    do_sample: bool = True
    num_return_sequences: int = 1

@dataclass
class Answer:
    """생성된 답변 데이터 클래스"""
    content: str
    confidence_score: float
    used_chunks: List[str]
    generation_time: float
    model_name: str
    metadata: Optional[Dict] = None

class OllamaInterface:
    """Ollama 인터페이스 (최적화)"""
    
    def __init__(self, model_name: str = "qwen2:1.5b", config: GenerationConfig = None):
        self.model_name = model_name
        self.config = config or GenerationConfig()
        self.client = ollama.Client(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
        
    def generate(self, prompt: str) -> str:
        """텍스트 생성 (최적화)"""
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': self.config.temperature,
                    'top_p': self.config.top_p,
                    'top_k': self.config.top_k,
                    'num_predict': self.config.max_length,
                    'repeat_penalty': self.config.repetition_penalty,
                    'num_thread': 4,  # 멀티스레딩
                    'num_gpu': 1      # GPU 가속
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama 생성 실패: {e}")
            return "답변을 생성할 수 없습니다."

class AnswerGenerator:
    """답변 생성기 (최적화)"""
    
    def __init__(self, model_name: str = "qwen2:1.5b", cache_enabled: bool = True):
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        
        # LLM 인터페이스 초기화
        self.llm = OllamaInterface(model_name)
        
        # 캐시 초기화
        self.cache = get_question_cache() if cache_enabled else None
        
        # 프롬프트 템플릿 (단순화)
        self.prompt_templates = {
            "basic": """문서: {context}

질문: {question}

한국어로 간단히 답변:"""
        }
        
        logger.info(f"답변 생성기 초기화 완료: {model_name}")
    
    def generate_answer(self, 
                       analyzed_question: AnalyzedQuestion,
                       relevant_chunks: List[Tuple[TextChunk, float]],
                       conversation_history: List = None,
                       pdf_id: Optional[str] = None) -> Answer:
        """질문에 대한 답변 생성 (최적화)"""
        start_time = time.time()
        question = analyzed_question.original_question
        
        # 1. 캐시 확인 (빠른 응답)
        if self.cache_enabled and self.cache:
            context_key = str([chunk.chunk_id for chunk, _ in relevant_chunks][:3])
            cached_answer = self.cache.get(question, context_key)
            if cached_answer:
                logger.info(f"캐시 히트: {time.time() - start_time:.3f}초")
                return cached_answer
        
        # 2. 컨텍스트 구성 (단순화)
        context = self._build_context(relevant_chunks)
        
        # 3. 프롬프트 구성
        prompt = self.prompt_templates["basic"].format(
            context=context,
            question=question
        )
        
        # 4. 답변 생성
        try:
            generated_text = self.llm.generate(prompt)
            
            # 5. 기본 후처리
            processed_answer = generated_text.strip()
            if not processed_answer:
                processed_answer = "답변을 생성할 수 없습니다."
            
            generation_time = time.time() - start_time
            
            answer = Answer(
                content=processed_answer,
                confidence_score=0.8,  # 고정 신뢰도
                used_chunks=[chunk.chunk_id for chunk, _ in relevant_chunks],
                generation_time=generation_time,
                model_name=self.llm.model_name,
                metadata={
                    "question_type": analyzed_question.question_type.value,
                    "num_chunks_used": len(relevant_chunks),
                    "from_cache": False
                }
            )
            
            # 6. 캐시에 저장
            if self.cache_enabled and self.cache:
                self.cache.put(question, answer, context_key)
            
            logger.info(f"답변 생성 완료: {generation_time:.2f}초")
            return answer
            
        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return Answer(
                content="죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.",
                confidence_score=0.0,
                used_chunks=[],
                generation_time=time.time() - start_time,
                model_name=self.llm.model_name,
                metadata={"error": str(e)}
            )
    
    def _build_context(self, relevant_chunks: List[Tuple[TextChunk, float]], 
                      max_context_length: int = 1500) -> str:
        """컨텍스트 구성 (최적화)"""
        if not relevant_chunks:
            return "관련 정보를 찾을 수 없습니다."
        
        context_parts = []
        current_length = 0
        
        for chunk, similarity in relevant_chunks:
            chunk_text = chunk.content.strip()
            if current_length + len(chunk_text) > max_context_length:
                break
            
            context_parts.append(f"[유사도: {similarity:.2f}] {chunk_text}")
            current_length += len(chunk_text)
        
        return "\n\n".join(context_parts)
    
    def update_model_config(self, config: GenerationConfig):
        """모델 설정 업데이트"""
        self.llm.config = config
        logger.info("모델 설정 업데이트 완료")
    
    def get_model_info(self) -> Dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "model_type": ModelType.OLLAMA.value,
            "cache_enabled": self.cache_enabled,
            "config": {
                "max_length": self.llm.config.max_length,
                "temperature": self.llm.config.temperature,
                "top_p": self.llm.config.top_p
            }
        }
