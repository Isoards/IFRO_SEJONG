"""
Pytest Configuration
"""
import pytest
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """세션 범위 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_entity():
    """테스트용 Entity"""
    from src.domain.entities import Entity
    return Entity(
        canonical_name="금리",
        entity_type="concept",
        description="중앙은행이 설정하는 기준 금리",
        aliases=["기준금리", "정책금리"],
        domain_tags=["경제", "금융"]
    )


@pytest.fixture
def sample_entity_2():
    """테스트용 Entity 2"""
    from src.domain.entities import Entity
    return Entity(
        canonical_name="인플레이션",
        entity_type="concept",
        description="물가 상승률",
        aliases=["물가상승", "인플레"],
        domain_tags=["경제"]
    )


@pytest.fixture
def sample_fragment():
    """테스트용 Fragment"""
    from src.domain.fragments import Fragment
    from config.constants import FragmentType, ValidationStatus
    
    return Fragment(
        fragment_type=FragmentType.MECHANISM,
        subject="금리",
        predicate="influences",
        object="인플레이션",
        direction="inverse",
        magnitude="high",
        source_document_id="doc-001",
        source_block_id="block-001",
        evidence="금리 인상은 인플레이션을 억제하는 효과가 있다.",
        confidence=0.85,
        validation_status=ValidationStatus.PENDING
    )


@pytest.fixture
def sample_relation(sample_entity, sample_entity_2):
    """테스트용 Relation"""
    from src.domain.relations import Relation
    from config.constants import RelationType, ValidationStatus
    
    return Relation(
        source_entity_id=sample_entity.id,
        target_entity_id=sample_entity_2.id,
        relation_type=RelationType.INVERSE,
        label="억제",
        direction="inverse",
        magnitude="high",
        source_fragment_ids=["frag-001"],
        validation_status=ValidationStatus.PENDING
    )


@pytest.fixture
def temp_db_path(tmp_path):
    """임시 데이터베이스 경로"""
    return tmp_path / "test.db"


@pytest.fixture
def temp_vector_path(tmp_path):
    """임시 벡터 DB 경로"""
    return tmp_path / "chroma_test"


@pytest.fixture
def temp_policy_path(tmp_path):
    """임시 정책 저장 경로"""
    return tmp_path / "policies"
