"""
대화형 CLI 인터페이스

터미널에서 대화형으로 질의할 수 있습니다.

실행:
    python examples/interactive_cli.py
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.sdk import OntologyPlatformSync


def print_help():
    """도움말 출력"""
    print("""
사용 가능한 명령어:
    /learn <텍스트>     - 텍스트 학습
    /file <파일경로>    - 파일 학습
    /entities           - 엔티티 목록
    /relations          - 관계 목록
    /stats              - 통계
    /help               - 도움말
    /quit 또는 /exit    - 종료
    
    그 외 입력          - RAG 질의
""")


def main():
    print("=" * 60)
    print("🧠 Ontology Platform - Interactive CLI")
    print("=" * 60)
    print("'/help'를 입력하면 사용 가능한 명령어를 볼 수 있습니다.")
    print("질문을 입력하면 RAG 기반 답변을 생성합니다.")
    print("=" * 60)
    
    # 플랫폼 초기화
    print("\n플랫폼 초기화 중...")
    platform = OntologyPlatformSync()
    
    status = platform.health_check()
    if status['ollama_connected']:
        print(f"✅ Ollama 연결됨 (모델: {status['ollama_model']})")
    else:
        print("⚠️ Ollama에 연결할 수 없습니다. LLM 기능이 제한됩니다.")
    
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # 명령어 처리
            if user_input.startswith("/"):
                parts = user_input.split(" ", 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command in ("/quit", "/exit"):
                    print("👋 종료합니다.")
                    break
                
                elif command == "/help":
                    print_help()
                
                elif command == "/learn":
                    if not args:
                        print("❌ 학습할 텍스트를 입력하세요. 예: /learn 금리가 오르면 주식이 떨어진다.")
                        continue
                    
                    print("📚 학습 중...")
                    result = platform.learn_text(args)
                    
                    if result.get("success"):
                        print(f"✅ 학습 완료! Fragment: {result['fragment_count']}개, Entity: {result['entity_count']}개")
                    else:
                        print(f"❌ 학습 실패: {result.get('error')}")
                
                elif command == "/file":
                    if not args:
                        print("❌ 파일 경로를 입력하세요. 예: /file ./document.pdf")
                        continue
                    
                    print(f"📄 파일 학습 중: {args}")
                    result = platform.learn_file(args)
                    
                    if result.get("success"):
                        print(f"✅ 학습 완료! Fragment: {result['fragment_count']}개, Entity: {result['entity_count']}개")
                    else:
                        print(f"❌ 학습 실패: {result.get('error')}")
                
                elif command == "/entities":
                    entities = platform.get_entities()
                    if entities:
                        print(f"📋 엔티티 목록 ({len(entities)}개):")
                        for e in entities[:20]:
                            print(f"   - {e.canonical_name}")
                        if len(entities) > 20:
                            print(f"   ... 외 {len(entities) - 20}개")
                    else:
                        print("📋 등록된 엔티티가 없습니다.")
                
                elif command == "/relations":
                    relations = platform.get_relations()
                    if relations:
                        print(f"🔗 관계 목록 ({len(relations)}개):")
                        for r in relations[:20]:
                            print(f"   - {r.label} ({r.relation_type.value})")
                        if len(relations) > 20:
                            print(f"   ... 외 {len(relations) - 20}개")
                    else:
                        print("🔗 등록된 관계가 없습니다.")
                
                elif command == "/stats":
                    stats = platform.get_stats()
                    print(f"📊 통계:")
                    print(f"   Entity: {stats['entity_count']}개")
                    print(f"   Relation: {stats['relation_count']}개")
                
                else:
                    print(f"❌ 알 수 없는 명령어: {command}")
                    print("'/help'를 입력하면 사용 가능한 명령어를 볼 수 있습니다.")
            
            else:
                # RAG 질의
                print("🤔 생각 중...")
                response = platform.query(user_input)
                print(f"\nAI: {response}\n")
        
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    platform.close()


if __name__ == "__main__":
    main()
