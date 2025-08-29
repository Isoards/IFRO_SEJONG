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
