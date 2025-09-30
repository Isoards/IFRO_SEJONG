# RAG + 웹 검색 기능 추가 가이드

## 개요

기존 RAG 시스템에 웹 검색 기능을 추가하여 **최신 정보**를 활용할 수 있도록 개선했습니다.

## 주요 기능

### 🔍 **웹 검색 기능**
- **자동 웹 검색**: 최신 정보가 필요한 질문에 자동으로 웹 검색 실행
- **다중 검색 엔진**: Google, Bing, DuckDuckGo 지원
- **API 키 지원**: Google Custom Search API 등 고급 검색 기능
- **스마트 판단**: 웹 검색이 필요한 질문인지 자동 판단

### 🤖 **하이브리드 RAG**
- **RAG + 웹**: 기존 RAG 결과 + 웹 검색 결과 결합
- **신뢰도 유지**: RAG의 신뢰도 점수 유지
- **소스 추적**: RAG 소스 + 웹 검색 소스 모두 제공
- **선택적 사용**: 웹 검색 기능을 켜고 끌 수 있음

## 설치 및 설정

### 1. 의존성 설치

```bash
# 웹 검색 기능이 추가된 requirements 설치
pip install -r requirements_web.txt
```

### 2. 환경 변수 설정

```bash
# Google Custom Search API 키 (선택사항)
export WEB_SEARCH_API_KEY="your_google_api_key"

# 웹 검색 엔진 선택 (기본값: google)
export WEB_SEARCH_ENGINE="google"  # google, bing, duckduckgo
```

### 3. 서버 시작

```bash
# 기본 설정으로 시작
python scripts/start_web_enhanced_server.py

# 커스텀 설정으로 시작
python scripts/start_web_enhanced_server.py \
    --host 0.0.0.0 \
    --port 8010 \
    --web-search-engine google \
    --web-search-api-key "your_api_key"
```

## API 사용법

### 1. 기본 질문 (RAG만 사용)

```bash
curl -X POST "http://localhost:8010/api/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "교통 정책이 무엇인가요?",
       "mode": "accuracy",
       "use_web_search": false
     }'
```

### 2. 웹 검색 포함 질문

```bash
curl -X POST "http://localhost:8010/api/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "최신 교통 정책 변경사항은 무엇인가요?",
       "mode": "accuracy",
       "use_web_search": true
     }'
```

### 3. 응답 예시

```json
{
  "answer": "교통 정책에 대한 답변...\n\n=== 최신 웹 검색 결과 ===\n1. 2024년 교통 정책 변경사항\n   URL: https://example.com/news\n   내용: 최신 교통 정책 변경 내용...",
  "confidence": 0.85,
  "sources": [...],
  "metrics": {...},
  "fallback_used": false,
  "web_search_used": true,
  "web_search_results": "=== 최신 웹 검색 결과 ===\n..."
}
```

## 웹 검색 트리거 조건

### 자동 웹 검색이 실행되는 경우:

1. **시간 관련 키워드**
   - "최신", "현재", "오늘", "어제", "이번 주", "이번 달", "올해"
   - "뉴스", "시사", "정책", "법령", "규정", "변경", "개정"
   - "실시간", "라이브", "현재 상황", "최근", "최신 동향"

2. **시간 표현**
   - "2024년", "12월", "오늘", "최근", "최신", "현재"

3. **예시 질문**
   - "최신 교통 정책은 무엇인가요?"
   - "오늘 교통 뉴스는 무엇인가요?"
   - "2024년 교통법 개정사항은?"
   - "현재 교통 체증 상황은?"

## 검색 엔진 설정

### 1. Google (기본값)
```bash
# API 키 없이 사용 (기본 웹 검색)
export WEB_SEARCH_ENGINE="google"

# Google Custom Search API 사용 (권장)
export WEB_SEARCH_API_KEY="your_google_api_key"
export WEB_SEARCH_ENGINE="google"
```

### 2. Bing
```bash
export WEB_SEARCH_ENGINE="bing"
```

### 3. DuckDuckGo
```bash
export WEB_SEARCH_ENGINE="duckduckgo"
```

## 성능 최적화

### 1. 웹 검색 제한
- **최대 결과 수**: 3개 (기본값)
- **검색 타임아웃**: 10초
- **캐싱**: 동일 질문에 대한 캐싱 지원

### 2. API 키 설정 (권장)
- **Google Custom Search API**: 더 정확하고 안정적인 검색
- **무료 할당량**: 일일 100회 검색 (Google)
- **API 키 발급**: [Google Cloud Console](https://console.cloud.google.com/)

## 모니터링

### 1. 로그 확인
```bash
# 웹 검색 사용 로그
tail -f logs/chatbot_conversations.log | grep "웹검색"

# 상세 질문/답변 로그
tail -f logs/qa_detailed.log
```

### 2. 메트릭 확인
```bash
# 웹 검색 사용 통계
curl http://localhost:8010/metrics
```

### 3. 상태 확인
```bash
# 서버 상태 및 웹 검색 설정 확인
curl http://localhost:8010/status
```

## 문제 해결

### 1. 웹 검색이 작동하지 않는 경우
- **API 키 확인**: 올바른 API 키 설정 여부
- **네트워크 연결**: 인터넷 연결 상태 확인
- **검색 엔진 설정**: 지원되는 검색 엔진 사용 여부

### 2. 검색 결과가 없는 경우
- **질문 형식**: 웹 검색 트리거 조건 확인
- **검색 엔진**: 다른 검색 엔진으로 변경 시도
- **API 할당량**: API 키 할당량 확인

### 3. 성능 문제
- **타임아웃 설정**: 검색 타임아웃 조정
- **결과 수 제한**: 최대 결과 수 감소
- **캐싱 활용**: 동일 질문 캐싱 활용

## 예시 사용 시나리오

### 시나리오 1: 최신 교통 정책 문의
```bash
curl -X POST "http://localhost:8010/api/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "2024년 최신 교통 정책 변경사항은 무엇인가요?",
       "use_web_search": true
     }'
```

### 시나리오 2: 실시간 교통 정보
```bash
curl -X POST "http://localhost:8010/api/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "오늘 서울시 교통 상황은 어떤가요?",
       "use_web_search": true
     }'
```

### 시나리오 3: 기존 RAG만 사용
```bash
curl -X POST "http://localhost:8010/api/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "교통 정책의 기본 원칙은 무엇인가요?",
       "use_web_search": false
     }'
```

## 주의사항

1. **API 키 보안**: API 키를 환경 변수로 설정하여 보안 유지
2. **할당량 관리**: API 사용량 모니터링 및 할당량 관리
3. **검색 품질**: 검색 결과의 신뢰성 및 정확성 검증
4. **성능 최적화**: 웹 검색으로 인한 응답 시간 증가 고려

---

**이제 RAG + 웹 검색을 결합한 강력한 교통 정책 챗봇을 사용할 수 있습니다!** 🚀
