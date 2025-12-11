"""
v5.2 Reasoning Engine 테스트
PathReasoner, MechanismReasoner, ScenarioSimulator
"""
import pytest
from unittest.mock import MagicMock

from src.reasoning import (
    PathReasoner, MechanismReasoner, ScenarioSimulator,
    ScenarioInput, ReasoningResult, ReasoningResultType
)
from src.domain.relations import OntologyGraph, Relation
from src.domain.entities import Entity
from config.constants import RelationType


class TestPathReasoner:
    """PathReasoner 테스트"""
    
    @pytest.fixture
    def graph_with_chain(self):
        """A → B → C 체인 그래프"""
        graph = OntologyGraph()
        
        e1 = Entity(id="e1", canonical_name="금리", entity_type="concept")
        e2 = Entity(id="e2", canonical_name="투자", entity_type="concept")
        e3 = Entity(id="e3", canonical_name="경제성장", entity_type="concept")
        
        graph.add_entity(e1)
        graph.add_entity(e2)
        graph.add_entity(e3)
        
        r1 = Relation(
            source_entity_id="e1",
            target_entity_id="e2",
            relation_type=RelationType.INFLUENCES,
            label="영향",
            sign=-1,  # 금리 ↑ → 투자 ↓
            validation_score=0.9
        )
        r2 = Relation(
            source_entity_id="e2",
            target_entity_id="e3",
            relation_type=RelationType.CAUSES,
            label="촉진",
            sign=1,  # 투자 ↑ → 경제성장 ↑
            validation_score=0.85
        )
        
        graph.add_relation(r1)
        graph.add_relation(r2)
        
        return graph
    
    @pytest.mark.asyncio
    async def test_find_path(self, graph_with_chain):
        """경로 탐색 테스트"""
        reasoner = PathReasoner(graph_with_chain)
        result = await reasoner.reason("e1", "e3")
        
        assert result.success
        assert result.result_type == ReasoningResultType.PATH
        assert len(result.paths) > 0
        assert result.confidence > 0
    
    @pytest.mark.asyncio
    async def test_sign_propagation(self, graph_with_chain):
        """v5.2 sign 전파 테스트: -1 * 1 = -1"""
        reasoner = PathReasoner(graph_with_chain)
        result = await reasoner.reason("e1", "e3")
        
        assert result.success
        # 금리 ↑ → 투자 ↓ → 경제성장 ↓ (sign = -1 * 1 = -1)
        assert result.sign == -1
    
    @pytest.mark.asyncio
    async def test_path_confidence(self, graph_with_chain):
        """v5.2 경로 confidence 테스트"""
        reasoner = PathReasoner(graph_with_chain)
        result = await reasoner.reason("e1", "e3")
        
        # path_conf = 0.9 * 0.85 * 0.92^(3-1) = 0.765 * 0.8464 ≈ 0.647
        assert result.success
        assert 0.5 < result.confidence < 0.8
    
    @pytest.mark.asyncio
    async def test_no_path(self, graph_with_chain):
        """경로 없음 테스트"""
        reasoner = PathReasoner(graph_with_chain)
        result = await reasoner.reason("e3", "e1")  # 역방향 없음
        
        assert not result.success
        assert result.confidence == 0


