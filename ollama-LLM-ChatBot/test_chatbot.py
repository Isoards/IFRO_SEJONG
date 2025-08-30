#!/usr/bin/env python3
"""
챗봇 테스트 스크립트

이 스크립트는 챗봇 서버의 기능을 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime

def test_chatbot():
    """챗봇 테스트"""
    
    # 서버 URL
    base_url = "http://localhost:8008"
    
    # 테스트 질문들
    test_questions = [
        "교통량이 가장 많은 지역을 알려줘",
        "안녕하세요",
        "교통사고가 몇 건 발생했나요?",
        "조치원으로 이동해주세요"
    ]
    
    print("=" * 60)
    print("🤖 챗봇 테스트 시작")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 테스트 {i}: {question}")
        print("-" * 40)
        
        try:
            # 요청 데이터
            request_data = {
                "question": question,
                "pdf_id": "",
                "user_id": "test_user",
                "use_conversation_context": True,
                "max_chunks": 5,
                "use_dual_pipeline": True
            }
            
            # 요청 시작 시간
            start_time = time.time()
            
            # API 호출
            response = requests.post(
                f"{base_url}/ask",
                json=request_data,
                timeout=60
            )
            
            # 응답 시간 계산
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ 응답 성공 (소요시간: {response_time:.2f}초)")
                print(f"답변: {result['answer']}")
                print(f"신뢰도: {result['confidence_score']:.3f}")
                print(f"질문 유형: {result['question_type']}")
                print(f"파이프라인: {result['pipeline_type']}")
                print(f"모델: {result['model_name']}")
                
                if result.get('sql_query'):
                    print(f"SQL 쿼리: {result['sql_query']}")
                    
            else:
                print(f"❌ 응답 실패 (상태 코드: {response.status_code})")
                print(f"오류: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 요청 시간 초과 (60초)")
        except requests.exceptions.ConnectionError:
            print(f"❌ 서버 연결 실패")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("-" * 40)
        time.sleep(1)  # 요청 간 간격
    
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    print("=" * 60)

def test_server_status():
    """서버 상태 테스트"""
    print("\n🔍 서버 상태 확인 중...")
    
    try:
        response = requests.get("http://localhost:8008/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 서버 상태: {status['status']}")
            print(f"모델 로드: {status['model_loaded']}")
            print(f"PDF 수: {status['total_pdfs']}")
            print(f"청크 수: {status['total_chunks']}")
        else:
            print(f"❌ 서버 상태 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 상태 확인 오류: {e}")

if __name__ == "__main__":
    # 서버 상태 확인
    test_server_status()
    
    # 챗봇 테스트
    test_chatbot()
