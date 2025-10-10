#!/usr/bin/env python3
"""
Gemini AI 분석 테스트 스크립트
"""
import os
import sys
import django

# Django 설정
import sys
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from traffic.gemini_service import GeminiTrafficAnalyzer
from traffic.models import Intersection

def test_gemini_analysis():
    """Gemini AI 분석 테스트"""
    try:
        print("🔍 Gemini AI 분석 테스트 시작...")
        
        # 교차로 확인
        intersection = Intersection.objects.filter(id=1).first()
        if not intersection:
            print("❌ 교차로 ID 1을 찾을 수 없습니다.")
            return
        
        print(f"✅ 교차로 발견: {intersection.name}")
        
        # Gemini 분석기 초기화
        analyzer = GeminiTrafficAnalyzer()
        print("✅ Gemini 분석기 초기화 완료")
        
        # 분석 실행
        print("🚀 AI 분석 실행 중...")
        result = analyzer.analyze_intersection_traffic(
            intersection_id=1,
            time_period="24h",
            language="ko",
            use_report_data=True
        )
        
        print("✅ 분석 완료!")
        print(f"📊 분석 결과 키: {list(result.keys())}")
        
        if 'error' in result:
            print(f"❌ 에러 발생: {result['error']}")
        else:
            print(f"📝 분석 내용 길이: {len(result.get('analysis', ''))}")
            print(f"🎯 혼잡 수준: {result.get('congestion_level', 'N/A')}")
            print(f"📈 피크 방향: {result.get('peak_direction', 'N/A')}")
            print(f"💡 권장사항 수: {len(result.get('recommendations', []))}")
            print(f"🔍 인사이트 수: {len(result.get('insights', []))}")
            
            if 'statistical_analysis' in result:
                print(f"📊 통계 분석: {result['statistical_analysis']}")
            
            if 'completeness_score' in result:
                print(f"⭐ 완성도 점수: {result['completeness_score']}%")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_analysis()
