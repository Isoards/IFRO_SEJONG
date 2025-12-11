"""
Ontology Platform 사용 예제 (비동기식)

async/await를 사용하는 비동기 예제입니다.

실행:
    python examples/async_usage.py
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.sdk import OntologyPlatform


async def main():
    print("=" * 60)
    print("🧠 Ontology Platform - Async Example")
    print("=" * 60)
    
    # 플랫폼 초기화
    print("\n[1] 플랫폼 초기화...")
    platform = OntologyPlatform()
    
    # 상태 확인
    status = await platform.health_check()
    print(f"    Ollama: {'✅' if status['ollama_connected'] else '❌'}")
    
    # 텍스트 학습
    print("\n[2] 지식 학습...")
    
    texts = [
        """
        머신러닝은 인공지능의 한 분야이다.
        딥러닝은 머신러닝의 하위 분야로, 신경망을 기반으로 한다.
        """,
        """
        트랜스포머는 딥러닝 아키텍처 중 하나이다.
        GPT와 BERT는 트랜스포머 기반 모델이다.
        """,
        """
        LLM(대규모 언어 모델)은 트랜스포머 아키텍처를 기반으로 한다.
        ChatGPT는 GPT 기반의 대화형 AI이다.
        """
    ]
    
    for i, text in enumerate(texts, 1):
        result = await platform.learn_text(text, f"AI_지식_{i}")
        print(f"    텍스트 {i}: Fragment {result['fragment_count']}개, Entity {result['entity_count']}개")
    
    # 엔티티 확인
    print("\n[3] 학습된 엔티티:")
    for entity in platform.get_entities()[:10]:
        print(f"    - {entity.canonical_name}")
    
    # 스트리밍 질의
    print("\n[4] 스트리밍 RAG 질의:")
    question = "딥러닝과 트랜스포머의 관계를 설명해줘."
    print(f"    Q: {question}")
    print(f"    A: ", end="")
    
    async for chunk in platform.query_stream(question):
        print(chunk, end="", flush=True)
    
    print("\n")
    
    # 상세 질의 (추적 정보 포함)
    print("\n[5] 상세 질의 (추적 정보 포함):")
    question2 = "GPT는 어떤 기술을 기반으로 하나요?"
    
    result = await platform.query(question2, include_trace=True)
    
    print(f"    Q: {question2}")
    print(f"    A: {result['response'][:200]}...")
    print(f"    Intent: {result['intent']}")
    print(f"    관련 엔티티: {result['entities']}")
    
    # 통계
    print("\n[6] 최종 통계:")
    stats = platform.get_stats()
    print(f"    Entity: {stats['entity_count']}개")
    print(f"    Relation: {stats['relation_count']}개")
    
    print("\n" + "=" * 60)
    print("✅ 완료!")


if __name__ == "__main__":
    asyncio.run(main())