class TestMechanismReasoner:
    """MechanismReasoner 테스트"""
    
    @pytest.fixture
    def causal_graph(self):
        """인과 그래프"""
        graph = OntologyGraph()
        
        e1 = Entity(id="e1", canonical_name="인플레이션", entity_type="concept")
        e2 = Entity(id="e2", canonical_name="중앙은행금리", entity_type="concept")
        e3 = Entity(id="e3", canonical_name="소비", entity_type="concept")
        
        graph.add_entity(e1)
        graph.add_entity(e2)
        graph.add_entity(e3)
        
        r1 = Relation(
            source_entity_id="e1",
            target_entity_id="e2",
            relation_type=RelationType.CAUSES,
            label="인상 유발",
            sign=1,  # 인플레이션 ↑ → 금리 인상
            validation_score=0.88
        )
        r2 = Relation(
            source_entity_id="e2",
            target_entity_id="e3",
            relation_type=RelationType.INVERSE,
            label="억제",
            sign=-1,  # 금리 ↑ → 소비 ↓
            validation_score=0.82
        )
        
        graph.add_relation(r1)
        graph.add_relation(r2)
        
        return graph
    
    @pytest.mark.asyncio
    async def test_mechanism_chain(self, causal_graph):
        """메커니즘 체인 테스트"""
        reasoner = MechanismReasoner(causal_graph)
        result = await reasoner.reason("e1", "e3")
        
        assert result.success
        assert result.result_type == ReasoningResultType.MECHANISM
    
    @pytest.mark.asyncio
    async def test_sign_calculation(self, causal_graph):
        """v5.2 sign 계산: 1 * -1 = -1"""
        reasoner = MechanismReasoner(causal_graph)
        result = await reasoner.reason("e1", "e3")
        
        # 인플레이션 ↑ → 금리 ↑ → 소비 ↓ (sign = 1 * -1 = -1)
        assert result.sign == -1
    
    @pytest.mark.asyncio
    async def test_confidence_multiplication(self, causal_graph):
        """v5.2 confidence 곱셈: 0.88 * 0.82"""
        reasoner = MechanismReasoner(causal_graph)
        result = await reasoner.reason("e1", "e3")
        
        # conf = 0.88 * 0.82 ≈ 0.72
        assert 0.6 < result.confidence < 0.8


class TestScenarioSimulator:
    """ScenarioSimulator 테스트"""
    
    @pytest.fixture
    def impact_graph(self):
        """영향도 그래프"""
        graph = OntologyGraph()
        
        entities = [
            Entity(id="root", canonical_name="금리", entity_type="policy"),
            Entity(id="inv", canonical_name="투자", entity_type="activity"),
            Entity(id="cons", canonical_name="소비", entity_type="activity"),
            Entity(id="gdp", canonical_name="GDP", entity_type="indicator"),
        ]
        
        for e in entities:
            graph.add_entity(e)
        
        relations = [
            Relation(
                source_entity_id="root", target_entity_id="inv",
                relation_type=RelationType.INVERSE, label="억제",
                sign=-1, validation_score=0.9
            ),
            Relation(
                source_entity_id="root", target_entity_id="cons",
                relation_type=RelationType.INVERSE, label="억제",
                sign=-1, validation_score=0.85
            ),
            Relation(
                source_entity_id="inv", target_entity_id="gdp",
                relation_type=RelationType.PROPORTIONAL, label="촉진",
                sign=1, validation_score=0.88
            ),
            Relation(
                source_entity_id="cons", target_entity_id="gdp",
                relation_type=RelationType.PROPORTIONAL, label="촉진",
                sign=1, validation_score=0.82
            ),
        ]
        
        for r in relations:
            graph.add_relation(r)
        
        return graph
    
    @pytest.mark.asyncio
    async def test_scenario_simulation(self, impact_graph):
        """시나리오 시뮬레이션 테스트"""
        simulator = ScenarioSimulator(impact_graph)
        
        scenario = ScenarioInput(
            root_entity_id="root",
            initial_magnitude=1.0,
            initial_sign=1  # 금리 인상
        )
        
        result = await simulator.reason(scenario)
        
        assert result.success
        assert result.result_type == ReasoningResultType.SCENARIO
    
    @pytest.mark.asyncio
    async def test_propagation_effects(self, impact_graph):
        """v5.2 영향도 전파 테스트"""
        simulator = ScenarioSimulator(impact_graph)
        
        scenario = ScenarioInput(
            root_entity_id="root",
            initial_magnitude=1.0,
            initial_sign=1
        )
        
        result = await simulator.reason(scenario)
        
        effects = result.details.get("effects", {})
        
        # 투자와 소비는 감소해야 함 (금리 ↑ → 투자 ↓, 소비 ↓)
        inv_effect = effects.get("inv", {})
        cons_effect = effects.get("cons", {})
        
        assert inv_effect.get("sign") == -1
        assert cons_effect.get("sign") == -1
    
    @pytest.mark.asyncio
    async def test_what_if_simulation(self, impact_graph):
        """What-if 시뮬레이션 테스트"""
        simulator = ScenarioSimulator(impact_graph)
        
        result = await simulator.simulate_what_if("금리", "increase")
        
        assert "effects" in result
        assert len(result["effects"]) > 0
