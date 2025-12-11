"""
Storage Layer 테스트
단위/통합 테스트
"""
import pytest
import json
from pathlib import Path

from src.storage.base import JSONFileStore, StoreError
from src.storage.graph_store import GraphStore
from src.storage.document_store import DocumentStore
from src.storage.policy_store import PolicyStore, PolicyData
from src.domain.entities import Entity
from src.domain.fragments import Fragment, StructuredDoc, Block
from src.domain.relations import Relation, OntologyGraph
from config.constants import FragmentType, ValidationStatus, RelationType


class TestJSONFileStore:
    """JSONFileStore 테스트"""
    
    @pytest.mark.asyncio
    async def test_initialize_empty(self, tmp_path):
        """빈 저장소 초기화"""
        file_path = tmp_path / "test_store.json"
        store = JSONFileStore("test", file_path)
        
        await store.initialize()
        
        assert store._initialized
        assert file_path.parent.exists()
    
    @pytest.mark.asyncio
    async def test_save_and_get(self, tmp_path):
        """저장 및 조회"""
        file_path = tmp_path / "test_store.json"
        store = JSONFileStore("test", file_path)
        await store.initialize()
        
        item = {"id": "test-1", "name": "테스트", "value": 123}
        item_id = await store.save(item)
        
        assert item_id == "test-1"
        
        loaded = await store.get(item_id)
        assert loaded["name"] == "테스트"
        assert loaded["value"] == 123
    
    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        """삭제 테스트"""
        file_path = tmp_path / "test_store.json"
        store = JSONFileStore("test", file_path)
        await store.initialize()
        
        item = {"id": "test-1", "name": "삭제 테스트"}
        await store.save(item)
        
        deleted = await store.delete("test-1")
        assert deleted
        
        loaded = await store.get("test-1")
        assert loaded is None
    
    @pytest.mark.asyncio
    async def test_list_all(self, tmp_path):
        """목록 조회"""
        file_path = tmp_path / "test_store.json"
        store = JSONFileStore("test", file_path)
        await store.initialize()
        
        for i in range(5):
            await store.save({"id": f"item-{i}", "index": i})
        
        items = await store.list_all(limit=3)
        assert len(items) == 3
    
    @pytest.mark.asyncio
    async def test_persistence(self, tmp_path):
        """영속화 테스트"""
        file_path = tmp_path / "test_store.json"
        
        # 첫 번째 인스턴스
        store1 = JSONFileStore("test", file_path)
        await store1.initialize()
        await store1.save({"id": "persist-1", "data": "영속화 테스트"})
        await store1.close()
        
        # 두 번째 인스턴스 (새로 로드)
        store2 = JSONFileStore("test", file_path)
        await store2.initialize()
        
        loaded = await store2.get("persist-1")
        assert loaded is not None
        assert loaded["data"] == "영속화 테스트"


class TestGraphStore:
    """GraphStore 테스트"""
    
    @pytest.mark.asyncio
    async def test_initialize(self, tmp_path):
        """그래프 저장소 초기화"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = GraphStore(db_url=db_url)
        
        await store.initialize()
        
        assert store._initialized
        await store.close()
    
    @pytest.mark.asyncio
    async def test_save_and_load_entity(self, tmp_path, sample_entity):
        """엔티티 저장 및 로드"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = GraphStore(db_url=db_url)
        await store.initialize()
        
        # 저장
        entity_id = await store.save_entity(sample_entity)
        assert entity_id == sample_entity.id
        
        # 로드
        loaded = await store.get_entity(sample_entity.id)
        assert loaded is not None
        assert loaded.canonical_name == sample_entity.canonical_name
        assert loaded.entity_type == sample_entity.entity_type
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_save_and_load_graph(self, tmp_path, sample_entity, sample_entity_2, sample_relation):
        """전체 그래프 저장 및 로드"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = GraphStore(db_url=db_url)
        await store.initialize()
        
        # 그래프 생성
        graph = OntologyGraph()
        graph.add_entity(sample_entity)
        graph.add_entity(sample_entity_2)
        graph.add_relation(sample_relation)
        
        # 저장
        await store.save(graph)
        
        # 로드
        loaded_graph = await store.load_graph()
        
        assert len(loaded_graph.entities) == 2
        assert len(loaded_graph.relations) == 1
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_get_relations_for_entity(self, tmp_path, sample_entity, sample_entity_2, sample_relation):
        """엔티티별 관계 조회"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = GraphStore(db_url=db_url)
        await store.initialize()
        
        await store.save_entity(sample_entity)
        await store.save_entity(sample_entity_2)
        await store.save_relation(sample_relation)
        
        relations = await store.get_relations_for_entity(sample_entity.id)
        assert len(relations) >= 1
        
        await store.close()


