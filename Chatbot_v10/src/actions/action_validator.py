"""
v5.2 Action Validator
Action 검증 및 Feasibility 평가

핵심 기능:
- Feasibility Score 계산
- AUTO_EXECUTE / REQUIRE_APPROVAL / REJECT 결정
- 규칙 기반 보안/안전 필터
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from src.domain.actions import (
    Action, ActionTier, ActionStatus, RiskLevel,
    ACTION_RISK_MAP
)
from config.constants import ActionType, ValidationStatus
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ActionDecision(Enum):
    """v5.2 Action 결정"""
    AUTO_EXECUTE = "auto_execute"        # F >= 0.75
    REQUIRE_APPROVAL = "require_approval"  # 0.55 <= F < 0.75
    REJECT = "reject"                    # F < 0.55


@dataclass
class ActionValidationResult:
    """Action 검증 결과"""
    decision: ActionDecision
    feasibility_score: float
    data_ready: float
    resource_available: float
    reasoning_confidence: float
    risk_factor: float
    reasons: List[str]
    warnings: List[str]


class ActionValidator:
    """
    v5.2 Action Validator
    
    Feasibility Score:
    F = 0.4*data_ready + 0.2*resource_available + 0.2*reasoning_confidence + 0.2*(1-risk_level)
    
    Decision:
    - F >= 0.75 → AUTO_EXECUTE
    - 0.55 <= F < 0.75 → REQUIRE_APPROVAL
    - F < 0.55 → REJECT
    """
    
    # v5.2 임계값
    AUTO_EXECUTE_THRESHOLD = 0.75
    APPROVAL_THRESHOLD = 0.55
    
    def __init__(self):
        # 리소스 상태 (실제 구현에서는 외부 시스템 조회)
        self._resource_status = {
            "llm_available": True,
            "api_available": True,
            "storage_available": True,
        }
    
    async def validate(
        self,
        action: Action,
        context: Optional[Dict[str, Any]] = None
    ) -> ActionValidationResult:
        """
        Action 검증 및 Feasibility 평가
        
        Args:
            action: 검증할 Action
            context: 추가 컨텍스트 (예: 현재 그래프 상태)
        """
        context = context or {}
        reasons = []
        warnings = []
        
        # 1. 데이터 준비도 평가
        data_ready = self._evaluate_data_ready(action, context)
        
        # 2. 리소스 가용성 평가
        resource_available = self._evaluate_resource_available(action)
        
        # 3. 추론 신뢰도
        reasoning_confidence = action.confidence
        
        # 4. 위험도 평가
        risk_level = self._evaluate_risk(action)
        risk_factor = 1.0 - (risk_level / 4.0)  # 1~4 → 0.75~0.0
        
        # 5. v5.2 Feasibility 공식
        feasibility_score = (
            0.4 * data_ready +
            0.2 * resource_available +
            0.2 * reasoning_confidence +
            0.2 * risk_factor
        )
        
        # 6. 안전 규칙 검사
        safety_check, safety_reasons = self._safety_check(action)
        if not safety_check:
            reasons.extend(safety_reasons)
            feasibility_score *= 0.5  # 안전 검사 실패 시 점수 감소
        
        # 7. 결정
        if feasibility_score >= self.AUTO_EXECUTE_THRESHOLD and safety_check:
            decision = ActionDecision.AUTO_EXECUTE
        elif feasibility_score >= self.APPROVAL_THRESHOLD:
            decision = ActionDecision.REQUIRE_APPROVAL
            warnings.append(f"Feasibility score {feasibility_score:.2f} requires approval")
        else:
            decision = ActionDecision.REJECT
            reasons.append(f"Feasibility score {feasibility_score:.2f} below threshold")
        
        # 8. Action 상태 업데이트
        action.feasibility_score = feasibility_score
        action.validation_score = feasibility_score
        
        if decision == ActionDecision.REJECT:
            action.status = ActionStatus.REJECTED
            action.validation_status = ValidationStatus.REJECTED
        elif decision == ActionDecision.REQUIRE_APPROVAL:
            action.status = ActionStatus.PENDING
            action.validation_status = ValidationStatus.NEEDS_REVIEW
        else:
            action.status = ActionStatus.APPROVED
            action.validation_status = ValidationStatus.APPROVED
        
        logger.info(
            "action_validated",
            action_id=action.id,
            decision=decision.value,
            feasibility=feasibility_score
        )
        
        return ActionValidationResult(
            decision=decision,
            feasibility_score=feasibility_score,
            data_ready=data_ready,
            resource_available=resource_available,
            reasoning_confidence=reasoning_confidence,
            risk_factor=risk_factor,
            reasons=reasons,
            warnings=warnings
        )
    
    def _evaluate_data_ready(
        self,
        action: Action,
        context: Dict[str, Any]
    ) -> float:
        """데이터 준비도 평가"""
        score = 0.5  # 기본값
        
        # 트리거 엔티티가 있으면 점수 증가
        if action.trigger_entities:
            score += 0.2
        
        # Intent가 있으면 점수 증가
        if action.trigger_intent:
            score += 0.1
        
        # Trace가 있으면 점수 증가 (추론 근거 존재)
        if action.trace and action.trace.reasoning_steps:
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_resource_available(self, action: Action) -> float:
        """리소스 가용성 평가"""
        required_resources = []
        
        # Tier별 필요 리소스
        if action.tier in {ActionTier.REASONING, ActionTier.REPORT}:
            required_resources.append("llm_available")
        
        if action.tier == ActionTier.ANALYSIS:
            required_resources.append("api_available")
        
        if action.tier == ActionTier.WORKFLOW:
            required_resources.extend(["api_available", "storage_available"])
        
        if not required_resources:
            return 1.0
        
        available = sum(
            1 for r in required_resources
            if self._resource_status.get(r, False)
        )
        return available / len(required_resources)
    
    def _evaluate_risk(self, action: Action) -> int:
        """위험도 평가 (1~4)"""
        # Action에 이미 risk_level이 있으면 사용
        if action.risk_level:
            return action.risk_level.value
        
        # ActionType에서 추정
        risk = ACTION_RISK_MAP.get(action.action_type, RiskLevel.MEDIUM)
        return risk.value
    
    def _safety_check(self, action: Action) -> tuple[bool, List[str]]:
        """안전 규칙 검사"""
        reasons = []
        
        # HIGH/CRITICAL 위험도는 자동 실행 불가
        if action.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            reasons.append(f"High risk action requires manual approval")
        
        # WORKFLOW tier는 추가 검증 필요
        if action.tier == ActionTier.WORKFLOW:
            if not action.trace or not action.trace.reasoning_steps:
                reasons.append("Workflow actions require reasoning trace")
        
        # 성공률이 낮은 Action 경고
        if action.execution_count > 5 and action.success_rate < 0.3:
            reasons.append(f"Low historical success rate: {action.success_rate:.1%}")
        
        return len(reasons) == 0, reasons
    
    def update_resource_status(self, resource: str, available: bool):
        """리소스 상태 업데이트"""
        self._resource_status[resource] = available
