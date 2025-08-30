# IFRO 교통 챗봇 LLM RAG 시스템

## 🚀 개요

IFRO(Intelligent Freeway Ramp Operations) 교통 챗봇은 교통 관련 질문에 대해 지능적으로 답변하는 LLM 기반 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 🏗️ 시스템 아키텍처

### 핵심 구성 요소

1. **벡터 저장소 (Vector Store)**
   - 하이브리드 저장소: FAISS와 ChromaDB 지원
   - 다중 표현 인덱싱: 동일한 의미의 다양한 표현을 함께 저장
   - 임베딩 모델: `jhgan/ko-sroberta-multitask` (한국어 특화)

2. **LLM 모델**
   - Ollama 기반 Mistral 모델 (로컬 실행)
   - 다중 모델 지원: HuggingFace, llama.cpp 등 확장 가능
   - 생성 설정: Temperature 0.7, Top-p 0.9

3. **고도화된 의도 분류기 (Intent Classifier)**
   - SBERT + FastText 하이브리드 구조
   - 3단계 분류: FastText → SBERT → LLM
   - 교통 도메인 특화 학습 데이터
   - 실시간 응답 최적화

## 🎯 의도 분류 시스템

### 의도 유형

시스템은 다음과 같은 12가지 의도 유형을 분류합니다:

1. **DB_QUERY**: 데이터베이스 질의 (교통량, 사고 데이터 조회)
2. **FACTUAL_INQUIRY**: 사실 질문 (IFRO 시스템 정의, 기능 설명)
3. **CONCEPTUAL_INQUIRY**: 개념 질문 (시스템 간 차이점, 원리 설명)
4. **PROCEDURAL_INQUIRY**: 절차 질문 (사용 방법, 접속 방법)
5. **DATA_ANALYSIS**: 데이터 분석 (패턴 분석, 성능 분석)
6. **STATISTICAL_QUERY**: 통계 질문 (사용률, 가동률, 정확도)
7. **COMPARISON_INQUIRY**: 비교 질문 (시스템 성능 비교)
8. **RANKING_INQUIRY**: 순위 질문 (성능 순위, 효율성 순위)
9. **GREETING**: 인사말 (시스템 환영 메시지)
10. **CLARIFICATION**: 명확화 요청 (구체적 설명 요구)
11. **FOLLOW_UP**: 후속 질문 (추가 정보 요청)
12. **LOCATION_MOVEMENT**: 장소 이동 요청 (화면 전환)

### 하이브리드 분류 구조

```
질문 입력
    ↓
1단계: FastText (빠른 필터링)
    - 신뢰도 > 0.8: 즉시 반환
    - 신뢰도 ≤ 0.8: 2단계로 진행
    ↓
2단계: SBERT (정확한 분류)
    - 신뢰도 > 0.7: 반환
    - 신뢰도 ≤ 0.7: 3단계로 진행
    ↓
3단계: LLM Fallback (복잡한 케이스)
    - 최종 분류 결과 반환
```

### 성능 특징

- **응답 시간**: 50-200ms (대부분 1-2단계에서 해결)
- **정확도**: 85-95% (3단계 조합으로 높은 정확도)
- **처리량**: 초당 수백 건 처리 가능

## 📊 데이터셋

### 학습 데이터 구성

- **총 예시 수**: 408개
- **의도 유형 수**: 12개
- **평균 예시 수**: 34개/의도
- **데이터 균형**: 최대/최소 비율 1.1 (매우 균형잡힘)

### 데이터 분포

- **질문 길이**: 평균 19.4자 (2-44자)
- **주요 키워드**: 교통(181회), 시스템(89회), 데이터(67회)
- **도메인 특화**: IFRO, 교통량, 교통사고, 신호등 등

## 🔧 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. SBERT 모델 자동 다운로드 설정

```bash
# SBERT 모델 자동 다운로드 및 설정
python setup_sbert.py
```

이 스크립트는 다음 작업을 수행합니다:
- **의존성 확인**: 필요한 패키지들이 설치되어 있는지 확인
- **SBERT 모델 다운로드**: 한국어 특화 모델 및 대안 모델들을 자동으로 다운로드
- **의도 분류기 테스트**: 다운로드된 모델로 의도 분류기 동작 확인

### 3. 의도 분류기 학습

```bash
# 데이터셋 분석
python analyze_dataset.py

# 분류기 학습
python train_intent_classifier.py
```

### 4. 시스템 실행

```bash
# 메인 서버 실행
python main.py

# 또는 FastAPI 서버 실행
python run_server.py
```

## 🐳 Docker 실행 (권장)

