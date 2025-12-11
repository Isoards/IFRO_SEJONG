"""
통합 테스트
전체 시스템 플로우 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.ontology_service import OntologyService
from src.validators.relation_validator import RelationValidator
from src.validators.fragment_validator import FragmentValidator
from src.storage.graph_store import GraphStore
from src.storage.document_store import DocumentStore
from src.storage.policy_store import PolicyStore
from src.domain.entities import Entity
from src.domain.fragments import Fragment
from src.domain.relations import Relation, OntologyGraph
from config.constants import (
    FragmentType, ValidationStatus, RelationType
)


class TestOntologyServiceIntegration:
    """OntologyService 통합 테스트"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM Service"""
        mock = AsyncMock()
        mock.embed = AsyncMock(return_value=[0.1] * 384)  # 임베딩 벡터
        mock.generate = AsyncMock(return_value='{"score": 0.8, "is_valid": true, "issues": []}')
        return mock
    
    @pytest.fixture
    def ontology_service(self):
        """기본 OntologyService"""
        validator = RelationValidator()
        service = OntologyService(validator=validator)
        return service
    
    @pytest.mark.asyncio
    async def test_add_entity(self, ontology_service, sample_entity):
        """엔티티 추가"""
        result = await ontology_service.add_entity(sample_entity, persist=False)
        
        assert result.success
        assert result.value.id == sample_entity.id
        assert len(ontology_service.graph.entities) == 1
    
    @pytest.mark.asyncio
    async def test_add_multiple_entities(self, ontology_service, sample_entity, sample_entity_2):
        """다중 엔티티 추가"""
        await ontology_service.add_entity(sample_entity, persist=False)
        await ontology_service.add_entity(sample_entity_2, persist=False)
        
        assert len(ontology_service.graph.entities) == 2
    
    @pytest.mark.asyncio
    async def test_fallback_search(self, ontology_service, sample_entity, sample_entity_2):
        """폴백 검색 (벡터 저장소 없이)"""
        await ontology_service.add_entity(sample_entity, persist=False)
        await ontology_service.add_entity(sample_entity_2, persist=False)
        
        results = await ontology_service.search_entities_by_similarity("금리", top_k=5)
        
        assert len(results) > 0
        assert any(e.canonical_name == "금리" for e, _ in results)
    
    @pytest.mark.asyncio
    async def test_get_subgraph(self, ontology_service, sample_entity, sample_entity_2, sample_relation):
        """서브그래프 추출"""
        await ontology_service.add_entity(sample_entity, persist=False)
        await ontology_service.add_entity(sample_entity_2, persist=False)
        ontology_service.graph.add_relation(sample_relation)
        
        subgraph = ontology_service.get_subgraph([sample_entity.canonical_name], depth=1)
        
        assert len(subgraph.entities) >= 1
    
    @pytest.mark.asyncio
    async def test_rag_context_generation(self, ontology_service, sample_entity, sample_entity_2):
        """RAG 컨텍스트 생성"""
        await ontology_service.add_entity(sample_entity, persist=False)
        await ontology_service.add_entity(sample_entity_2, persist=False)
        
        context = await ontology_service.generate_rag_context("금리와 인플레이션의 관계")
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    @pytest.mark.asyncio
    async def test_statistics(self, ontology_service, sample_entity, sample_entity_2):
        """통계 조회"""
        await ontology_service.add_entity(sample_entity, persist=False)
        await ontology_service.add_entity(sample_entity_2, persist=False)
        
        stats = ontology_service.get_statistics()
        
        assert stats["entity_count"] == 2
        assert "entities" in stats


class TestStorageIntegration:
    """Storage 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_graph_persistence(self, tmp_path, sample_entity, sample_entity_2, sample_relation):
        """그래프 저장 및 로드"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        
        # 저장
        store = GraphStore(db_url=db_url)
        await store.initialize()
        
        await store.save_entity(sample_entity)
        await store.save_entity(sample_entity_2)
        await store.save_relation(sample_relation)
        
        await store.close()
        
        # 로드
        store2 = GraphStore(db_url=db_url)
        await store2.initialize()
        
        graph = await store2.load_graph()
        
        assert len(graph.entities) == 2
        assert len(graph.relations) == 1
        
        await store2.close()
    
    @pytest.mark.asyncio
    async def test_ontology_with_storage(self, tmp_path, sample_entity, sample_entity_2):
        """저장소와 OntologyService 통합"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        
        graph_store = GraphStore(db_url=db_url)
        await graph_store.initialize()
        
        validator = RelationValidator()
        service = OntologyService(
            validator=validator,
            graph_store=graph_store
        )
        await service.initialize()
        
        # 엔티티 추가 (영속화)
        await service.add_entity(sample_entity)
        await service.add_entity(sample_entity_2)
        
        # 저장 확인
        loaded = await graph_store.get_entity(sample_entity.id)
        assert loaded is not None
        assert loaded.canonical_name == sample_entity.canonical_name
        
        await service.close()


class TestValidatorFeedbackLoop:
    """Validator 피드백 루프 테스트"""
    
    @pytest.mark.asyncio
    async def test_feedback_loop(self, tmp_path):
        """피드백 루프 테스트"""
        policy_store = PolicyStore(storage_path=tmp_path / "policies")
        await policy_store.initialize()
        
        validator = RelationValidator(policy_store=policy_store)
        
        # 피드백 시뮬레이션 (충분한 수)
        for i in range(20):
            approved = i % 3 != 0  # 2/3 승인률
            await validator.record_feedback(
                item_id=f"relation-{i}",
                approved=approved,
                reason="테스트"
            )
        
        # 정책이 업데이트되었는지 확인
        stats = validator.get_policy_stats()
        assert stats["total_feedbacks"] == 20
        
        # 정책 저장
        await validator.save_policy()
        
        # 새 Validator로 정책 로드
        new_validator = RelationValidator(policy_store=policy_store)
        loaded = await new_validator.load_policy()
        
        assert loaded
        assert len(new_validator._reward_history) > 0
        
        await policy_store.close()


class TestFragmentToRelationPipeline:
    """Fragment -> Relation 파이프라인 테스트"""
    
    @pytest.mark.asyncio
    async def test_fragment_validation(self, sample_fragment):
        """Fragment 검증"""
        validator = FragmentValidator()
        
        result = await validator.validate_fragment(sample_fragment, use_llm=False)
        
        assert result.is_valid or result.score >= 0.5
    
    @pytest.mark.asyncio
    async def test_approved_fragment_to_relation(self, sample_entity, sample_entity_2):
        """승인된 Fragment에서 Relation 생성"""
        fragment = Fragment(
            fragment_type=FragmentType.MECHANISM,
            subject=sample_entity.canonical_name,
            predicate="억제",
            object=sample_entity_2.canonical_name,
            direction="inverse",
            source_document_id="doc-001",
            source_block_id="block-001",
            evidence="금리 인상은 인플레이션을 억제한다",
            confidence=0.9,
            validation_status=ValidationStatus.APPROVED
        )
        
        validator = RelationValidator()
        ontology = OntologyService(validator=validator)
        
        await ontology.add_entity(sample_entity, persist=False)
        await ontology.add_entity(sample_entity_2, persist=False)
        
        entities = {
            sample_entity.canonical_name.lower(): sample_entity,
            sample_entity_2.canonical_name.lower(): sample_entity_2,
        }
        
        result = await ontology.build_relations_from_fragments([fragment], entities)
        
        assert result.success
