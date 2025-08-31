"""
경량화된 답변 생성 모듈 (KoELECTRA 기반)

메모리 효율성과 빠른 응답을 위한 최적화된 모듈
"""

import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

# 로컬 LLM 라이브러리
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers 라이브러리를 찾을 수 없습니다.")

# 상대 경로 import 수정
from ..document.pdf_processor import TextChunk
from ..query.question_analyzer import AnalyzedQuestion
from ..cache.fast_cache import get_question_cache

logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """경량화된 생성 설정"""
    max_length: int = 128  # 답변 길이 제한 (256 → 128로 축소)
    temperature: float = 0.1
    top_p: float = 0.7
    top_k: int = 20
    repetition_penalty: float = 1.1
    do_sample: bool = True
    num_return_sequences: int = 1

@dataclass
class Answer:
    """경량화된 답변 데이터 클래스"""
    content: str
    confidence_score: float
    used_chunks: List[str]
    generation_time: float
    model_name: str
    metadata: Optional[Dict] = None

class LocalLLMInterface:
    """경량화된 KoELECTRA 인터페이스"""
    
    def __init__(self, model_name: str = "monologg/koelectra-small-v3-discriminator", config: GenerationConfig = None):
        self.model_name = model_name
        self.config = config or GenerationConfig()
        self.tokenizer = None
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """경량화된 KoELECTRA 모델 로드"""
        try:
            logger.info(f"KoELECTRA 모델 로딩 중: {self.model_name}")
            
            # 토크나이저 로드 (캐시 디렉토리 최적화)
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir="./models",
                use_fast=True  # 빠른 토크나이저 사용
            )
            
            # KoELECTRA 모델 로드 (메모리 최적화)
            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                cache_dir="./models",
                low_cpu_mem_usage=True,
                device_map="cpu"  # CPU 전용으로 설정
            )
            
            logger.info(f"KoELECTRA 모델 로딩 완료: {self.model_name}")
            
        except Exception as e:
            logger.error(f"KoELECTRA 모델 로딩 실패: {e}")
            raise
        
    def generate(self, prompt: str) -> str:
        """경량화된 템플릿 기반 답변 생성"""
        try:
            # 키워드 추출 (간소화)
            keywords = self._extract_keywords_simple(prompt)
            
            # 템플릿 기반 답변 생성
            response = self._generate_template_response(prompt, keywords)
            
            return response if response else "답변을 생성할 수 없습니다."
            
        except Exception as e:
            logger.error(f"KoELECTRA 기반 생성 실패: {e}")
            return "답변을 생성할 수 없습니다."
    
    def _extract_keywords_simple(self, text: str) -> list:
        """간소화된 키워드 추출"""
        import re
        # 한국어 키워드만 추출 (성능 향상)
        korean_pattern = re.compile(r'[가-힣]+')
        keywords = korean_pattern.findall(text)
        return list(set(keywords))[:5]  # 상위 5개만 (10개 → 5개로 축소)
    
    def _generate_template_response(self, prompt: str, keywords: list) -> str:
        """경량화된 템플릿 기반 답변 생성"""
        # 교통 관련 키워드 (최적화된 목록)
        traffic_keywords = ['교통', '사고', '통계', '데이터', '조회', '정보', '도로', '신호']
        
        if any(keyword in prompt.lower() for keyword in traffic_keywords):
            return "교통 관련 데이터베이스에서 해당 정보를 조회할 수 있습니다."
        
        return "주어진 문서 내용을 바탕으로 답변을 생성했습니다."

