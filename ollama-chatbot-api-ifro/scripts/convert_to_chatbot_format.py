#!/usr/bin/env python3
"""
TF-IDF 인덱스를 챗봇이 인식할 수 있는 형식으로 변환
"""

import json
import pickle
import shutil
from pathlib import Path

def convert_tfidf_to_chatbot_format():
    """TF-IDF 인덱스를 챗봇 형식으로 변환"""
    
    # 소스 경로
    source_dir = Path("data/vector_index")
    target_dir = Path("vector_store")
    
    print("벡터 스토어 변환 시작...")
    
    # 대상 디렉토리 생성
    target_dir.mkdir(exist_ok=True)
    
    # 문서 메타데이터 복사
    if (source_dir / "documents.json").exists():
        shutil.copy2(source_dir / "documents.json", target_dir / "documents.json")
        print("✅ documents.json 복사 완료")
    
    # TF-IDF 매트릭스와 어휘 사전을 챗봇이 인식할 수 있는 형식으로 변환
    if (source_dir / "tfidf_matrix.pkl").exists() and (source_dir / "vocabulary.pkl").exists():
        
        # TF-IDF 매트릭스 로드
        with open(source_dir / "tfidf_matrix.pkl", "rb") as f:
            tfidf_matrix = pickle.load(f)
        
        with open(source_dir / "vocabulary.pkl", "rb") as f:
            vocabulary = pickle.load(f)
        
        print(f"TF-IDF 매트릭스 크기: {len(tfidf_matrix)} x {len(vocabulary)}")
        
        # 챗봇이 인식할 수 있는 메타데이터 생성
        meta_data = {
            "type": "tfidf",
            "dim": len(vocabulary),
            "documents": len(tfidf_matrix),
            "vocabulary_size": len(vocabulary),
            "created_at": "2024-10-16T04:00:00Z"
        }
        
        with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        # TF-IDF 매트릭스 저장 (챗봇 형식)
        with open(target_dir / "tfidf_matrix.pkl", "wb") as f:
            pickle.dump(tfidf_matrix, f)
        
        # 어휘 사전 저장
        with open(target_dir / "vocabulary.pkl", "wb") as f:
            pickle.dump(vocabulary, f)
        
        # 매핑 파일 생성 (문서 ID 매핑)
        id_mapping = list(range(len(tfidf_matrix)))
        with open(target_dir / "mapping.json", "w", encoding="utf-8") as f:
            json.dump(id_mapping, f, ensure_ascii=False, indent=2)
        
        print("✅ TF-IDF 인덱스 변환 완료")
        print(f"   - 메타데이터: {target_dir / 'meta.json'}")
        print(f"   - TF-IDF 매트릭스: {target_dir / 'tfidf_matrix.pkl'}")
        print(f"   - 어휘 사전: {target_dir / 'vocabulary.pkl'}")
        print(f"   - ID 매핑: {target_dir / 'mapping.json'}")
    
    else:
        print("❌ TF-IDF 인덱스 파일을 찾을 수 없습니다.")
        return False
    
    print(f"\n벡터 스토어 변환 완료: {target_dir}")
    return True

if __name__ == "__main__":
    success = convert_tfidf_to_chatbot_format()
    if success:
        print("\n🎉 챗봇이 인식할 수 있는 벡터 스토어가 준비되었습니다!")
        print("이제 챗봇 서버를 재시작하면 새로운 교통 정책 데이터를 사용할 수 있습니다.")
    else:
        print("\n❌ 벡터 스토어 변환에 실패했습니다.")
