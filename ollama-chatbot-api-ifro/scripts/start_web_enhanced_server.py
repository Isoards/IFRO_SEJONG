#!/usr/bin/env python3
"""
웹 검색 기능이 추가된 서버 시작 스크립트
RAG + 웹 검색을 결합하여 최신 정보를 활용할 수 있도록 함
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="웹 검색 기능이 추가된 교통 정책 챗봇 서버 시작")
    parser.add_argument("--host", default="0.0.0.0", help="서버 호스트")
    parser.add_argument("--port", type=int, default=8010, help="서버 포트")
    parser.add_argument("--web-search-engine", default="google", 
                       choices=["google", "bing", "duckduckgo"],
                       help="웹 검색 엔진")
    parser.add_argument("--web-search-api-key", help="웹 검색 API 키 (Google Custom Search API 등)")
    parser.add_argument("--disable-web-search", action="store_true", 
                       help="웹 검색 기능 비활성화")
    parser.add_argument("--reload", action="store_true", help="개발 모드 (자동 리로드)")
    
    args = parser.parse_args()
    
    # 환경 변수 설정
    if args.web_search_api_key:
        os.environ['WEB_SEARCH_API_KEY'] = args.web_search_api_key
    os.environ['WEB_SEARCH_ENGINE'] = args.web_search_engine
    
    # 서버 시작
    server_file = Path(__file__).parent / "server" / "web_enhanced_app.py"
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        f"{server_file}:app",
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    if args.reload:
        cmd.append("--reload")
    
    print(f"🚀 웹 검색 기능이 추가된 교통 정책 챗봇 서버 시작")
    print(f"📍 주소: http://{args.host}:{args.port}")
    print(f"🔍 웹 검색 엔진: {args.web_search_engine}")
    print(f"🌐 웹 검색 활성화: {not args.disable_web_search}")
    
    if args.web_search_api_key:
        print(f"🔑 API 키: {'*' * (len(args.web_search_api_key) - 4) + args.web_search_api_key[-4:]}")
    else:
        print("⚠️  API 키가 설정되지 않음 - 기본 웹 검색 사용")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 서버 종료")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
