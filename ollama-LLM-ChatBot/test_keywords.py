import re
import json
from pathlib import Path

def test_keyword_extraction():
    question = "사고 목록 확인하는 방법 알려줘"
    
    # 파이프라인 설정에서 키워드 로드
    patterns = []
    try:
        config_path = Path("config/pipelines/pdf_pipeline.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 기본 키워드들
            keywords = config.get("keywords", [])
            domain_keywords = config.get("domain_specific_keywords", [])
            
            # 모든 키워드를 패턴으로 변환
            all_keywords = list(set(keywords + domain_keywords))
            
            for keyword in all_keywords:
                # 키워드를 정규식 패턴으로 변환
                pattern = r'\b' + re.escape(keyword) + r'\b'
                patterns.append(pattern)
            
            print(f"✅ 파이프라인 설정에서 {len(patterns)}개 키워드 패턴 로드")
        else:
            print("파이프라인 설정 파일을 찾을 수 없습니다.")
            return
    except Exception as e:
        print(f"키워드 패턴 로드 실패: {e}")
        return
    
    keywords = []
    for pattern in patterns:
        matches = re.findall(pattern, question, re.IGNORECASE)
        keywords.extend(matches)
    
    # 중복 제거 및 정렬
    keywords = list(set(keywords))
    keywords.sort()
    
    print(f"질문: {question}")
    print(f"키워드: {keywords}")
    print(f"키워드 개수: {len(keywords)}")
    
    # 개별 키워드 매칭 확인
    print("\n개별 키워드 매칭 확인:")
    for keyword in ["사고", "목록", "확인", "방법", "알려줘"]:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, question, re.IGNORECASE)
        print(f"'{keyword}': {matches}")

if __name__ == "__main__":
    test_keyword_extraction()