### 전체 시스템 실행 (상위 디렉토리에서)

이 챗봇은 상위 `IFRO-SEJONG` 디렉토리의 `docker-compose.yml`에 통합되어 있습니다.

```bash
# 상위 디렉토리로 이동
cd ..

# 전체 시스템 시작 (자동으로 모든 설정 완료)
docker-compose up -d
```

### Docker 실행 시 자동 설정 과정

Docker 컨테이너가 시작되면 다음 순서로 자동 설정이 진행됩니다:

#### 1단계: 의존성 확인
- Python 패키지 설치 상태 확인
- 필수 라이브러리 검증

#### 2단계: SBERT 모델 자동 다운로드
- `jhgan/ko-sroberta-multitask` (한국어 특화 모델) - **우선 사용**
- 한국어 특화 모델이 성공하면 나머지 대안 모델들은 건너뜀
- 실패 시에만 대안 모델들 시도:
  - `sentence-transformers/all-MiniLM-L6-v2` (범용 모델)
  - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (다국어 모델)

#### 3단계: 의도 분류기 초기화
- FastText 분류기 학습
- SBERT 분류기 초기화
- 하이브리드 분류 시스템 구축

#### 4단계: Ollama 서버 대기
- Ollama 서버가 완전히 시작될 때까지 대기
- 네트워크 연결 확인

#### 5단계: Ollama 모델 다운로드
- Mistral 모델 자동 다운로드
- 모델 설치 상태 확인

#### 6단계: 챗봇 서버 시작
- 모든 초기화 완료 후 서버 시작
- 헬스체크 엔드포인트 활성화

### Docker 명령어

```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f chatbot

# 특정 서비스만 재시작
docker-compose restart chatbot

# 전체 시스템 중지
docker-compose down

# 전체 시스템 재시작
docker-compose restart
```

## 📊 서비스 정보

- **챗봇 서버**: http://localhost:8008
- **API 문서**: http://localhost:8008/docs
- **Ollama 서버**: http://localhost:11434
- **백엔드 서버**: http://localhost:8000
- **프론트엔드**: http://localhost:3000

## 🔍 문제 해결

### 로그 확인
```bash
# 챗봇 로그만 확인
docker-compose logs -f chatbot

# 전체 시스템 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f ollama
docker-compose logs -f backend
```

### 컨테이너 재시작
```bash
# 챗봇만 재시작
docker-compose restart chatbot

# 전체 재시작
docker-compose restart
```

### 완전 초기화
```bash
# 모든 컨테이너와 볼륨 삭제
docker-compose down -v --remove-orphans
docker system prune -f
```

## 📁 프로젝트 구조

```
ollama-LLM-ChatBot/
├── core/                          # 핵심 모듈
│   ├── intent_classifier.py       # 의도 분류기
│   ├── question_analyzer.py       # 질문 분석기
│   ├── dual_pipeline_processor.py # 이중 파이프라인 처리기
│   └── ...
├── data/                          # 데이터
│   ├── intent_training_dataset.json  # 의도 분류 학습 데이터
│   ├── pdfs/                      # PDF 문서
│   └── ...
├── models/                        # 학습된 모델
│   └── intent_classifier_trained.pkl
├── api/                          # API 엔드포인트
├── utils/                        # 유틸리티
└── ...
```

## 🧪 테스트

### 의도 분류기 테스트

```bash
# 기본 테스트
python test_intent_classifier.py

# 학습된 분류기 테스트
python train_intent_classifier.py
```

### 예시 질문

**DB 쿼리 예시:**
- "traffic_volume 테이블에서 최근 데이터를 조회해주세요"
- "교통사고 데이터베이스에서 어제 발생한 사고 건수는?"

**사실 질문 예시:**
- "IFRO 시스템이 무엇인가요?"
- "교통 관제 시스템의 역할은?"

**절차 질문 예시:**
- "IFRO 시스템을 사용하는 방법은?"
- "실시간 교통 정보를 확인하는 방법은?"

## 📈 성능 모니터링

### 분류 통계

시스템은 다음과 같은 통계를 제공합니다:

- **FastText 사용률**: 빠른 필터링 성공률
- **SBERT 사용률**: 정확한 분류 성공률
- **LLM Fallback 사용률**: 복잡한 케이스 처리률
- **평균 처리 시간**: 질문당 처리 시간
- **정확도**: 의도 분류 정확도

### 로그 분석

```bash
# 분류 통계 확인
python -c "
from core.intent_classifier import create_intent_classifier
classifier = create_intent_classifier('traffic')
stats = classifier.get_classification_stats()
print(stats)
"
```