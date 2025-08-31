#!/usr/bin/env python3
"""
리팩토링된 모듈 테스트

실제 데이터베이스 구조에 맞게 리팩토링된 모듈들을 테스트
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from core.real_database_executor import RealDatabaseExecutor
from core.sql_element_extractor import SQLElementExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("데이터베이스 연결 테스트")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    result = db_executor.test_connection()
    
    if result['success']:
        print("✅ 데이터베이스 연결 성공")
        details = result['details']
        print(f"  - 사용 가능한 테이블: {details['available_main_tables']}")
        print(f"  - 테이블별 데이터 개수: {details['table_counts']}")
        print(f"  - 세종 교차로 개수: {details['sejong_intersection_count']}")
        print(f"  - 세종 사고 개수: {details['sejong_incident_count']}")
    else:
        print(f"❌ 데이터베이스 연결 실패: {result['error']}")
    
    return result['success']

def test_sql_element_extractor():
    """SQL 요소 추출기 테스트"""
    print("\n" + "=" * 60)
    print("SQL 요소 추출기 테스트")
    print("=" * 60)
    
    extractor = SQLElementExtractor()
    
    test_questions = [
        "세종특별자치시 교차로 개수는 몇 개인가요?",
        "세종 지역 교통량 데이터를 보여주세요",
        "세종에서 발생한 교통사고 건수는?",
        "세종특별자치시금남면 교차로의 교통량을 알려주세요",
        "최근 10건의 사고 정보를 보여주세요"
    ]
    
    for question in test_questions:
        print(f"\n질문: {question}")
        elements = extractor.extract_elements(question)
        
        print(f"  - 테이블: {elements.table_name}")
        print(f"  - 쿼리 타입: {elements.query_type.value}")
        print(f"  - 컬럼: {elements.columns}")
        print(f"  - 조건: {elements.conditions}")
        print(f"  - 정렬: {elements.order_by}")
        print(f"  - 제한: {elements.limit}")
        print(f"  - 신뢰도: {elements.confidence:.2f}")
        
        # SQL 생성
        sql = extractor.generate_sql(elements)
        print(f"  - 생성된 SQL: {sql}")

def test_real_database_executor():
    """실제 데이터베이스 실행기 테스트"""
    print("\n" + "=" * 60)
    print("실제 데이터베이스 실행기 테스트")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    
    # 1. 교차로 데이터 조회
    print("\n1. 세종 교차로 데이터 조회:")
    result = db_executor.get_intersection_data("세종", 5)
    if result['success']:
        print(f"  - 조회된 교차로 수: {result['row_count']}")
        for i, row in enumerate(result['data'][:3], 1):
            print(f"    {i}. {row['name']} (ID: {row['id']})")
    else:
        print(f"  - 오류: {result['error']}")
    
    # 2. 교통량 데이터 조회
    print("\n2. 교통량 데이터 조회:")
    result = db_executor.get_traffic_volume_data(limit=5)
    if result['success']:
        print(f"  - 조회된 교통량 데이터 수: {result['row_count']}")
        for i, row in enumerate(result['data'][:3], 1):
            print(f"    {i}. {row['intersection_name']} - {row['datetime']} ({row['direction']}방향: {row['volume']})")
    else:
        print(f"  - 오류: {result['error']}")
    
    # 3. 사고 데이터 조회
    print("\n3. 세종 사고 데이터 조회:")
    result = db_executor.get_incident_data("세종", 5)
    if result['success']:
        print(f"  - 조회된 사고 데이터 수: {result['row_count']}")
        for i, row in enumerate(result['data'][:3], 1):
            print(f"    {i}. {row['district']} {row['intersection_name']} - {row['incident_type']} ({row['status']})")
    else:
        print(f"  - 오류: {result['error']}")
    
    # 4. 데이터 요약
    print("\n4. 데이터 요약:")
    result = db_executor.get_data_summary()
    if result['success']:
        summary = result['data']
        print(f"  - 교차로 요약: {summary.get('intersection_summary', {})}")
        print(f"  - 교통량 요약: {summary.get('traffic_volume_summary', {})}")
        print(f"  - 사고 요약: {summary.get('incident_summary', {})}")
    else:
        print(f"  - 오류: {result['error']}")

def test_integration():
    """통합 테스트"""
    print("\n" + "=" * 60)
    print("통합 테스트")
    print("=" * 60)
    
    # SQL 요소 추출기로 SQL 생성 후 실제 실행
    extractor = SQLElementExtractor()
    db_executor = RealDatabaseExecutor()
    
    test_questions = [
        "세종 교차로 개수는 몇 개인가요?",
        "세종 지역 교통량 데이터 5개를 보여주세요",
        "세종에서 발생한 교통사고 건수는?",
        "세종특별자치시금남면 교차로의 교통량을 알려주세요"
    ]
    
    for question in test_questions:
        print(f"\n질문: {question}")
        
        # SQL 요소 추출 및 SQL 생성
        elements = extractor.extract_elements(question)
        sql = extractor.generate_sql(elements)
        print(f"  - 생성된 SQL: {sql}")
        
        # 실제 실행
        result = db_executor.execute_sql(sql)
        if result['success']:
            print(f"  - 실행 결과: {result['row_count']}개 행")
            if result['data'] and len(result['data']) > 0:
                print(f"  - 첫 번째 결과: {result['data'][0]}")
        else:
            print(f"  - 실행 오류: {result['error']}")

def main():
    """메인 테스트 함수"""
    print("리팩토링된 모듈 테스트 시작")
    
    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        print("❌ 데이터베이스 연결 실패로 테스트 중단")
        return
    
    # 2. SQL 요소 추출기 테스트
    test_sql_element_extractor()
    
    # 3. 실제 데이터베이스 실행기 테스트
    test_real_database_executor()
    
    # 4. 통합 테스트
    test_integration()
    
    print("\n" + "=" * 60)
    print("모든 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()
