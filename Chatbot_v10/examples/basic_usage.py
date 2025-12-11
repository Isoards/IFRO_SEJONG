"""
Ontology Platform 사용 예제 (동기식)

서버 없이 직접 라이브러리로 사용하는 예제입니다.

실행:
    python examples/basic_usage.py
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.sdk import OntologyPlatformSync


def main():
    print("=" * 60)
    print("🧠 Ontology-driven Reasoning & Action Platform")
    print("=" * 60)
    
    # 플랫폼 초기화
    print("\n[1] 플랫폼 초기화 중...")
    platform = OntologyPlatformSync()
    
    # 시스템 상태 확인
    status = platform.health_check()
    print(f"    Ollama 연결: {'✅' if status['ollama_connected'] else '❌'}")
    print(f"    모델: {status['ollama_model']}")
    
    # 텍스트 학습
    print("\n[2] 텍스트 학습 중...")
    
    sample_text = """
    금리가 인상되면 주식 시장은 하락하는 경향이 있다.
    이는 기업의 차입 비용이 증가하고, 투자자들이 안전 자산을 선호하기 때문이다.
    
    인플레이션이 상승하면 중앙은행은 금리를 인상하는 정책을 취한다.
    금리 인상은 소비를 억제하여 인플레이션을 낮추는 효과가 있다.
    
    채권 가격은 금리와 반비례 관계에 있다.
    금리가 오르면 기존 채권의 가치가 하락한다.
    """
    
    result = platform.learn_text(sample_text, "경제학_기초")
    
    if result.get("success"):
        print(f"    ✅ 학습 완료!")
        print(f"       - Fragment 추출: {result['fragment_count']}개")
        print(f"       - Entity 추출: {result['entity_count']}개")
        print(f"       - Relation 구축: {result['relation_count']}개")
    else:
        print(f"    ❌ 학습 실패: {result.get('error')}")
        return
    
    # 엔티티 확인
    print("\n[3] 추출된 엔티티:")
    entities = platform.get_entities()
    for entity in entities[:10]:
        print(f"    - {entity.canonical_name}")
        if entity.aliases:
            print(f"      별칭: {', '.join(entity.aliases)}")
    
    # 관계 확인
    print("\n[4] 구축된 관계:")
    relations = platform.get_relations()
    for relation in relations[:10]:
        source = platform.get_entity_by_id(relation.source_entity_id) if hasattr(platform, 'get_entity_by_id') else None
        target = platform.get_entity_by_id(relation.target_entity_id) if hasattr(platform, 'get_entity_by_id') else None
        print(f"    - {relation.label} ({relation.relation_type.value})")
    
    # RAG 질의
    print("\n[5] RAG 질의 테스트:")
    
    questions = [
        "금리 인상이 주식 시장에 미치는 영향은?",
        "인플레이션과 금리의 관계를 설명해줘.",
        "채권 투자 시 금리 변동에 대해 어떻게 대응해야 하나?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n    Q{i}: {question}")
        
        response = platform.query(question)
        print(f"    A{i}: {response[:300]}...")
    
    # 통계
    print("\n[6] 온톨로지 통계:")
    stats = platform.get_stats()
    print(f"    - 총 Entity: {stats['entity_count']}개")
    print(f"    - 총 Relation: {stats['relation_count']}개")
    
    # 정리
    platform.close()
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