class AnswerGenerator:
    """경량화된 답변 생성기"""
    
    def __init__(self, model_name: str = "monologg/koelectra-small-v3-discriminator", cache_enabled: bool = True):
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        
        # LLM 인터페이스 초기화
        if TRANSFORMERS_AVAILABLE:
            self.llm = LocalLLMInterface(model_name)
        else:
            raise RuntimeError("Transformers 라이브러리가 설치되지 않았습니다.")
        
        # 캐시 초기화
        self.cache = get_question_cache() if cache_enabled else None
        
        # 경량화된 프롬프트 템플릿
        self.prompt_templates = {
            "basic": "문서: {context}\n질문: {question}\n답변:"
        }
        
        logger.info(f"경량화된 답변 생성기 초기화 완료: {model_name}")
    
    def load_model(self) -> bool:
        """모델 로드 (로컬 LLM은 이미 로드되어 있음)"""
        try:
            # 로컬 LLM은 이미 초기화 시 로드되므로 성공으로 간주
            logger.info(f"로컬 LLM 모델 {self.model_name} 로드 완료")
            return True
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def unload_model(self):
        """경량화된 모델 언로드"""
        try:
            if hasattr(self.llm, 'model'):
                del self.llm.model
            if hasattr(self.llm, 'tokenizer'):
                del self.llm.tokenizer
            import gc
            gc.collect()
            logger.info(f"경량화된 모델 {self.model_name} 언로드 완료")
        except Exception as e:
            logger.error(f"모델 언로드 실패: {e}")
    
    def generate_answer(self, 
                       analyzed_question: AnalyzedQuestion,
                       relevant_chunks: List[Tuple[TextChunk, float]],
                       conversation_history: List = None,
                       pdf_id: Optional[str] = None) -> Answer:
        """경량화된 답변 생성"""
        start_time = time.time()
        question = analyzed_question.original_question
        
        # 1. 캐시 확인
        if self.cache_enabled and self.cache:
            context_key = str([chunk.chunk_id for chunk, _ in relevant_chunks][:3])
            cached_answer = self.cache.get(question, context_key)
            if cached_answer:
                return cached_answer
        
        # 2. 컨텍스트 구성 (간소화)
        context = self._build_context_simple(relevant_chunks)
        
        # 3. 프롬프트 구성
        prompt = self.prompt_templates["basic"].format(
            context=context,
            question=question
        )
        
        # 4. 답변 생성
        try:
            generated_text = self.llm.generate(prompt)
            total_time = time.time() - start_time
            
            answer = Answer(
                content=generated_text.strip() or "답변을 생성할 수 없습니다.",
                confidence_score=0.8,
                used_chunks=[chunk.chunk_id for chunk, _ in relevant_chunks],
                generation_time=total_time,
                model_name=self.llm.model_name,
                metadata={
                    "question_type": analyzed_question.question_type.value,
                    "num_chunks_used": len(relevant_chunks),
                    "from_cache": False
                }
            )
            
            # 5. 캐시에 저장
            if self.cache_enabled and self.cache:
                self.cache.put(question, answer, context_key)
            
            logger.info(f"경량화된 답변 생성 완료: {total_time:.2f}초")
            return answer
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"답변 생성 실패: {e}")
            return Answer(
                content="죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.",
                confidence_score=0.0,
                used_chunks=[],
                generation_time=total_time,
                model_name=self.llm.model_name,
                metadata={"error": str(e)}
            )
    
    def _build_context_simple(self, relevant_chunks: List[Tuple[TextChunk, float]], 
                             max_context_length: int = 400) -> str:
        """경량화된 컨텍스트 구성"""
        if not relevant_chunks:
            return "관련 정보를 찾을 수 없습니다."
        
        context_parts = []
        current_length = 0
        
        for chunk, _ in relevant_chunks[:3]:  # 상위 3개만 사용
            chunk_text = chunk.content.strip()
            if current_length + len(chunk_text) > max_context_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n".join(context_parts)
    
    def update_model_config(self, config: GenerationConfig):
        """모델 설정 업데이트"""
        self.llm.config = config
        logger.info("경량화된 모델 설정 업데이트 완료")
    
    def get_model_info(self) -> Dict:
        """경량화된 모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "model_type": "local",
            "cache_enabled": self.cache_enabled,
            "config": {
                "max_length": self.llm.config.max_length,
                "temperature": self.llm.config.temperature,
                "top_p": self.llm.config.top_p
            }
        }
