"""
Action Validator
계획서 5.2: Action Validator (Rule + LLM + RL)
"""
from typing import Any, List, Dict

from config.constants import ActionType, FeasibilityLevel
from src.validators.base import BaseValidator, ValidationResult
from src.domain.actions import Action
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ActionValidator(BaseValidator):
    """
    Action 검증기
    
    계획서 5.2 검증 항목:
    - 온톨로지 기반 타당성
    - 입력 엔티티 유효성
    - 예상 출력 구조 준수 여부
    - 도메인 규약 위반 여부
    - 과거 Action들의 성능 기록 비교
    - 실행 리스크 평가
    
    RL reward 설계:
    - Action 성공률 (실행 후 오류 여부)
    - 사용자 승인률 (승인된 Action 비율)
    - 온톨로지 타당성 (Action 사용한 관계의 신뢰도)
    - 중복/불필요 Action 감소 (Action 공간 효율화)
    """
    
    def __init__(self):
        super().__init__()
        
        # Action 성능 기록
        self._action_performance: Dict[str, Dict[str, Any]] = {}
    
    async def validate(self, item: Any) -> ValidationResult:
        """Action 검증"""
        if isinstance(item, Action):
            return await self.validate_action(item)
        return ValidationResult(is_valid=False, score=0.0, reasons=["Invalid input"])
    
    async def validate_action(self, action: Action) -> ValidationResult:
        """
        Action 검증
        
        Args:
            action: 검증할 Action
        
        Returns:
            ValidationResult
        """
        reasons: List[str] = []
        
        # 1. Rule-based 검증
        rule_score, rule_reasons = self._rule_based_validation(action)
        reasons.extend(rule_reasons)
        
        # 2. 리스크 평가
        risk_score, risk_reasons = self._risk_assessment(action)
        reasons.extend(risk_reasons)
        
        # 3. 히스토리 기반 검증
        history_score = self._history_based_score(action)
        
        # 최종 점수 계산
        final_score = self._calculate_score(
            rule_score=rule_score,
            llm_score=risk_score,
            history_score=history_score
        )
        
        # Feasibility Level 결정
        feasibility_level = self._determine_feasibility(final_score, action)
        
        is_valid = final_score >= 0.5 and rule_score >= 0.4
        
        result = ValidationResult(
            is_valid=is_valid,
            score=final_score,
            reasons=reasons,
            feasibility_level=feasibility_level,
            details={
                "rule_score": rule_score,
                "risk_score": risk_score,
                "history_score": history_score,
            }
        )
        
        logger.debug(
            "action_validated",
            action_id=action.id,
            is_valid=is_valid,
            score=final_score,
            feasibility=feasibility_level.value
        )
        
        return result
    
    def _rule_based_validation(self, action: Action) -> tuple[float, List[str]]:
        """Rule 기반 검증"""
        score = 1.0
        reasons = []
        
        # 1. 이름 검증
        if not action.name or len(action.name) < 2:
            score -= 0.2
            reasons.append("Action 이름 누락 또는 너무 짧음")
        
        # 2. 설명 검증
        if not action.description or len(action.description) < 10:
            score -= 0.1
            reasons.append("Action 설명 부족")
        
        # 3. 핸들러 검증 (EXECUTE 타입은 핸들러 필수)
        if action.action_type == ActionType.EXECUTE and not action.handler:
            score -= 0.2
            reasons.append("EXECUTE 타입에 핸들러 없음")
        
        # 4. 트리거 조건 검증
        if not action.trigger_entities and not action.trigger_keywords:
            score -= 0.1
            reasons.append("트리거 조건 없음")
        
        # 5. 신뢰도 검증
        if action.confidence < 0.3:
            score -= 0.2
            reasons.append(f"LLM 신뢰도 낮음: {action.confidence:.2f}")
        
        return max(0.0, score), reasons
    
    def _risk_assessment(self, action: Action) -> tuple[float, List[str]]:
        """
        리스크 평가
        
        - 실행 영향도
        - 롤백 가능성
        - 외부 시스템 의존도
        """
        score = 1.0
        reasons = []
        
        # 1. Action 타입별 기본 리스크
        type_risk = {
            ActionType.RETRIEVE: 0.0,   # 조회는 리스크 없음
            ActionType.REASON: 0.1,     # 추론은 낮은 리스크
            ActionType.EXECUTE: 0.3,    # 실행은 중간 리스크
        }
        
        base_risk = type_risk.get(action.action_type, 0.2)
        score -= base_risk
        
        if base_risk > 0.2:
            reasons.append(f"실행 타입 리스크: {action.action_type.value}")
        
        # 2. 파라미터 검증
        risky_params = {"delete", "remove", "drop", "truncate", "update", "modify"}
        for param_key in action.parameters.keys():
            if any(r in param_key.lower() for r in risky_params):
                score -= 0.1
                reasons.append(f"위험 파라미터 감지: {param_key}")
        
        # 3. 외부 시스템 호출 감지
        if "api" in action.handler.lower() if action.handler else False:
            score -= 0.1
            reasons.append("외부 API 호출 감지")
        
        return max(0.0, score), reasons
    
    def _history_based_score(self, action: Action) -> float:
        """
        히스토리 기반 점수
        
        유사한 Action의 성공률 참조
        """
        # 1. 동일 핸들러의 성능 기록
        if action.handler and action.handler in self._action_performance:
            perf = self._action_performance[action.handler]
            success_rate = perf.get("success_rate", 0.5)
            approval_rate = perf.get("approval_rate", 0.5)
            return (success_rate + approval_rate) / 2
        
        # 2. 유사한 Action 타입의 성능
        type_feedbacks = [
            f for f in self._feedback_history
            if f.get("action_type") == action.action_type.value
        ]
        
        if type_feedbacks:
            approved = sum(1 for f in type_feedbacks if f.get("approved", False))
            return approved / len(type_feedbacks)
        
        return 0.5  # 기본값
    
    def _determine_feasibility(
        self,
        score: float,
        action: Action
    ) -> FeasibilityLevel:
        """
        실행 가능성 수준 결정
        
        계획서 5.3:
        - High → 자동 실행
        - Medium → 경고 후 실행
        - Low → Admin 승인 필요
        """
        if score >= 0.8:
            # EXECUTE 타입은 자동 실행 제한
            if action.action_type == ActionType.EXECUTE:
                return FeasibilityLevel.MEDIUM
            return FeasibilityLevel.HIGH
        elif score >= 0.5:
            return FeasibilityLevel.MEDIUM
        else:
            return FeasibilityLevel.LOW
    
    async def record_execution_result(
        self,
        action_id: str,
        handler: str,
        success: bool,
        execution_time_ms: int
    ):
        """
        실행 결과 기록
        
        RL reward signal로 활용
        """
        if handler not in self._action_performance:
            self._action_performance[handler] = {
                "total_executions": 0,
                "successful_executions": 0,
                "success_rate": 0.0,
                "total_approvals": 0,
                "approval_rate": 0.0,
                "avg_execution_time_ms": 0,
            }
        
        perf = self._action_performance[handler]
        perf["total_executions"] += 1
        
        if success:
            perf["successful_executions"] += 1
        
        perf["success_rate"] = (
            perf["successful_executions"] / perf["total_executions"]
        )
        
        # 실행 시간 평균 업데이트
        prev_avg = perf["avg_execution_time_ms"]
        n = perf["total_executions"]
        perf["avg_execution_time_ms"] = (
            (prev_avg * (n - 1) + execution_time_ms) / n
        )
        
        # 피드백 기록
        reward = 1.0 if success else -0.5
        self._reward_history.append(reward)
        await self._update_policy()
    
    async def record_feedback(
        self,
        action_id: str,
        approved: bool,
        reason: str = None
    ):
        """Admin 피드백 기록"""
        await super().record_feedback(action_id, approved, reason)
        
        # Action 타입별 통계 업데이트
        feedback_entry = {
            "action_id": action_id,
            "approved": approved,
            "reason": reason,
        }
        
        logger.info(
            "action_feedback_recorded",
            action_id=action_id,
            approved=approved
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            "handler_performance": self._action_performance,
            "policy_stats": self.get_policy_stats(),
            "total_validations": len(self._feedback_history),
        }
