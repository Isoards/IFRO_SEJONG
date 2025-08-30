#!/usr/bin/env python3
"""
SBERT 모델 자동 다운로드 설정 스크립트

이 스크립트는 의도 분류기에 필요한 SBERT 모델을 미리 다운로드합니다.
"""

import os
import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """의존성 확인"""
    print("=" * 60)
    print("🔍 의존성 확인")
    print("=" * 60)
    
    required_packages = [
        "sentence_transformers",
        "torch",
        "transformers",
        "numpy",
        "sklearn"  # scikit-learn의 실제 import 이름
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (설치 필요)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 다음 패키지들을 설치해야 합니다:")
        for package in missing_packages:
            if package == "sklearn":
                print(f"pip install scikit-learn")
            else:
                print(f"pip install {package}")
        return False
    else:
        print(f"\n✅ 모든 의존성이 설치되어 있습니다.")
        return True

def setup_sbert_models():
    """SBERT 모델들을 미리 다운로드"""
    print("=" * 60)
    print("🤖 SBERT 모델 자동 다운로드 설정")
    print("=" * 60)
    
    try:
        # sentence-transformers 임포트
        from sentence_transformers import SentenceTransformer
        
        # 다운로드할 모델 목록 (우선순위 순서)
        models = [
            {
                "name": "한국어 특화 모델",
                "model_id": "jhgan/ko-sroberta-multitask",
                "description": "한국어 교통 도메인에 최적화된 SBERT 모델",
                "priority": 1
            },
            {
                "name": "범용 모델 (대안)",
                "model_id": "sentence-transformers/all-MiniLM-L6-v2",
                "description": "빠르고 효율적인 범용 SBERT 모델",
                "priority": 2
            },
            {
                "name": "다국어 모델 (대안)",
                "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "description": "다국어 지원 SBERT 모델",
                "priority": 3
            }
        ]
        
        print(f"\n📥 SBERT 모델 다운로드를 시작합니다...")
        print("한국어 특화 모델이 성공하면 나머지는 건너뜁니다.")
        
        primary_model_success = False
        
        for i, model_info in enumerate(models, 1):
            print(f"\n{i}/{len(models)}. {model_info['name']}")
            print(f"   모델 ID: {model_info['model_id']}")
            print(f"   설명: {model_info['description']}")
            
            try:
                print(f"   ⏳ 다운로드 중...")
                model = SentenceTransformer(model_info['model_id'])
                print(f"   ✅ 다운로드 완료!")
                
                # 간단한 테스트
                test_sentences = ["안녕하세요", "교통량 확인"]
                embeddings = model.encode(test_sentences)
                print(f"   🧪 테스트 완료 (임베딩 크기: {embeddings.shape})")
                
                # 한국어 특화 모델이 성공하면 나머지는 건너뛰기
                if model_info['priority'] == 1:
                    primary_model_success = True
                    print(f"   🎯 한국어 특화 모델 다운로드 성공!")
                    print(f"   ✅ 나머지 대안 모델들은 건너뜁니다.")
                    break
                
            except Exception as e:
                print(f"   ❌ 다운로드 실패: {e}")
                if model_info['priority'] == 1:
                    print(f"   ⚠️ 한국어 특화 모델 실패. 대안 모델을 시도합니다.")
                    continue
                else:
                    print(f"   ⚠️ 이 모델은 건너뛰고 다음 모델을 시도합니다.")
                    continue
        
        if primary_model_success:
            print(f"\n✅ 한국어 특화 SBERT 모델 설정 완료!")
            print("이제 의도 분류기에서 최적화된 한국어 모델을 사용합니다.")
        else:
            print(f"\n⚠️ 한국어 특화 모델 다운로드에 실패했습니다.")
            print("대안 모델을 사용하거나 네트워크 연결을 확인해주세요.")
        
        # 모델 저장 경로 확인
        cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
        if cache_dir.exists():
            print(f"\n📁 모델 캐시 위치: {cache_dir}")
            cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            print(f"📊 캐시 크기: {cache_size / (1024*1024):.1f} MB")
        
        return primary_model_success
        
    except ImportError:
        print("❌ sentence-transformers가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요:")
        print("pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ SBERT 모델 설정 중 오류 발생: {e}")
        return False

def test_core_modules():
    """핵심 모듈 테스트"""
    print(f"\n" + "=" * 60)
    print("🧪 핵심 모듈 테스트")
    print("=" * 60)
    
    try:
        from core.query_router import QueryRouter
        from core.sql_element_extractor import SQLElementExtractor
        from core.answer_generator import AnswerGenerator
        
        print("핵심 모듈 임포트 성공!")
        
        # 간단한 테스트
        test_questions = [
            "교통량이 가장 많은 구간은 어디인가요?",
            "IFRO 시스템이 무엇인가요?",
            "안녕하세요"
        ]
        
        print(f"\n테스트 질문들:")
        for i, question in enumerate(test_questions, 1):
            print(f"{i}. {question}")
        
        print(f"\n모듈 초기화 테스트:")
        try:
            router = QueryRouter()
            print("✅ QueryRouter 초기화 성공")
        except Exception as e:
            print(f"❌ QueryRouter 초기화 실패: {e}")
        
        try:
            extractor = SQLElementExtractor()
            print("✅ SQLElementExtractor 초기화 성공")
        except Exception as e:
            print(f"❌ SQLElementExtractor 초기화 실패: {e}")
        
        try:
            generator = AnswerGenerator()
            print("✅ AnswerGenerator 초기화 성공")
        except Exception as e:
            print(f"❌ AnswerGenerator 초기화 실패: {e}")
        
        print("✅ 핵심 모듈 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 핵심 모듈 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 SBERT 모델 자동 다운로드 설정 시작")
    
    # 1. 의존성 확인
    if not check_dependencies():
        print("\n❌ 의존성 문제로 인해 설정을 중단합니다.")
        return
    
    # 2. SBERT 모델 다운로드
    if not setup_sbert_models():
        print("\n❌ SBERT 모델 설정에 실패했습니다.")
        return
    
    # 3. 핵심 모듈 테스트
    if not test_core_modules():
        print("\n❌ 핵심 모듈 테스트에 실패했습니다.")
        return
    
    print(f"\n" + "=" * 60)
    print("🎉 SBERT 모델 설정 완료!")
    print("이제 최적화된 챗봇 시스템을 사용할 수 있습니다.")
    print("=" * 60)

if __name__ == "__main__":
    main()
