"""
Action 관리 API
계획서 5: Action Layer
계획서 6: Admin / Human-in-the-loop
"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config.constants import ActionType, ValidationStatus, FeasibilityLevel
from src.services.action_service import ActionService
from src.services.ontology_service import OntologyService
from src.services.llm_service import LLMService
from src.validators.action_validator import ActionValidator
from src.validators.relation_validator import RelationValidator

router = APIRouter(prefix="/actions", tags=["Actions"])


# === Request/Response Models ===

class ActionCreateRequest(BaseModel):
    """Action 생성 요청"""
    name: str = Field(min_length=2, description="Action 이름")
    description: str = Field(min_length=10, description="Action 설명")
    action_type: str = Field(description="Action 유형 (retrieve/reason/execute)")
    handler: Optional[str] = Field(default=None, description="실행 핸들러")
    parameters: dict = Field(default_factory=dict, description="파라미터")
    trigger_entities: List[str] = Field(default_factory=list, description="트리거 엔티티")
    trigger_keywords: List[str] = Field(default_factory=list, description="트리거 키워드")


class ActionExecuteRequest(BaseModel):
    """Action 실행 요청"""
    parameters: dict = Field(default_factory=dict, description="실행 파라미터")
    force: bool = Field(default=False, description="강제 실행 (Feasibility 무시)")


class ActionFeedbackRequest(BaseModel):
    """Action 피드백 요청"""
    rating: int = Field(ge=1, le=5, description="평점 (1-5)")
    feedback: Optional[str] = Field(default=None, description="피드백 내용")


class AdminApprovalRequest(BaseModel):
    """Admin 승인 요청"""
    approved: bool = Field(description="승인 여부")
    reason: Optional[str] = Field(default=None, description="사유")


class ActionResponse(BaseModel):
    """Action 응답"""
    id: str
    name: str
    description: str
    action_type: str
    handler: Optional[str]
    parameters: dict
    trigger_entities: List[str]
    trigger_keywords: List[str]
    confidence: float
    validation_status: str
    validation_score: float
    feasibility_level: str
    execution_count: int
    success_rate: float
    approval_rate: float


class ActionExecutionResponse(BaseModel):
    """Action 실행 결과"""
    action_id: str
    success: bool
    output: Optional[str] = None
    output_type: str = "text"
    rag_response: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int


class ActionStatsResponse(BaseModel):
    """Action 통계"""
    total_actions: int
    by_type: dict
    by_status: dict
    avg_success_rate: float


# === Dependencies ===

def get_llm_service() -> LLMService:
    return LLMService()


def get_action_validator() -> ActionValidator:
    return ActionValidator()


def get_relation_validator() -> RelationValidator:
    return RelationValidator()


# 싱글톤 서비스들
_ontology_service: Optional[OntologyService] = None
_action_service: Optional[ActionService] = None


def get_ontology_service(
    validator: RelationValidator = Depends(get_relation_validator)
) -> OntologyService:
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = OntologyService(validator)
    return _ontology_service


def get_action_service(
    llm: LLMService = Depends(get_llm_service),
    ontology: OntologyService = Depends(get_ontology_service),
    validator: ActionValidator = Depends(get_action_validator)
) -> ActionService:
    global _action_service
    if _action_service is None:
        _action_service = ActionService(llm, ontology, validator)
    return _action_service


# === Endpoints ===

@router.post("", response_model=ActionResponse)
async def create_action(
    request: ActionCreateRequest,
    action_service: ActionService = Depends(get_action_service)
):
    """
    Action 생성
    
    계획서 5.1: Action Generator - LLM이 생성한 Action 등록
    계획서 5.2: Action Validator - 자동 검증 수행
    """
    # ActionType 변환
    try:
        action_type = ActionType(request.action_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 Action 유형: {request.action_type}. "
                   f"가능한 값: {[at.value for at in ActionType]}"
        )
    
    result = await action_service.create_action(
        name=request.name,
        description=request.description,
        action_type=action_type,
        handler=request.handler,
        parameters=request.parameters,
        trigger_entities=request.trigger_entities,
        trigger_keywords=request.trigger_keywords,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    action = result.data
    return ActionResponse(
        id=action.id,
        name=action.name,
        description=action.description,
        action_type=action.action_type.value,
        handler=action.handler,
        parameters=action.parameters,
        trigger_entities=action.trigger_entities,
        trigger_keywords=action.trigger_keywords,
        confidence=action.confidence,
        validation_status=action.validation_status.value,
        validation_score=action.validation_score,
        feasibility_level=action.feasibility_level.value,
        execution_count=action.execution_count,
        success_rate=action.success_rate,
        approval_rate=action.approval_rate,
    )


@router.get("", response_model=List[ActionResponse])
async def list_actions(
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    action_service: ActionService = Depends(get_action_service)
):
    """
    Action 목록 조회
    """
    actions = action_service.get_all_actions()
    
    # 필터링
    if action_type:
        try:
            at = ActionType(action_type)
            actions = [a for a in actions if a.action_type == at]
        except ValueError:
            pass
    
    if status:
        try:
            vs = ValidationStatus(status)
            actions = [a for a in actions if a.validation_status == vs]
        except ValueError:
            pass
    
    return [
        ActionResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            action_type=a.action_type.value,
            handler=a.handler,
            parameters=a.parameters,
            trigger_entities=a.trigger_entities,
            trigger_keywords=a.trigger_keywords,
            confidence=a.confidence,
            validation_status=a.validation_status.value,
            validation_score=a.validation_score,
            feasibility_level=a.feasibility_level.value,
            execution_count=a.execution_count,
            success_rate=a.success_rate,
            approval_rate=a.approval_rate,
        )
        for a in actions[:limit]
    ]


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: str,
    action_service: ActionService = Depends(get_action_service)
):
    """Action 조회"""
    action = action_service.get_action(action_id)
    
    if not action:
        raise HTTPException(status_code=404, detail="Action을 찾을 수 없습니다")
    
    return ActionResponse(
        id=action.id,
        name=action.name,
        description=action.description,
        action_type=action.action_type.value,
        handler=action.handler,
        parameters=action.parameters,
        trigger_entities=action.trigger_entities,
        trigger_keywords=action.trigger_keywords,
        confidence=action.confidence,
        validation_status=action.validation_status.value,
        validation_score=action.validation_score,
        feasibility_level=action.feasibility_level.value,
        execution_count=action.execution_count,
        success_rate=action.success_rate,
        approval_rate=action.approval_rate,
    )


@router.post("/{action_id}/execute", response_model=ActionExecutionResponse)
async def execute_action(
    action_id: str,
    request: ActionExecuteRequest,
    action_service: ActionService = Depends(get_action_service)
):
    """
    Action 실행
    
    계획서 5.3: 실행 가능성 평가 후 실행
    """
    result = await action_service.execute_action(
        action_id=action_id,
        parameters=request.parameters,
        force=request.force
    )
    
    if not result.success:
        # 실행 실패 케이스
        return ActionExecutionResponse(
            action_id=action_id,
            success=False,
            error=result.error,
            output_type="error",
            execution_time_ms=0
        )
    
    action_result = result.data
    
    return ActionExecutionResponse(
        action_id=action_result.action_id,
        success=action_result.success,
        output=str(action_result.output) if action_result.output else None,
        output_type=action_result.output_type,
        rag_response=action_result.rag_response,
        error=action_result.error,
        execution_time_ms=action_result.execution_time_ms,
    )


@router.post("/{action_id}/feedback")
async def submit_feedback(
    action_id: str,
    request: ActionFeedbackRequest,
    action_service: ActionService = Depends(get_action_service)
):
    """
    사용자 피드백 제출
    
    RL reward signal로 활용
    """
    result = await action_service.record_user_feedback(
        action_id=action_id,
        rating=request.rating,
        feedback=request.feedback
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {"message": "피드백이 기록되었습니다", "action_id": action_id}


# === Admin Endpoints ===

@router.post("/{action_id}/approve")
async def approve_action(
    action_id: str,
    request: AdminApprovalRequest,
    action_service: ActionService = Depends(get_action_service)
):
    """
    Action 승인/반려 (Admin)
    
    계획서 6: Admin / Human-in-the-loop
    """
    if request.approved:
        result = await action_service.approve_action(action_id)
        message = "Action이 승인되었습니다"
    else:
        if not request.reason:
            raise HTTPException(
                status_code=400,
                detail="반려 시 사유를 입력해주세요"
            )
        result = await action_service.reject_action(action_id, request.reason)
        message = "Action이 반려되었습니다"
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "message": message,
        "action_id": action_id,
        "approved": request.approved
    }


@router.get("/pending/review", response_model=List[ActionResponse])
async def get_pending_actions(
    action_service: ActionService = Depends(get_action_service)
):
    """
    검토 대기 Action 목록
    
    Admin이 검토해야 할 Action들
    """
    actions = action_service.get_all_actions()
    
    pending = [
        a for a in actions
        if a.validation_status == ValidationStatus.NEEDS_REVIEW
        or a.feasibility_level == FeasibilityLevel.LOW
    ]
    
    return [
        ActionResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            action_type=a.action_type.value,
            handler=a.handler,
            parameters=a.parameters,
            trigger_entities=a.trigger_entities,
            trigger_keywords=a.trigger_keywords,
            confidence=a.confidence,
            validation_status=a.validation_status.value,
            validation_score=a.validation_score,
            feasibility_level=a.feasibility_level.value,
            execution_count=a.execution_count,
            success_rate=a.success_rate,
            approval_rate=a.approval_rate,
        )
        for a in pending
    ]


@router.get("/stats/overview", response_model=ActionStatsResponse)
async def get_action_stats(
    action_service: ActionService = Depends(get_action_service)
):
    """Action 통계"""
    actions = action_service.get_all_actions()
    
    # 유형별 카운트
    by_type = {}
    for at in ActionType:
        by_type[at.value] = len([a for a in actions if a.action_type == at])
    
    # 상태별 카운트
    by_status = {}
    for vs in ValidationStatus:
        by_status[vs.value] = len([a for a in actions if a.validation_status == vs])
    
    # 평균 성공률
    success_rates = [a.success_rate for a in actions if a.execution_count > 0]
    avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
    
    return ActionStatsResponse(
        total_actions=len(actions),
        by_type=by_type,
        by_status=by_status,
        avg_success_rate=avg_success_rate,
    )


@router.get("/types")
async def get_action_types():
    """지원하는 Action 유형 조회"""
    return {
        "action_types": [
            {
                "value": at.value,
                "name": at.name,
                "description": {
                    "RETRIEVE": "조회/그래프/요약",
                    "REASON": "조건 기반 추론",
                    "EXECUTE": "알림/자동화/시스템 실행",
                }.get(at.name, "")
            }
            for at in ActionType
        ]
    }


@router.get("/handlers")
async def get_available_handlers(
    action_service: ActionService = Depends(get_action_service)
):
    """사용 가능한 핸들러 목록"""
    return {
        "handlers": [
            {
                "name": "retrieve_entity",
                "description": "엔티티 정보 조회",
                "parameters": ["entity_name"]
            },
            {
                "name": "retrieve_relations",
                "description": "엔티티 관계 조회",
                "parameters": ["entity_name"]
            },
            {
                "name": "analyze_causal_chain",
                "description": "인과 관계 분석",
                "parameters": ["entity_name", "max_depth"]
            },
            {
                "name": "generate_summary",
                "description": "엔티티 요약 생성",
                "parameters": ["entities"]
            },
        ]
    }
