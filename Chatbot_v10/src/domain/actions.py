"""
v5.2 Action Model
5-Tier Action 체계

Tier 정의:
- Tier1: Retrieval (정보 조회)
- Tier2: Reasoning (추론 실행)
- Tier3: Analysis / Computation / API
- Tier4: Report / Summaries
- Tier5: Workflow / Automation / Trigger
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field

from config.constants import ActionType, ValidationStatus, FeasibilityLevel


# ========== v5.2 새 Enum ==========

class ActionTier(Enum):
    """v5.2 Action Tier"""
    RETRIEVAL = 1       # 정보 조회
    REASONING = 2       # 추론 실행
    ANALYSIS = 3        # 분석/계산/API
    REPORT = 4          # 보고서/요약
    WORKFLOW = 5        # 워크플로우/자동화


class ActionStatus(Enum):
    """v5.2 Action 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class RiskLevel(Enum):
    """v5.2 위험도"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ========== v5.2 Action Trace ==========

class ActionTrace(BaseModel):
    """
    v5.2 Action 실행 추적
    모든 실행은 반드시 trace 로그로 저장
    """
    # 근거 정보
    source_fragments: List[str] = Field(default_factory=list, description="근거 Fragment ID들")
    source_relations: List[str] = Field(default_factory=list, description="사용된 관계 ID들")
    source_entities: List[str] = Field(default_factory=list, description="관련 엔티티 ID들")
    
    # 추론 과정
    reasoning_steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="추론 단계별 설명"
    )
    
    # v5.2: 입출력 기록
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # 온톨로지 컨텍스트
    ontology_subgraph: Optional[Dict[str, Any]] = Field(
        default=None,
        description="사용된 온톨로지 서브그래프"
    )
    
    # v5.2: 정책 버전
    policy_version: str = Field(default="v5.2")
    
    # v5.2: 실행 메트릭
    execution_time_ms: float = Field(default=0.0)
    resource_usage: Dict[str, float] = Field(default_factory=dict)


# ========== v5.2 Action Model ==========

class Action(BaseModel):
    """
    v5.2 Action Model
    
    기존 구조 + v5.2 확장:
    - tier: 5-Tier 계층
    - risk_level: 위험도
    - feasibility_score: 실행 가능성 점수
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # 기본 정보
    name: str = Field(description="Action 이름")
    description: str = Field(default="", description="Action 설명")
    action_type: ActionType = Field(description="Action 유형")
    
    # v5.2: Tier 및 위험도
    tier: ActionTier = Field(default=ActionTier.RETRIEVAL)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    
    # 실행 정보
    handler: Optional[str] = Field(default=None, description="실행 핸들러 함수명")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="실행 파라미터")
    expected_output: Optional[str] = Field(default=None, description="예상 출력 형태")
    
    # 트리거 조건
    trigger_intent: Optional[str] = Field(default=None, description="트리거 Intent")
    trigger_entities: List[str] = Field(default_factory=list, description="트리거 엔티티들")
    trigger_keywords: List[str] = Field(default_factory=list, description="트리거 키워드들")
    
    # LLM 생성 신뢰도
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 검증 정보
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    validation_score: float = Field(default=0.0)
    feasibility_level: FeasibilityLevel = Field(default=FeasibilityLevel.LOW)
    
    # v5.2: 실행 가능성 점수
    feasibility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # v5.2: 비용 추정
    cost_estimate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 과거 성능 기록 (RL reward 요소)
    execution_count: int = Field(default=0, description="실행 횟수")
    success_count: int = Field(default=0, description="성공 횟수")
    approval_count: int = Field(default=0, description="사용자 승인 횟수")
    
    # v5.2: 상태 추적
    status: ActionStatus = Field(default=ActionStatus.PENDING)
    
    # 추적 정보
    trace: Optional[ActionTrace] = Field(default=None, description="Action 추적 정보")
    
    # 실행 결과
    result: Optional[Any] = Field(default=None)
    error: Optional[str] = Field(default=None)
    
    # 메타데이터
    created_by: str = Field(default="system", description="생성자 (system/user)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = Field(default=None)
    
    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    @property
    def approval_rate(self) -> float:
        """승인률 계산"""
        if self.execution_count == 0:
            return 0.0
        return self.approval_count / self.execution_count
    
    def record_execution(self, success: bool, approved: bool = True) -> None:
        """실행 결과 기록"""
        self.execution_count += 1
        if success:
            self.success_count += 1
        if approved:
            self.approval_count += 1
        self.updated_at = datetime.utcnow()
        self.executed_at = datetime.utcnow()


# ========== v5.2 Action Candidate ==========

class ActionCandidate(BaseModel):
    """v5.2 Action 후보"""
    action: Action
    score: float = Field(default=0.0)           # 선택 점수
    intent_match: float = Field(default=0.0)    # 의도 매칭 점수
    history_success: float = Field(default=0.0) # 히스토리 성공률
    reasoning_confidence: float = Field(default=0.0)  # 추론 신뢰도
    
    @property
    def is_viable(self) -> bool:
        """실행 가능 여부"""
        return self.score >= 0.5 and self.action.feasibility_score >= 0.55


# ========== Action Result ==========

class ActionResult(BaseModel):
    """Action 실행 결과"""
    action_id: str = Field(description="실행된 Action ID")
    success: bool = Field(description="실행 성공 여부")
    
    # 결과 데이터
    output: Optional[Any] = Field(default=None, description="실행 출력")
    output_type: str = Field(default="text", description="출력 유형 (text/json/graph)")
    
    # RAG 응답 (온톨로지 기반 LLM 답변)
    rag_response: Optional[str] = Field(default=None, description="RAG 기반 응답")
    
    # 에러 정보
    error: Optional[str] = Field(default=None, description="에러 메시지")
    error_code: Optional[str] = Field(default=None)
    
    # 추적 정보
    trace: Optional[ActionTrace] = Field(default=None, description="실행 추적")
    
    # 메타데이터
    execution_time_ms: int = Field(default=0, description="실행 시간(ms)")
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 사용자 피드백 (RL reward signal)
    user_feedback: Optional[str] = Field(default=None, description="사용자 피드백")
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="사용자 평점")


# ========== v5.2 위험도 매핑 ==========

ACTION_RISK_MAP = {
    ActionType.RETRIEVE: RiskLevel.LOW,
    ActionType.REASON: RiskLevel.MEDIUM,
    ActionType.EXECUTE: RiskLevel.HIGH,
}


def get_tier_for_action_type(action_type: ActionType) -> ActionTier:
    """ActionType에 해당하는 Tier 반환"""
    tier_map = {
        ActionType.RETRIEVE: ActionTier.RETRIEVAL,
        ActionType.REASON: ActionTier.REASONING,
        ActionType.EXECUTE: ActionTier.WORKFLOW,
    }
    return tier_map.get(action_type, ActionTier.RETRIEVAL)
