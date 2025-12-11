"""
로컬 학습 스크립트
train_local.cmd에서 호출됨
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def run_training():
    from config.settings import get_settings
    from src.services.ontology_service import OntologyService
    from src.services.llm_service import LLMService
    from src.services.data_loader import DataLoader
    from src.validators.relation_validator import RelationValidator
    from src.storage.graph_store import GraphStore
    from src.storage.vector_store import VectorStore

    settings = get_settings()
    
    print('[1/5] 서비스 초기화 중...')
    
    # 1. LLM Service 먼저 초기화
    llm_service = LLMService()
    llm_available = await llm_service.health_check()
    if llm_available:
        print('      ✓ LLMService 연결 완료 (Ollama)')
    else:
        print('      ✗ LLMService 연결 실패 - Ollama 실행을 확인하세요')
        return False
    
    # 2. GraphStore 초기화 (SQLite 영속화)
    print()
    print('[2/5] GraphStore 초기화 중...')
    graph_store = GraphStore(db_url=settings.database_url)
    await graph_store.initialize()
    print(f'      ✓ GraphStore 준비 완료 ({settings.database_url})')
    
    # 3. VectorStore 초기화 (ChromaDB 영속화)
    print()
    print('[3/5] VectorStore 초기화 중...')
    vector_store = VectorStore(persist_dir=settings.chroma_persist_dir)
    await vector_store.initialize()
    print(f'      ✓ VectorStore 준비 완료 ({settings.chroma_persist_dir})')
    
    # 4. OntologyService 초기화 (저장소 연결)
    print()
    print('[4/5] OntologyService 초기화 중...')
    relation_validator = RelationValidator(llm_service=llm_service)
    ontology_service = OntologyService(
        validator=relation_validator,
        llm_service=llm_service,
        graph_store=graph_store,
        vector_store=vector_store
    )
    await ontology_service.initialize()
    print('      ✓ OntologyService 초기화 완료')
    
    # 5. DataLoader로 학습
    print()
    print('[5/5] 데이터 학습 시작...')
    print('      (domain/ -> user/ 순서로 학습)')
    print()
    
    data_loader = DataLoader(ontology_service, llm_service)
    await data_loader.load_initial_data()
    
    # 최종 통계
    print()
    print('============================================')
    print('  온톨로지 통계')
    print('============================================')
    stats = ontology_service.get_statistics()
    print(f'      - Entity: {stats.get("entity_count", 0)}개')
    print(f'      - Relation: {stats.get("relation_count", 0)}개')
    print(f'      - Vector: {stats.get("vector_count", 0)}개')
    
    # 저장소 닫기
    await ontology_service.close()
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(run_training())
        if result:
            print()
            print('============================================')
            print('  ✅ 학습 완료!')
            print('============================================')
        else:
            print()
            print('============================================')
            print('  ❌ 학습 실패 - 위 오류를 확인하세요')
            print('============================================')
            sys.exit(1)
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
