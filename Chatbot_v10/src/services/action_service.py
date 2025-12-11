"""
Action 서비스
계획서 5: Action Layer
"""
import time
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from config.settings import get_settings
from config.constants import ActionType, ValidationStatus, FeasibilityLevel
from src.domain.actions import Action, ActionResult, ActionTrace
from src.services.llm_service import LLMService
from src.services.ontology_service import OntologyService
from src.validators.action_validator import ActionValidator
from src.shared.logging import get_logger, log_error
from src.shared.types import Result

logger = get_logger(__name__)


class ActionService:
    """
    Action 관리 서비스
    
    계획서 5.1: Action Generator (LLM)
    계획서 5.2: Action Validator (Rule + LLM + RL)
    계획서 5.3: 실행 가능성 평가 (Feasibility Layer)
    
    원칙 4: 단일 책임 - Action 생성/검증/실행만 담당
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        ontology_service: OntologyService,
        validator: ActionValidator
    ):
        self.llm = llm_service
        self.ontology = ontology_service
        self.validator = validator
        self.settings = get_settings()
        
        # Action 저장소
        self._actions: Dict[str, Action] = {}
        
        # Action 핸들러 레지스트리
        self._handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """기본 Action 핸들러 등록"""
        self._handlers = {
            "retrieve_entity": self._handle_retrieve_entity,
            "retrieve_relations": self._handle_retrieve_relations,
            "analyze_causal_chain": self._handle_analyze_causal_chain,
            "generate_summary": self._handle_generate_summary,
        }
    
    def register_handler(self, name: str, handler: Callable):
        """커스텀 Action 핸들러 등록"""
        self._handlers[name] = handler
    
    async def create_action(
        self,
        name: str,
        description: str,
        action_type: ActionType,
        handler: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        trigger_entities: Optional[List[str]] = None,
        trigger_keywords: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> Result[Action]:
        """
        Action 생성
        """
        action = Action(
            name=name,
            description=description,
            action_type=action_type,
            handler=handler,
            parameters=parameters or {},
            trigger_entities=trigger_entities or [],
            trigger_keywords=trigger_keywords or [],
            created_by=created_by,
            validation_status=ValidationStatus.PENDING,
        )
        
        # Validator로 검증
        validation_result = await self.validator.validate_action(action)
        
        action.validation_status = (
            ValidationStatus.APPROVED if validation_result.is_valid
            else ValidationStatus.NEEDS_REVIEW
        )
        action.validation_score = validation_result.score
        action.feasibility_level = validation_result.feasibility_level
        
        # 저장
        self._actions[action.id] = action
        
        logger.info(
            "action_created",
            action_id=action.id,
            name=name,
            status=action.validation_status.value
        )
        
        return Result.ok(action)
    
    async def execute_action(
        self,
        action_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> Result[ActionResult]:
        """
        Action 실행
        
        계획서 5.3: 실행 가능성 평가 후 실행
        """
        action = self._actions.get(action_id)
        if not action:
            return Result.fail(
                error="Action을 찾을 수 없습니다",
                error_code="ACTION_NOT_FOUND"
            )
        
        # 실행 가능성 검사
        if not force:
            feasibility_result = await self._check_feasibility(action)
            
            if feasibility_result.level == FeasibilityLevel.LOW:
                return Result.fail(
                    error="실행 가능성 낮음 - Admin 승인 필요",
                    error_code="ADMIN_APPROVAL_REQUIRED",
                    details=feasibility_result.details
                )
        
        # 실행
        start_time = time.time()
        
        try:
            # 파라미터 병합
            exec_params = {**action.parameters, **(parameters or {})}
            
            # 핸들러 실행
            handler = self._handlers.get(action.handler)
            if handler:
                output = await handler(exec_params)
            else:
                # 기본 처리 (RAG 응답)
                output = await self._default_handler(action, exec_params)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 성공 기록
            action.record_execution(success=True, approved=True)
            
            # Trace 생성
            trace = ActionTrace(
                source_entities=action.trigger_entities,
                reasoning_steps=[{
                    "step": "execution",
                    "handler": action.handler,
                    "parameters": exec_params,
                }]
            )
            
            result = ActionResult(
                action_id=action_id,
                success=True,
                output=output.get("data") if isinstance(output, dict) else output,
                output_type=output.get("type", "text") if isinstance(output, dict) else "text",
                rag_response=output.get("rag_response") if isinstance(output, dict) else None,
                trace=trace,
                execution_time_ms=execution_time,
            )
            
            logger.info(
                "action_executed",
                action_id=action_id,
                execution_time_ms=execution_time
            )
            
            return Result.ok(result)
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            # 실패 기록
            action.record_execution(success=False, approved=True)
            
            log_error(logger, e, {"action_id": action_id})
            
            result = ActionResult(
                action_id=action_id,
                success=False,
                error=str(e),
                error_code="EXECUTION_FAILED",
                execution_time_ms=execution_time,
            )
            
            return Result.fail(
                error=str(e),
                error_code="ACTION_EXECUTION_FAILED",
                details={"result": result.model_dump()}
            )
    
    async def _check_feasibility(self, action: Action) -> Any:
        """
        실행 가능성 검사
        
        계획서 5.3:
        - 리소스 존재 여부
        - 온톨로지 커버리지
        - Action 과거 성능 기록
        - 잠재적 위험 평가
        """
        class FeasibilityResult:
            def __init__(self, level: FeasibilityLevel, details: Dict[str, Any]):
                self.level = level
                self.details = details
        
        score = 0.0
        details = {}
        
        # 1. 과거 성능 기록
        if action.execution_count > 0:
            success_rate = action.success_rate
            details["success_rate"] = success_rate
            score += success_rate * 0.3
        else:
            score += 0.5 * 0.3  # 첫 실행은 중립
        
        # 2. 검증 점수
        details["validation_score"] = action.validation_score
        score += action.validation_score * 0.3
        
        # 3. 핸들러 존재 여부
        has_handler = action.handler in self._handlers
        details["has_handler"] = has_handler
        score += 0.2 if has_handler else 0.0
        
        # 4. 온톨로지 커버리지
        coverage = 0.0
        if action.trigger_entities:
            found = 0
            for entity_name in action.trigger_entities:
                if self.ontology.graph.get_entity_by_name(entity_name):
                    found += 1
            coverage = found / len(action.trigger_entities)
        else:
            coverage = 1.0  # 엔티티 없으면 체크 불필요
        
        details["ontology_coverage"] = coverage
        score += coverage * 0.2
        
        # Level 결정
        if score >= self.settings.feasibility_high_threshold:
            level = FeasibilityLevel.HIGH
        elif score >= self.settings.feasibility_medium_threshold:
            level = FeasibilityLevel.MEDIUM
        else:
            level = FeasibilityLevel.LOW
        
        details["total_score"] = score
        
        return FeasibilityResult(level, details)
    
    async def _default_handler(
        self,
        action: Action,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """기본 Action 핸들러 - RAG 응답 생성"""
        query = parameters.get("query", action.description)
        
        # 온톨로지 컨텍스트 생성
        context = self.ontology.to_context_string(action.trigger_entities)
        
        # RAG 응답 생성
        response = await self.llm.generate_rag_response(query, context)
        
        return {
            "type": "text",
            "data": response,
            "rag_response": response,
        }
    
    # === 기본 핸들러들 ===
    
    async def _handle_retrieve_entity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """엔티티 조회 핸들러"""
        entity_name = params.get("entity_name")
        if not entity_name:
            return {"type": "error", "data": "entity_name 파라미터 필요"}
        
        entity = self.ontology.graph.get_entity_by_name(entity_name)
        if entity:
            return {"type": "json", "data": entity.model_dump()}
        else:
            return {"type": "error", "data": f"엔티티 '{entity_name}'을 찾을 수 없습니다"}
    
    async def _handle_retrieve_relations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """관계 조회 핸들러"""
        entity_name = params.get("entity_name")
        if not entity_name:
            return {"type": "error", "data": "entity_name 파라미터 필요"}
        
        mechanisms = self.ontology.get_related_mechanisms(entity_name)
        return {"type": "json", "data": mechanisms}
    
    async def _handle_analyze_causal_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """인과 관계 분석 핸들러"""
        entity_name = params.get("entity_name")
        max_depth = params.get("max_depth", 5)
        
        if not entity_name:
            return {"type": "error", "data": "entity_name 파라미터 필요"}
        
        chains = self.ontology.get_causal_chain(entity_name, max_depth)
        return {"type": "json", "data": chains}
    
    async def _handle_generate_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """요약 생성 핸들러"""
        entities = params.get("entities", [])
        
        context = self.ontology.to_context_string(entities)
        query = f"다음 엔티티들에 대해 요약해주세요: {', '.join(entities)}"
        
        response = await self.llm.generate_rag_response(query, context)
        return {"type": "text", "data": response, "rag_response": response}
    
    # === 관리 메서드들 ===
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Action 조회"""
        return self._actions.get(action_id)
    
    def get_all_actions(self) -> List[Action]:
        """모든 Action 조회"""
        return list(self._actions.values())
    
    def get_actions_by_type(self, action_type: ActionType) -> List[Action]:
        """유형별 Action 조회"""
        return [a for a in self._actions.values() if a.action_type == action_type]
    
    async def approve_action(self, action_id: str) -> Result[Action]:
        """
        Action 승인 (Admin)
        계획서 6: Admin / Human-in-the-loop
        """
        action = self._actions.get(action_id)
        if not action:
            return Result.fail(error="Action not found", error_code="NOT_FOUND")
        
        action.validation_status = ValidationStatus.APPROVED
        action.approval_count += 1
        
        # RL reward signal 기록
        await self.validator.record_feedback(action_id, approved=True)
        
        return Result.ok(action)
    
    async def reject_action(
        self,
        action_id: str,
        reason: str
    ) -> Result[Action]:
        """
        Action 반려 (Admin)
        """
        action = self._actions.get(action_id)
        if not action:
            return Result.fail(error="Action not found", error_code="NOT_FOUND")
        
        action.validation_status = ValidationStatus.REJECTED
        
        # RL negative reward signal 기록
        await self.validator.record_feedback(action_id, approved=False, reason=reason)
        
        return Result.ok(action)
    
    async def record_user_feedback(
        self,
        action_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> Result[None]:
        """
        사용자 피드백 기록
        RL reward signal로 활용
        """
        action = self._actions.get(action_id)
        if not action:
            return Result.fail(error="Action not found", error_code="NOT_FOUND")
        
        # Validator에 피드백 전달
        await self.validator.record_user_feedback(action_id, rating, feedback)
        
        return Result.ok(None)
