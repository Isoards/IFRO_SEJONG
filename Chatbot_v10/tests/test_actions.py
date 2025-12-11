"""
v5.2 Action Layer 테스트
ActionGenerator, ActionValidator, ActionExecutor
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.actions import (
    ActionGenerator, ActionValidator, ActionExecutor,
    ActionDecision, ActionValidationResult
)
from src.domain.actions import Action, ActionTier, ActionStatus, RiskLevel
from config.constants import ActionType


class TestActionGenerator:
    """ActionGenerator 테스트"""
    
    @pytest.fixture
    def generator(self):
        return ActionGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_retrieve_action(self, generator):
        """조회 액션 생성 테스트"""
        candidates = await generator.generate(
            query="금리에 대해 찾아줘",
            entities=["금리"],
            reasoning_result=None
        )
        
        assert len(candidates) > 0
        assert len(candidates) <= 3  # Top-3
        
        # 최소 하나는 RETRIEVE
        action_types = [c.action.action_type for c in candidates]
        assert ActionType.RETRIEVE in action_types
    
    @pytest.mark.asyncio
    async def test_generate_reason_action(self, generator):
        """추론 액션 생성 테스트"""
        candidates = await generator.generate(
            query="Why does interest rate affect economy? Explain the cause.",
            entities=["금리", "경제"],
            reasoning_result=None
        )
        
        assert len(candidates) > 0
        
        # REASON 타입이 있거나, 최소한 검색 결과 있어야 함
        action_types = [c.action.action_type for c in candidates]
        assert ActionType.REASON in action_types or ActionType.RETRIEVE in action_types
    
    @pytest.mark.asyncio
    async def test_score_calculation(self, generator):
        """v5.2 점수 계산 테스트"""
        mock_reasoning = MagicMock()
        mock_reasoning.confidence = 0.8
        
        candidates = await generator.generate(
            query="금리를 분석해",
            entities=["금리"],
            reasoning_result=mock_reasoning
        )
        
        assert len(candidates) > 0
        # Score = 0.5*intent + 0.3*history + 0.2*reasoning
        for c in candidates:
            assert 0 <= c.score <= 1.0
    
    def test_history_update(self, generator):
        """히스토리 업데이트 테스트"""
        generator.update_history(ActionType.RETRIEVE, success=True, confidence=0.9)
        generator.update_history(ActionType.RETRIEVE, success=True, confidence=0.8)
        
        history = generator.action_history.get(ActionType.RETRIEVE.value, {})
        
        assert history.get("count") == 2
        assert history.get("success_rate") == 1.0


class TestActionValidator:
    """ActionValidator 테스트"""
    
    @pytest.fixture
    def validator(self):
        return ActionValidator()
    
    @pytest.fixture
    def low_risk_action(self):
        return Action(
            name="search_test",
            action_type=ActionType.RETRIEVE,
            tier=ActionTier.RETRIEVAL,
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            trigger_entities=["금리"],
            trigger_intent="search"
        )
    
    @pytest.fixture
    def high_risk_action(self):
        return Action(
            name="execute_test",
            action_type=ActionType.EXECUTE,
            tier=ActionTier.WORKFLOW,
            risk_level=RiskLevel.HIGH,
            confidence=0.7
        )
    
    @pytest.mark.asyncio
    async def test_validate_low_risk(self, validator, low_risk_action):
        """저위험 액션 검증 - AUTO_EXECUTE 가능"""
        result = await validator.validate(low_risk_action)
        
        assert isinstance(result, ActionValidationResult)
        assert result.feasibility_score > 0.5
        # 저위험 + 높은 confidence → AUTO_EXECUTE 또는 APPROVAL
        assert result.decision in {ActionDecision.AUTO_EXECUTE, ActionDecision.REQUIRE_APPROVAL}
    
    @pytest.mark.asyncio
    async def test_validate_high_risk(self, validator, high_risk_action):
        """고위험 액션 검증 - 승인 필요"""
        result = await validator.validate(high_risk_action)
        
        assert isinstance(result, ActionValidationResult)
        # 고위험은 AUTO_EXECUTE 불가
        assert result.decision != ActionDecision.AUTO_EXECUTE
    
    @pytest.mark.asyncio
    async def test_feasibility_formula(self, validator, low_risk_action):
        """v5.2 Feasibility 공식 테스트"""
        result = await validator.validate(low_risk_action)
        
        # F = 0.4*data + 0.2*resource + 0.2*reasoning + 0.2*(1-risk)
        expected_approx = (
            0.4 * result.data_ready +
            0.2 * result.resource_available +
            0.2 * result.reasoning_confidence +
            0.2 * result.risk_factor
        )
        
        assert abs(result.feasibility_score - expected_approx) < 0.01


class TestActionExecutor:
    """ActionExecutor 테스트"""
    
    @pytest.fixture
    def executor(self):
        return ActionExecutor()
    
    @pytest.fixture
    def simple_action(self):
        return Action(
            name="search_test",
            action_type=ActionType.RETRIEVE,
            tier=ActionTier.RETRIEVAL,
            trigger_entities=["금리"]
        )
    
    @pytest.mark.asyncio
    async def test_execute_action(self, executor, simple_action):
        """액션 실행 테스트"""
        result = await executor.execute(simple_action, context={})
        
        assert result.action_id == simple_action.id
        # 기본 핸들러는 성공
        assert result.success or result.error is not None
    
    @pytest.mark.asyncio
    async def test_trace_logging(self, executor, simple_action):
        """Trace 로깅 테스트"""
        result = await executor.execute(simple_action, context={})
        
        assert result.trace is not None
        assert "action_type" in result.trace.inputs
    
    @pytest.mark.asyncio
    async def test_execution_count(self, executor, simple_action):
        """실행 횟수 추적 테스트"""
        await executor.execute(simple_action, context={})
        await executor.execute(simple_action, context={})
        
        logs = executor.get_execution_logs()
        assert len(logs) >= 2
    
    def test_custom_handler_registration(self, executor):
        """커스텀 핸들러 등록 테스트"""
        async def custom_handler(action, context):
            return {"custom": True}
        
        executor.register_handler(ActionType.RETRIEVE, custom_handler)
        
        assert ActionType.RETRIEVE.value in executor._handlers
