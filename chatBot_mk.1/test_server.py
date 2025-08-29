#!/usr/bin/env python3
"""
테스트용 간단한 FastAPI 서버
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="PDF QA 챗봇 테스트 서버",
    description="의존성 문제 해결을 위한 테스트 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "PDF QA 챗봇 테스트 서버가 실행 중입니다!",
        "status": "success",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "서버가 정상적으로 작동하고 있습니다."
    }

@app.get("/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    return {
        "message": "테스트 성공!",
        "data": {
            "server": "FastAPI",
            "python_version": "3.11",
            "dependencies": "기본 패키지만 설치됨"
        }
    }

@app.post("/chat")
async def simple_chat(message: dict):
    """간단한 챗봇 응답 (PDF 없이 작동)"""
    try:
        # 메시지 추출
        user_message = message.get("message", "")
        if not user_message:
            return {
                "success": False,
                "response": "메시지가 비어있습니다.",
                "timestamp": "2025-08-29T14:55:40"
            }
        
        # 간단한 키워드 기반 응답
        lower_message = user_message.lower()
        
        if "교통" in lower_message or "traffic" in lower_message:
            response = "교통 데이터는 대시보드의 '분석' 탭에서 확인하실 수 있습니다. 특정 교차로를 클릭하시면 해당 지점의 상세한 교통량 정보를 볼 수 있어요."
        elif "사고" in lower_message or "incident" in lower_message:
            response = "교통사고 정보는 '사고' 탭에서 확인 가능합니다. 빨간색 삼각형 아이콘을 클릭하시면 사고 목록과 상세 정보를 볼 수 있습니다."
        elif "경로" in lower_message or "route" in lower_message:
            response = "경로 분석은 '교통흐름' 탭에서 이용하실 수 있습니다. 지도에서 두 지점을 선택하시면 해당 구간의 교통 흐름을 분석해드립니다."
        elif "즐겨찾기" in lower_message or "favorite" in lower_message:
            response = "관심 있는 교차로나 사고를 즐겨찾기에 추가하실 수 있습니다. 별표 아이콘을 클릭하시면 '즐겨찾기' 탭에서 쉽게 찾아보실 수 있어요."
        elif "help" in lower_message or "도움" in lower_message or "사용법" in lower_message:
            response = "IFRO 대시보드 사용법:\n\n🚗 분석: 교차로별 교통량 분석\n🔄 교통흐름: 두 지점 간 경로 분석\n⚠️ 사고: 교통사고 현황\n⭐ 즐겨찾기: 관심 지점 관리\n📊 Tableau: 고급 분석 대시보드\n\n더 자세한 정보가 필요하시면 구체적으로 물어보세요!"
        else:
            response = "네, 무엇을 도와드릴까요? 교통 데이터 분석, 대시보드 사용법, 특정 기능에 대해 궁금한 점이 있으시면 언제든 말씀해 주세요!"
        
        return {
            "success": True,
            "response": response,
            "timestamp": "2025-08-29T14:55:40"
        }
        
    except Exception as e:
        logger.error(f"챗봇 응답 생성 중 오류: {e}")
        return {
            "success": False,
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            "timestamp": "2025-08-29T14:55:40"
        }

if __name__ == "__main__":
    print("=" * 60)
    print("PDF QA 챗봇 테스트 서버 시작")
    print("=" * 60)
    print()
    print("기능:")
    print("- 기본 웹 서버 테스트")
    print("- 의존성 문제 해결 확인")
    print()
    print("API 문서: http://localhost:8008/docs")
    print("서버 주소: http://localhost:8008")
    print()
    print("=" * 60)
    
    # 서버 실행
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8008,
        reload=False,
        log_level="info"
    )
