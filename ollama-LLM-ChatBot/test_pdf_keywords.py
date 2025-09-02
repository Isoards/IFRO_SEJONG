import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.document.pdf_keyword_extractor import PDFKeywordExtractor

def test_pdf_keyword_extractor():
    """PDF 키워드 추출기 테스트"""
    
    # 키워드 추출기 초기화
    extractor = PDFKeywordExtractor(cache_threshold=3)  # 3번 이상 나온 단어를 키워드로 추가
    
    # 테스트 텍스트 (사고 관련 문서 내용 시뮬레이션)
    test_texts = [
        "교통사고 발생 건수가 증가하고 있습니다. 사고 목록을 확인하여 분석이 필요합니다.",
        "사고 통계 자료를 보면 교통사고가 주요 원인입니다. 사고 정보를 수집하고 있습니다.",
        "사고 데이터 분석 결과 교통사고가 가장 많습니다. 사고 보고서를 작성해야 합니다.",
        "사고 목록 확인 방법을 알려드리겠습니다. 사고 정보를 조회할 수 있습니다.",
        "교통사고 사고목록 사고정보 사고데이터 사고통계 사고분석 사고보고서 사고리포트",
        "사고자료 사고문서 사고파일 사고목록 확인 방법 알려줘 교통사고 분석",
        "사고 발생 건수 사고 통계 사고 분석 사고 보고서 사고 정보 사고 데이터",
        "교통사고 사고목록 사고정보 사고데이터 사고통계 사고분석 사고보고서",
        "사고목록 확인 방법 사고정보 조회 사고데이터 분석 사고통계 확인",
        "교통사고 사고목록 사고정보 사고데이터 사고통계 사고분석 사고보고서 사고리포트"
    ]
    
    print("=== PDF 키워드 추출기 테스트 ===")
    
    # 각 텍스트에서 키워드 추출
    for i, text in enumerate(test_texts, 1):
        print(f"\n텍스트 {i}: {text[:50]}...")
        keywords = extractor.extract_keywords_from_text(text)
        print(f"추출된 키워드: {keywords}")
    
    # 자주 사용된 키워드 확인
    print(f"\n=== 자주 사용된 키워드 (임계값: {extractor.cache_threshold}회) ===")
    frequent_keywords = extractor.get_frequent_keywords()
    print(f"자주 사용된 키워드: {frequent_keywords}")
    
    # 캐시 통계 확인
    stats = extractor.get_cache_stats()
    print(f"\n=== 캐시 통계 ===")
    print(f"총 키워드 수: {stats['total_keywords']}")
    print(f"자주 사용된 키워드 수: {stats['frequent_keywords']}")
    print(f"이미 추출된 키워드 수: {stats['extracted_keywords']}")
    print(f"상위 10개 키워드: {stats['top_keywords']}")
    
    # 파이프라인에 키워드 추가
    print(f"\n=== 파이프라인에 키워드 추가 ===")
    extractor.add_keywords_to_pipeline()
    
    # 추가 후 통계 확인
    stats_after = extractor.get_cache_stats()
    print(f"추가 후 자주 사용된 키워드 수: {stats_after['frequent_keywords']}")
    print(f"추가 후 이미 추출된 키워드 수: {stats_after['extracted_keywords']}")

if __name__ == "__main__":
    test_pdf_keyword_extractor()
