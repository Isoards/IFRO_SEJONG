"""
v5.2 Action Executor
Action 실행 엔진

핵심 기능:
- Action 실행 및 결과 반환
- 모든 실행은 trace 로그로 저장
- 실행 시간/리소스 측정
"""
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
import time
import traceback

from src.domain.actions import (
    Action, ActionResult, ActionStatus, ActionTrace, ActionTier
)
from config.constants import ActionType
from src.shared.logging import get_logger

logger = get_logger(__name__)


# 핸들러 타입
ActionHandler = Callable[[Action, Dict[str, Any]], Awaitable[Any]]


class ActionExecutor:
    """
    v5.2 Action Executor
    
    모든 실행은 반드시 trace 로그로 저장:
    - timestamp
    - inputs
    - outputs
    - success/failure
    - reasoning_trace
    - policy_version
    """
    
    def __init__(self):
        # 등록된 핸들러
        self._handlers: Dict[str, ActionHandler] = {}
        
        # 실행 로그 저장소
        self._execution_logs: list[ActionResult] = []
        
        # 기본 핸들러 등록
        self._register_default_handlers()
    
    def register_handler(
        self,
        action_type: ActionType,
        handler: ActionHandler
    ):
        """Action 핸들러 등록"""
        self._handlers[action_type.value] = handler
    
    async def execute(
        self,
        action: Action,
        context: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """
        Action 실행
        
        Args:
            action: 실행할 Action
            context: 실행 컨텍스트 (그래프, 서비스 등)
        """
        context = context or {}
        start_time = time.time()
        
        # 상태 업데이트
        action.status = ActionStatus.EXECUTING
        
        try:
            # 핸들러 찾기
            handler = self._handlers.get(action.action_type.value)
            
            if not handler:
                # 기본 핸들러 사용
                handler = self._default_handler
            
            # 실행
            output = await handler(action, context)
            
            # 성공 결과 생성
            execution_time = (time.time() - start_time) * 1000
            
            result = ActionResult(
                action_id=action.id,
                success=True,
                output=output,
                output_type=self._determine_output_type(output),
                execution_time_ms=int(execution_time),
                trace=self._create_execution_trace(action, context, output, None)
            )
            
            # Action 상태 업데이트
            action.status = ActionStatus.COMPLETED
            action.executed_at = datetime.utcnow()
            action.result = output
            action.record_execution(success=True)
            
            logger.info(
                "action_executed",
                action_id=action.id,
                action_type=action.action_type.value,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            result = ActionResult(
                action_id=action.id,
                success=False,
                error=str(e),
                error_code=e.__class__.__name__,
                execution_time_ms=int(execution_time),
                trace=self._create_execution_trace(action, context, None, str(e))
            )
            
            # Action 상태 업데이트
            action.status = ActionStatus.FAILED
            action.executed_at = datetime.utcnow()
            action.error = str(e)
            action.record_execution(success=False)
            
            logger.error(
                "action_execution_failed",
                action_id=action.id,
                error=str(e),
                traceback=traceback.format_exc()
            )
        
        # 로그 저장
        self._execution_logs.append(result)
        
        return result
    
    def _create_execution_trace(
        self,
        action: Action,
        context: Dict[str, Any],
        output: Any,
        error: Optional[str]
    ) -> ActionTrace:
        """실행 Trace 생성"""
        # 기존 trace가 있으면 확장
        if action.trace:
            trace = action.trace
        else:
            trace = ActionTrace()
        
        # 입출력 기록
        trace.inputs = {
            "action_type": action.action_type.value,
            "tier": action.tier.value if action.tier else None,
            "parameters": action.parameters,
            "entities": action.trigger_entities,
        }
        
        if output is not None:
            trace.outputs = {
                "result": str(output)[:500],  # 최대 500자
                "type": self._determine_output_type(output)
            }
        
        if error:
            trace.outputs["error"] = error
        
        return trace
    
    def _determine_output_type(self, output: Any) -> str:
        """출력 유형 결정"""
        if output is None:
            return "none"
        if isinstance(output, dict):
            return "json"
        if isinstance(output, list):
            return "list"
        if isinstance(output, str):
            return "text"
        return "object"
    
    def _register_default_handlers(self):
        """기본 핸들러 등록"""
        self._handlers[ActionType.RETRIEVE.value] = self._handle_retrieve
        self._handlers[ActionType.REASON.value] = self._handle_reason
        self._handlers[ActionType.EXECUTE.value] = self._handle_execute
    
    async def _default_handler(
        self,
        action: Action,
        context: Dict[str, Any]
    ) -> Any:
        """기본 핸들러"""
        return {
            "message": f"Executed action: {action.name}",
            "action_type": action.action_type.value,
            "tier": action.tier.value if action.tier else None
        }
    
    async def _handle_retrieve(
        self,
        action: Action,
        context: Dict[str, Any]
    ) -> Any:
        """RETRIEVE 핸들러"""
        ontology_service = context.get("ontology_service")
        
        if not ontology_service:
            return {"entities": [], "message": "No ontology service available"}
        
        # 엔티티 검색
        entities = action.trigger_entities
        if entities:
            results = []
            for name in entities:
                entity = ontology_service.graph.get_entity_by_name(name)
                if entity:
                    results.append({
                        "id": entity.id,
                        "name": entity.canonical_name,
                        "type": entity.entity_type,
                        "description": entity.description
                    })
            return {"entities": results}
        
        return {"entities": [], "message": "No entities specified"}
    
    async def _handle_reason(
        self,
        action: Action,
        context: Dict[str, Any]
    ) -> Any:
        """REASON 핸들러"""
        # 추론 엔진 사용
        from src.reasoning import PathReasoner, MechanismReasoner
        
        ontology_service = context.get("ontology_service")
        if not ontology_service:
            return {"reasoning": "No ontology service available"}
        
        entities = action.trigger_entities
        if len(entities) >= 2:
            # 두 엔티티 간 경로 추론
            source = ontology_service.graph.get_entity_by_name(entities[0])
            target = ontology_service.graph.get_entity_by_name(entities[1])
            
            if source and target:
                reasoner = PathReasoner(ontology_service.graph)
                result = await reasoner.reason(source.id, target.id)
                
                return {
                    "success": result.success,
                    "confidence": result.confidence,
                    "sign": result.sign,
                    "explanation": result.explanation
                }
        
        return {"reasoning": "Insufficient entities for reasoning"}
    
    async def _handle_execute(
        self,
        action: Action,
        context: Dict[str, Any]
    ) -> Any:
        """EXECUTE 핸들러"""
        # 실행 로직 (보안 검사 필요)
        return {
            "executed": True,
            "action": action.name,
            "message": "Action executed (stub)"
        }
    
    def get_execution_logs(
        self,
        limit: int = 100
    ) -> list[ActionResult]:
        """실행 로그 조회"""
        return self._execution_logs[-limit:]
    
    def get_success_rate(self) -> float:
        """전체 성공률"""
        if not self._execution_logs:
            return 0.0
        success = sum(1 for r in self._execution_logs if r.success)
        return success / len(self._execution_logs)
