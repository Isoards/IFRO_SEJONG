# Multi-Expression Chatbot (다중 표현 인덱싱 챗봇)

교통 도메인에 특화된 다중 표현 인덱싱 기술을 적용한 지능형 챗봇 시스템입니다.

## 🚀 주요 기능

### 다중 표현 인덱싱 (Multi-Expression Indexing)
- **동의어 처리**: 같은 의미의 다양한 표현을 자동 인식
- **도메인 특화 표현**: 교통, 데이터베이스, 일반 도메인별 최적화된 표현 관리
- **컨텍스트 기반 분석**: 질문의 맥락에 따른 적절한 표현 선택
- **학습 기반 최적화**: 사용자 피드백을 통한 표현 성능 지속 개선

### 핵심 컴포넌트
- **Dual Pipeline 처리**: SQL 질의와 문서 검색을 분리 처리
- **하이브리드 벡터 저장소**: FAISS와 ChromaDB를 병행 사용
- **다중 임베딩 모델**: 한국어 특화 및 다국어 지원
- **실시간 피드백 시스템**: 표현 사용 통계 및 성공률 추적

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   사용자 질문   │───▶│  다중 표현 분석 │───▶│  컨텍스트 결정  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  표현별 인덱스  │◀───│  표현 체인 관리 │    │  파이프라인 분기 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  피드백 시스템  │◀───│  결과 통합      │◀───│  검색/질의 처리 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
```bash
# 환경 변수 설정
export MODEL_TYPE=ollama
export MODEL_NAME=mistral:latest
export EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
```

### 3. 서버 실행
```bash
python main.py
```

### 4. 테스트 실행
```bash
python test_multi_expression.py
```

## 🔧 다중 표현 인덱싱 사용법

### 기본 사용
```python
from utils.keyword_enhancer import KeywordEnhancer

# 키워드 향상기 초기화
enhancer = KeywordEnhancer(domain="traffic")

# 표현 추출
expressions = enhancer.get_multi_expressions("교통사고 정보", "traffic")
print(expressions)  # ['교통사고', '사고', '충돌', '교통사고', ...]

# 최적 표현 선택
optimal = enhancer.get_optimal_expressions("교통사고 정보", "traffic", top_k=3)
print(optimal)  # [('교통사고', 0.95), ('사고', 0.88), ...]
```

### 사용자 정의 표현 추가
```python
# 새로운 표현 체인 추가
enhancer.add_custom_expression_chain(
    base_expression="교통안전",
    related_expressions=["안전", "교통안전", "안전관리"],
    context="traffic",
    weight=1.5
)
```

### 쿼리 향상
```python
# 표현을 활용한 쿼리 향상
enhanced_query = enhancer.enhance_query_with_expressions(
    "교통사고", "traffic"
)
print(enhanced_query)  # "교통사고 사고 충돌"
```

## 📊 표현 통계 및 모니터링

### 통계 조회
```python
# 표현 사용 통계
stats = enhancer.get_expression_statistics()
print(stats)
# {
#   "total_chains": 25,
#   "total_feedback": 150,
#   "contexts": ["traffic", "database", "general"],
#   "top_expressions": [...]
# }
```

### 피드백 업데이트
```python
# 표현 사용 피드백 업데이트
enhancer.update_expression_feedback(
    query="교통사고 정보",
    expressions_used=["교통사고", "사고"],
    success=True,
    user_rating=5
)
```

## 🎯 도메인별 표현 예시

### 교통 도메인
- **교통사고**: 사고, 충돌, 교통사고, 교통사고사고
- **교차로**: 사거리, 교차점, 인터섹션, 교차로
- **신호등**: 신호, 신호등, 트래픽라이트, 신호등
- **교통량**: 트래픽, 교통량, 차량수, 교통량

### 데이터베이스 도메인
- **조회**: 검색, 찾기, 가져오기, SELECT, 조회
- **통계**: 집계, 합계, 평균, COUNT, 통계
- **기간**: 기간, 날짜, 시간, 기간, 기간
- **정렬**: 순서, 정렬, ORDER BY, 정렬

## 🔍 API 엔드포인트

### 채팅
```http
POST /chat
{
  "question": "교통사고 통계를 보여주세요",
  "context": "traffic"
}
```

### 표현 통계
```http
GET /statistics
```

### 사용자 정의 표현 추가
```http
POST /expressions/add
{
  "base_expression": "교통안전",
  "related_expressions": ["안전", "교통안전"],
  "context": "traffic",
  "weight": 1.5
}
```

## 📈 성능 최적화

### 1. 표현 가중치 조정
- 도메인별 가중치 설정
- 사용 빈도 기반 동적 조정
- 성공률 기반 자동 최적화

### 2. 캐싱 전략
- 자주 사용되는 표현 조합 캐싱
- 컨텍스트별 캐싱 분리
- 실시간 캐시 업데이트

### 3. 병렬 처리
- 표현별 병렬 검색
- 다중 임베딩 모델 동시 처리
- 비동기 피드백 업데이트

## 🛠️ 개발 및 확장

### 새로운 도메인 추가
```python
# 도메인별 표현 정의
new_domain_expressions = {
    "medical": {
        "진료": ["진료", "치료", "의료", "병원"],
        "증상": ["증상", "병증", "아픔", "통증"]
    }
}

# 표현 체인 추가
for base_expr, related_exprs in new_domain_expressions.items():
    enhancer.add_custom_expression_chain(
        base_expr, related_exprs, "medical", weight=1.0
    )
```

### 커스텀 표현 체인
```python
class CustomExpressionChain:
    def __init__(self, base_expression, related_expressions, weight=1.0):
        self.base_expression = base_expression
        self.related_expressions = related_expressions
        self.weight = weight
        self.usage_count = 0
        self.success_count = 0
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