class TestDocumentStore:
    """DocumentStore 테스트"""
    
    @pytest.fixture
    def sample_doc(self):
        """테스트용 문서"""
        return StructuredDoc(
            source_path="/test/doc.pdf",
            source_type="pdf",
            title="테스트 문서",
            blocks=[
                Block(block_type="paragraph", content="첫 번째 단락", order=1),
                Block(block_type="paragraph", content="두 번째 단락", order=2),
            ],
            metadata={"author": "테스트"}
        )
    
    @pytest.mark.asyncio
    async def test_save_and_load_document(self, tmp_path, sample_doc):
        """문서 저장 및 로드"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = DocumentStore(db_url=db_url)
        await store.initialize()
        
        # 저장
        doc_id = await store.save(sample_doc)
        assert doc_id == sample_doc.id
        
        # 로드
        loaded = await store.get(sample_doc.id)
        assert loaded is not None
        assert loaded.title == sample_doc.title
        assert len(loaded.blocks) == 2
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_save_and_load_fragment(self, tmp_path, sample_fragment):
        """Fragment 저장 및 로드"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = DocumentStore(db_url=db_url)
        await store.initialize()
        
        # 저장
        frag_id = await store.save_fragment(sample_fragment)
        assert frag_id == sample_fragment.id
        
        # 로드
        loaded = await store.get_fragment(sample_fragment.id)
        assert loaded is not None
        assert loaded.subject == sample_fragment.subject
        assert loaded.fragment_type == sample_fragment.fragment_type
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_update_fragment_status(self, tmp_path, sample_fragment):
        """Fragment 상태 업데이트"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = DocumentStore(db_url=db_url)
        await store.initialize()
        
        await store.save_fragment(sample_fragment)
        
        # 상태 업데이트
        updated = await store.update_fragment_status(
            sample_fragment.id,
            ValidationStatus.APPROVED,
            0.85,
            ["검증 완료"]
        )
        assert updated
        
        # 확인
        loaded = await store.get_fragment(sample_fragment.id)
        assert loaded.validation_status == ValidationStatus.APPROVED
        assert loaded.validation_score == 0.85
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_get_fragments_by_document(self, tmp_path):
        """문서별 Fragment 조회"""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        store = DocumentStore(db_url=db_url)
        await store.initialize()
        
        doc_id = "test-doc-001"
        
        # 여러 Fragment 저장
        for i in range(3):
            fragment = Fragment(
                fragment_type=FragmentType.FACT,
                subject=f"Subject-{i}",
                predicate="is",
                object=f"Object-{i}",
                source_document_id=doc_id,
                source_block_id=f"block-{i}",
                evidence=f"Evidence {i}",
                confidence=0.8
            )
            await store.save_fragment(fragment)
        
        # 조회
        fragments = await store.get_fragments_by_document(doc_id)
        assert len(fragments) == 3
        
        await store.close()


class TestPolicyStore:
    """PolicyStore 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_and_load_policy(self, tmp_path):
        """정책 저장 및 로드"""
        store = PolicyStore(storage_path=tmp_path)
        await store.initialize()
        
        # 정책 데이터 생성
        policy = PolicyData(
            validator_name="TestValidator",
            policy_weights={"rule_weight": 0.5, "llm_weight": 0.3, "history_weight": 0.2},
            reward_history=[0.5, 0.8, -0.3, 1.0],
            feedback_count=10,
            avg_reward=0.5,
            approval_rate=0.7
        )
        
        # 저장
        await store.save(policy)
        
        # 로드
        loaded = await store.get("TestValidator")
        assert loaded is not None
        assert loaded.validator_name == "TestValidator"
        assert loaded.policy_weights["rule_weight"] == 0.5
        assert len(loaded.reward_history) == 4
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_save_validator_policy(self, tmp_path):
        """Validator 정책 저장 편의 메서드"""
        store = PolicyStore(storage_path=tmp_path)
        await store.initialize()
        
        await store.save_validator_policy(
            validator_name="EntityValidator",
            policy_weights={"rule_weight": 0.4, "llm_weight": 0.3, "history_weight": 0.3},
            reward_history=[1.0, 1.0, -1.0, 1.0],
            feedback_history=[
                {"item_id": "1", "approved": True},
                {"item_id": "2", "approved": True},
                {"item_id": "3", "approved": False},
            ]
        )
        
        loaded = await store.load_validator_policy("EntityValidator")
        assert loaded is not None
        assert loaded["feedback_count"] == 3
        assert loaded["approval_rate"] == pytest.approx(2/3, rel=0.01)
        
        await store.close()
    
    @pytest.mark.asyncio
    async def test_get_all_policy_stats(self, tmp_path):
        """모든 정책 통계 조회"""
        store = PolicyStore(storage_path=tmp_path)
        await store.initialize()
        
        # 여러 정책 저장
        for i, name in enumerate(["EntityValidator", "RelationValidator", "FragmentValidator"]):
            policy = PolicyData(
                validator_name=name,
                policy_weights={"rule_weight": 0.4, "llm_weight": 0.3, "history_weight": 0.3},
                reward_history=[0.5] * (i + 1),
                feedback_count=i + 1,
                avg_reward=0.5,
                approval_rate=0.7
            )
            await store.save(policy)
        
        stats = await store.get_all_policy_stats()
        assert len(stats) == 3
        assert "EntityValidator" in stats
        
        await store.close()
