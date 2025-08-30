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
    """텍스트 생성 설정 (정확성 최적화)"""
    max_length: int = 256  # 답변 길이 제한
    temperature: float = 0.1  # 더 정확한 답변을 위해 낮은 값
    top_p: float = 0.7  # 더 집중된 답변을 위해 낮은 값
    top_k: int = 20  # 더 집중된 선택을 위해 낮은 값
    repetition_penalty: float = 1.1  # 반복 방지 활성화
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
                    'num_thread': 8,  # 더 많은 스레드 사용
                    'num_gpu': 1,     # GPU 가속
                    'num_ctx': 1024,  # 컨텍스트 크기 제한
                    'num_batch': 512, # 배치 크기 최적화
                    'rope_freq_base': 10000,  # RoPE 최적화
                    'rope_freq_scale': 0.5    # RoPE 스케일링
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
        
        # 프롬프트 템플릿 (정확성 최적화)
        self.prompt_templates = {
            "basic": """다음 문서 내용을 기반으로 질문에 답변해주세요.

문서 내용:
{context}

질문: {question}

지시사항:
1. 위 문서 내용을 꼼꼼히 읽고 질문과 관련된 모든 정보를 찾아보세요.
2. 문서에 관련 내용이 있으면 반드시 그 내용을 바탕으로 답변하세요.
3. 답변은 구체적이고 실용적으로 작성하세요.
4. 최대 {max_length}자 이내에 답변을 완성하세요.
5. 단계별로 설명하거나 예시를 들어 설명하세요.
6. 문서에 관련 정보가 정말 없을 때만 "문서에서 해당 내용을 찾을 수 없습니다."라고 답변하세요.
7. 키워드 매칭이나 유사한 표현도 고려하여 답변하세요.

답변:"""
        }
        
        logger.info(f"답변 생성기 초기화 완료: {model_name}")
    
    def load_model(self) -> bool:
        """모델 로드 (Ollama는 이미 로드되어 있음)"""
        try:
            # Ollama는 이미 실행 중이므로 모델 로드 성공으로 간주
            logger.info(f"Ollama 모델 {self.model_name} 로드 완료")
            return True
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def unload_model(self):
        """모델 언로드 (Ollama는 자동으로 관리됨)"""
        try:
            logger.info(f"Ollama 모델 {self.model_name} 언로드 완료")
        except Exception as e:
            logger.error(f"모델 언로드 실패: {e}")
    
    def generate_answer(self, 
                       analyzed_question: AnalyzedQuestion,
                       relevant_chunks: List[Tuple[TextChunk, float]],
                       conversation_history: List = None,
                       pdf_id: Optional[str] = None) -> Answer:
        """질문에 대한 답변 생성 (최적화)"""
        total_start_time = time.time()
        question = analyzed_question.original_question
        
        # 1. 캐시 확인 (빠른 응답)
        cache_start = time.time()
        if self.cache_enabled and self.cache:
            context_key = str([chunk.chunk_id for chunk, _ in relevant_chunks][:3])
            cached_answer = self.cache.get(question, context_key)
            if cached_answer:
                cache_time = time.time() - cache_start
                print(f"  🚀 캐시 히트: {cache_time:.3f}초")
                return cached_answer
        cache_time = time.time() - cache_start
        
        # 2. 컨텍스트 구성 (단순화)
        context_start = time.time()
        context = self._build_context(relevant_chunks)
        context_time = time.time() - context_start
        print(f"  📝 컨텍스트 구성: {context_time:.3f}초")
        
        # 3. 프롬프트 구성
        prompt_start = time.time()
        prompt = self.prompt_templates["basic"].format(
            context=context,
            question=question,
            max_length=self.llm.config.max_length
        )
        prompt_time = time.time() - prompt_start
        print(f"  📋 프롬프트 구성: {prompt_time:.3f}초")
        
        # 4. 답변 생성 (가장 오래 걸리는 부분)
        llm_start = time.time()
        try:
            generated_text = self.llm.generate(prompt)
            llm_time = time.time() - llm_start
            print(f"  🤖 LLM 추론: {llm_time:.2f}초")
            
            # 5. 기본 후처리
            postprocess_start = time.time()
            processed_answer = generated_text.strip()
            if not processed_answer:
                processed_answer = "답변을 생성할 수 없습니다."
            postprocess_time = time.time() - postprocess_start
            print(f"  ✂️  후처리: {postprocess_time:.3f}초")
            
            total_time = time.time() - total_start_time
            
            answer = Answer(
                content=processed_answer,
                confidence_score=0.8,  # 고정 신뢰도
                used_chunks=[chunk.chunk_id for chunk, _ in relevant_chunks],
                generation_time=total_time,
                model_name=self.llm.model_name,
                metadata={
                    "question_type": analyzed_question.question_type.value,
                    "num_chunks_used": len(relevant_chunks),
                    "from_cache": False,
                    "timing_breakdown": {
                        "cache_check": cache_time,
                        "context_build": context_time,
                        "prompt_build": prompt_time,
                        "llm_generation": llm_time,
                        "postprocess": postprocess_time
                    }
                }
            )
            
            # 6. 캐시에 저장
            cache_save_start = time.time()
            if self.cache_enabled and self.cache:
                self.cache.put(question, answer, context_key)
            cache_save_time = time.time() - cache_save_start
            print(f"  💾 캐시 저장: {cache_save_time:.3f}초")
            
            print(f"  📊 LLM 생성 세부: 캐시({cache_time/total_time*100:.1f}%) | 컨텍스트({context_time/total_time*100:.1f}%) | 프롬프트({prompt_time/total_time*100:.1f}%) | LLM({llm_time/total_time*100:.1f}%) | 후처리({postprocess_time/total_time*100:.1f}%)")
            
            logger.info(f"답변 생성 완료: {total_time:.2f}초")
            return answer
            
        except Exception as e:
            llm_time = time.time() - llm_start
            total_time = time.time() - total_start_time
            logger.error(f"답변 생성 실패: {e}")
            print(f"  ❌ LLM 오류: {llm_time:.2f}초 후 실패")
            return Answer(
                content="죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.",
                confidence_score=0.0,
                used_chunks=[],
                generation_time=total_time,
                model_name=self.llm.model_name,
                metadata={"error": str(e)}
            )
    
    def _build_context(self, relevant_chunks: List[Tuple[TextChunk, float]], 
                       max_context_length: int = 800) -> str:
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
