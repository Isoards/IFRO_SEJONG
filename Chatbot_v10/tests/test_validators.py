"""
Validator 테스트
단위/통합 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.validators.entity_validator import EntityValidator
from src.validators.relation_validator import RelationValidator
from src.validators.fragment_validator import FragmentValidator
from src.validators.base import ValidationResult
from src.domain.entities import Entity
from src.domain.fragments import Fragment
from src.domain.relations import Relation, OntologyGraph
from config.constants import (
    FragmentType, ValidationStatus, RelationType, FeasibilityLevel
)


class TestEntityValidator:
    """EntityValidator 테스트"""
    
    @pytest.fixture
    def validator(self):
        """LLM 없는 EntityValidator"""
        return EntityValidator()
    
    @pytest.fixture
    def validator_with_llm(self):
        """Mock LLM이 있는 EntityValidator"""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value='{"score": 0.85, "is_valid": true, "issues": [], "reasoning": "valid"}')
        return EntityValidator(llm_service=mock_llm)
    
    @pytest.mark.asyncio
    async def test_validate_valid_entity(self, validator, sample_entity):
        """유효한 엔티티 검증"""
        result = await validator.validate_entity(sample_entity, use_llm=False)
        
        assert isinstance(result, ValidationResult)
        assert result.score >= 0.5
        # Rule 점수가 높아야 함
        assert result.details.get("rule_score", 0) >= 0.7
    
    @pytest.mark.asyncio
    async def test_validate_short_name_entity(self, validator):
        """짧은 이름 엔티티 검증 - 낮은 점수"""
        entity = Entity(
            canonical_name="A",
            entity_type="concept"
        )
        
        result = await validator.validate_entity(entity, use_llm=False)
        
        assert result.details.get("rule_score", 1.0) < 1.0
        assert any("짧" in r for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_validate_digit_only_entity(self, validator):
        """숫자로만 된 엔티티 검증 - 낮은 점수"""
        entity = Entity(
            canonical_name="12345",
            entity_type="number"
        )
        
        result = await validator.validate_entity(entity, use_llm=False)
        
        assert result.details.get("rule_score", 1.0) < 0.8
        assert any("숫자" in r for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_validate_with_llm(self, validator_with_llm, sample_entity):
        """LLM 검증 통합 테스트"""
        result = await validator_with_llm.validate_entity(sample_entity, use_llm=True)
        
        assert isinstance(result, ValidationResult)
        # v4.2: layer_scores에서 llm 점수 확인 또는 최종 점수 확인
        llm_score = result.layer_scores.get("llm", 0) if hasattr(result, 'layer_scores') else result.details.get("llm_score", 0)
        assert result.score >= 0.5 or llm_score >= 0.5
    
    def test_calculate_similarity(self, validator, sample_entity, sample_entity_2):
        """엔티티 유사도 계산"""
        similarity = validator.calculate_similarity(sample_entity, sample_entity)
        assert similarity >= 0.9  # 동일 엔티티
        
        similarity = validator.calculate_similarity(sample_entity, sample_entity_2)
        assert similarity < 0.9  # 다른 엔티티
    
    @pytest.mark.asyncio
    async def test_feedback_recording(self, validator, sample_entity):
        """피드백 기록 테스트"""
        await validator.record_feedback(sample_entity.id, approved=True)
        
        stats = validator.get_policy_stats()
        assert stats["total_feedbacks"] == 1
        assert stats["avg_reward"] == 1.0


class TestRelationValidator:
    """RelationValidator 테스트"""
    
    @pytest.fixture
    def validator(self):
        return RelationValidator()
    
    @pytest.fixture
    def graph_with_entities(self, sample_entity, sample_entity_2):
        """엔티티가 포함된 그래프"""
        graph = OntologyGraph()
        graph.add_entity(sample_entity)
        graph.add_entity(sample_entity_2)
        return graph
    
    @pytest.mark.asyncio
    async def test_validate_valid_relation(
        self, validator, sample_relation, graph_with_entities
    ):
        """유효한 관계 검증"""
        result = await validator.validate_relation(
            sample_relation, graph_with_entities, use_llm=False
        )
        
        assert isinstance(result, ValidationResult)
        assert result.score >= 0.5
    
    @pytest.mark.asyncio
    async def test_validate_self_reference(self, validator, sample_entity):
        """자기 참조 관계 검증 - 낮은 점수"""
        graph = OntologyGraph()
        graph.add_entity(sample_entity)
        
        relation = Relation(
            source_entity_id=sample_entity.id,
            target_entity_id=sample_entity.id,  # 자기 참조
            relation_type=RelationType.IS_A,
            label="자기참조"
        )
        
        result = await validator.validate_relation(relation, graph, use_llm=False)
        
        # v4.2: is_valid와 score로 검증 (layer=rule에서 reject)
        assert not result.is_valid or result.score < 0.6
        assert any("자기 참조" in r or "Self-loop" in r for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_validate_missing_entity(self, validator):
        """존재하지 않는 엔티티 관계 검증"""
        graph = OntologyGraph()
        
        relation = Relation(
            source_entity_id="non-existent-1",
            target_entity_id="non-existent-2",
            relation_type=RelationType.IS_A,
            label="관계"
        )
        
        result = await validator.validate_relation(relation, graph, use_llm=False)
        
        # v4.2: 엔티티 없으면 즉시 reject
        assert not result.is_valid
        assert result.score < 0.5
        assert any("엔티티 없음" in r or "missing" in r.lower() for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(
        self, validator, sample_relation, graph_with_entities
    ):
        """중복 관계 감지"""
        # 먼저 관계 추가
        graph_with_entities.add_relation(sample_relation)
        
        # 동일한 관계 생성
        duplicate = Relation(
            source_entity_id=sample_relation.source_entity_id,
            target_entity_id=sample_relation.target_entity_id,
            relation_type=sample_relation.relation_type,
            label="동일관계"
        )
        
        result = await validator.validate_relation(
            duplicate, graph_with_entities, use_llm=False
        )
        
        assert any("중복" in r for r in result.reasons)


class TestFragmentValidator:
    """FragmentValidator 테스트"""
    
    @pytest.fixture
    def validator(self):
        return FragmentValidator()
    
    @pytest.mark.asyncio
    async def test_validate_valid_fragment(self, validator, sample_fragment):
        """유효한 Fragment 검증"""
        result = await validator.validate_fragment(sample_fragment, use_llm=False)
        
        assert isinstance(result, ValidationResult)
        assert result.score >= 0.6
        assert result.is_valid
    
    @pytest.mark.asyncio
    async def test_validate_missing_fields(self, validator):
        """필수 필드 누락 Fragment 검증"""
        fragment = Fragment(
            fragment_type=FragmentType.MECHANISM,
            subject="",  # 빈 subject
            predicate="influences",
            object="인플레이션",
            direction=None,  # MECHANISM에 필요한 direction 누락
            source_document_id="doc-001",
            source_block_id="block-001",
            evidence="근거",
            confidence=0.5
        )
        
        result = await validator.validate_fragment(fragment, use_llm=False)
        
        assert result.details.get("rule_score", 1.0) < 0.8
        assert len(result.reasons) > 0
    
    @pytest.mark.asyncio
    async def test_validate_same_subject_object(self, validator):
        """Subject와 Object가 동일한 Fragment"""
        fragment = Fragment(
            fragment_type=FragmentType.FACT,
            subject="금리",
            predicate="equals",
            object="금리",  # 동일
            source_document_id="doc-001",
            source_block_id="block-001",
            evidence="금리는 금리이다",
            confidence=0.5
        )
        
        result = await validator.validate_fragment(fragment, use_llm=False)
        
        assert any("동일" in r for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_validate_low_confidence(self, validator):
        """낮은 신뢰도 Fragment"""
        fragment = Fragment(
            fragment_type=FragmentType.FACT,
            subject="금리",
            predicate="affects",
            object="경제",
            source_document_id="doc-001",
            source_block_id="block-001",
            evidence="금리가 경제에 영향을 미친다",
            confidence=0.2  # 매우 낮음
        )
        
        result = await validator.validate_fragment(fragment, use_llm=False)
        
        assert any("신뢰도" in r for r in result.reasons)
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, validator, sample_fragment):
        """배치 검증"""
        fragments = [sample_fragment] * 3
        
        results = await validator.validate_batch(fragments, use_llm=False)
        
        assert len(results) == 3
        assert all(isinstance(r, ValidationResult) for r in results)


class TestValidatorPolicyPersistence:
    """Validator 정책 영속화 테스트"""
    
    @pytest.mark.asyncio
    async def test_policy_save_and_load(self, temp_policy_path):
        """정책 저장 및 로드"""
        from src.storage.policy_store import PolicyStore
        
        # 정책 저장소 초기화
        policy_store = PolicyStore(storage_path=temp_policy_path)
        await policy_store.initialize()
        
        # Validator 생성 및 피드백 기록
        validator = EntityValidator(policy_store=policy_store)
        
        # 피드백 기록
        for i in range(15):
            await validator.record_feedback(f"entity-{i}", approved=(i % 2 == 0))
        
        # 정책 저장
        await validator.save_policy()
        
        # 새 Validator로 정책 로드
        new_validator = EntityValidator(policy_store=policy_store)
        loaded = await new_validator.load_policy()
        
        assert loaded
        assert new_validator._policy_loaded
        assert len(new_validator._reward_history) > 0
        
        await policy_store.close()
