"""
환경변수 & 설정 관리
원칙 2: 선택값 및 설정값 분리 (Configuration Separation)
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 - 환경변수로부터 로드"""
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama 서버 주소")
    ollama_model: str = Field(default="llama3.2:latest", description="기본 LLM 모델")
    ollama_embedding_model: str = Field(default="nomic-embed-text", description="임베딩 모델")
    ollama_timeout: int = Field(default=120, description="Ollama 요청 타임아웃(초)")
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./ontology.db")
    chroma_persist_dir: str = Field(default="./chroma_db")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    
    # Logging
    log_level: str = Field(default="INFO")
    error_log_path: Path = Field(default=Path("./logs/errors.log"))
    
    # RL Validator Settings
    rl_learning_rate: float = Field(default=0.01, description="RL 학습률")
    rl_reward_decay: float = Field(default=0.95, description="보상 감쇠율")
    entity_similarity_threshold: float = Field(default=0.85, description="엔티티 유사도 임계값")
    action_confidence_threshold: float = Field(default=0.7, description="액션 신뢰도 임계값")
    
    # Feasibility Thresholds
    feasibility_high_threshold: float = Field(default=0.8, description="자동 실행 임계값")
    feasibility_medium_threshold: float = Field(default=0.5, description="경고 후 실행 임계값")
    
    # v4.2 Validation Pyramid Weights
    # Score = Rule * α + SmallModel * β + LLM * γ + History(RL) * δ
    validation_alpha: float = Field(default=0.35, description="Rule 점수 가중치 (α)")
    validation_beta: float = Field(default=0.15, description="Small Model 점수 가중치 (β)")
    validation_gamma: float = Field(default=0.30, description="LLM 점수 가중치 (γ)")
    validation_delta: float = Field(default=0.20, description="History/RL 점수 가중치 (δ)")
    
    # v4.2 Validation Pyramid Thresholds
    rule_reject_threshold: float = Field(default=0.3, description="L0 Rule reject 임계값")
    small_model_reject_threshold: float = Field(default=0.4, description="L1 Small Model reject 임계값")
    final_validation_threshold: float = Field(default=0.6, description="L2 최종 검증 통과 임계값")
    
    # v4.2 Hairball Prevention (헤어볼 방지)
    max_entity_out_degree: int = Field(default=50, description="엔티티 최대 출력 차수")
    max_entity_in_degree: int = Field(default=50, description="엔티티 최대 입력 차수")
    transitive_reduction_threshold: int = Field(default=1000, description="Transitive Reduction 자동 실행 엣지 수")
    rag_context_max_depth: int = Field(default=2, description="RAG 컨텍스트 indirect path 최대 깊이")
    
    # v4.2 Small Model (optional)
    small_model_endpoint: str = Field(default="", description="Small Model API endpoint (빈 값이면 pass-through)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 - One Source of Truth"""
    return Settings()
