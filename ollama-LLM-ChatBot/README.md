# 🤖 IFRO_SEJONG AI 챗봇 시스템

## 📋 프로젝트 개요

IFRO_SEJONG AI 챗봇 시스템은 교통 데이터 분석과 PDF 문서 처리를 위한 지능형 대화형 AI 시스템입니다. Dual Pipeline 아키텍처를 통해 문서 검색과 SQL 질의를 통합한 하이브리드 답변을 생성합니다.

## 🏗️ 시스템 아키텍처

```
ollama-LLM-ChatBot/
├── 🚀 run_server.py              # 메인 서버 실행 파일
├── 🐳 Dockerfile                 # Docker 컨테이너 설정
├── 🔧 docker-entrypoint.sh       # Docker 초기화 스크립트
├── 📦 requirements.txt            # Python 의존성
├── 📚 README.md                  # 프로젝트 문서
├── 🔒 .dockerignore              # Docker 빌드 제외 파일
├── 🧠 core/                      # 핵심 처리 모듈
│   ├── __init__.py
│   ├── cache/                    # 캐싱 시스템
│   ├── database/                 # 데이터베이스 처리
│   ├── document/                 # 문서 처리
│   ├── llm/                      # LLM 통합
│   ├── movement/                 # 데이터 이동 처리
│   └── query/                    # 질의 처리
├── 🌐 api/                       # API 엔드포인트
│   ├── __init__.py
│   ├── endpoints.py              # FastAPI 엔드포인트
│   ├── django_client.py          # Django 연동 클라이언트
│   └── typescript_client.ts      # TypeScript 클라이언트
├── 📊 data/                      # 데이터 및 벡터 저장소
│   ├── pdfs/                     # PDF 문서 저장소
│   ├── conversation_history.db    # 대화 기록 데이터베이스
│   └── intent_training_dataset.json # 의도 분석 데이터셋
├── 🗄️ vector_store/              # 벡터 저장소
│   ├── chroma/                   # ChromaDB 벡터 저장소
│   └── faiss/                    # FAISS 벡터 저장소
├── 🤖 models/                    # AI 모델 저장소
├── 📝 logs/                      # 시스템 로그
└── 🧪 setup_sbert.py             # SBERT 모델 설정
```

## 🚀 빠른 시작

### 1. Docker를 통한 실행 (권장)

```bash
# 전체 시스템과 함께 실행
cd ../
docker-compose up -d chatbot

# 챗봇만 독립 실행
docker build -t ifro-chatbot .
docker run -p 8008:8008 ifro-chatbot
```

### 2. 로컬 개발 환경

```bash
# 의존성 설치
pip install -r requirements.txt

# SBERT 모델 설정
python setup_sbert.py

# 서버 실행
python run_server.py
```

### 3. 서비스 접속

- **API 서버**: http://localhost:8008
- **API 문서**: http://localhost:8008/docs
- **헬스체크**: http://localhost:8008/health

## 🏛️ 핵심 기능

### 📄 PDF 문서 처리
- **다양한 형식 지원**: PyPDF2, PyMuPDF, pdfplumber 통합
- **자동 텍스트 추출**: 구조화된 텍스트 및 메타데이터 추출
- **벡터 임베딩**: Sentence Transformers 기반 의미 분석

### 🔍 지능형 검색
- **하이브리드 검색**: 키워드 + 의미 기반 검색
- **벡터 저장소**: ChromaDB와 FAISS 통합
- **실시간 인덱싱**: 문서 업로드 시 자동 벡터화

### 💬 대화형 인터페이스
- **컨텍스트 유지**: 이전 대화 기반 연속성
- **의도 분석**: 질문 유형 자동 분류
- **개인화**: 사용자별 대화 기록 관리

### 🗄️ SQL 데이터 통합
- **자동 SQL 생성**: 자연어를 SQL로 변환
- **스키마 인식**: 데이터베이스 구조 자동 파악
- **실시간 실행**: 생성된 SQL 즉시 실행

## 🔧 API 엔드포인트

### 📋 기본 엔드포인트
- `GET /` - 서버 상태 확인
- `GET /docs` - Swagger UI API 문서
- `GET /health` - 헬스 체크

### 📄 PDF 관리
- `POST /upload-pdf` - PDF 파일 업로드
- `GET /pdfs` - 등록된 PDF 목록
- `DELETE /pdfs/{pdf_id}` - PDF 삭제

### 💬 질의응답
- `POST /ask` - 일반 질문
- `POST /ask-with-context` - 컨텍스트 기반 질문
- `GET /conversation-history` - 대화 기록

### 🗄️ 데이터베이스
- `POST /sql-query` - SQL 질의 실행
- `GET /database-schema` - 데이터베이스 스키마
- `POST /analyze-data` - 데이터 분석 요청

## ⚙️ 환경 변수

```bash
# 모델 설정
MODEL_TYPE=local                    # local/ollama/huggingface
MODEL_NAME=koelectra-small-v3      # 사용할 모델명
EMBEDDING_MODEL=ko-sroberta        # 임베딩 모델

# 데이터베이스 설정
MYSQL_DATABASE=traffic
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_HOST=db
MYSQL_PORT=3306

# 시스템 설정
PYTHONPATH=/app
```

## 🧠 AI 모델

### 지원하는 모델 타입

1. **로컬 모델 (권장)**
   - **KoElectra**: 한국어 텍스트 분류 및 분석
   - **Ko-SRoBERTa**: 한국어 의미 임베딩
   - **장점**: 빠른 응답, 오프라인 작동, 데이터 보안

2. **Ollama 모델**
   - **qwen2:1.5b**: 범용 질의응답
   - **sqlcoder:7b**: SQL 생성 특화
   - **장점**: 높은 품질, 다양한 모델 지원

3. **Hugging Face 모델**
   - **장점**: 최신 모델, 커스터마이징 가능
   - **단점**: 높은 리소스 요구사항

## 📊 성능 최적화

### 응답 시간
- **캐시된 질문**: 0.1-0.5초
- **일반 질문**: 1-3초
- **복잡한 분석**: 5-10초

### 메모리 사용량
- **기본 시스템**: 2-3GB RAM
- **모델 로딩**: 1-2GB RAM
- **벡터 저장소**: 0.5-1GB RAM

### 스토리지 요구사항
- **시스템**: 2-3GB
- **모델**: 3-5GB
- **데이터**: 사용량에 따라 증가

## 🛠️ 개발 가이드

### 모듈 구조

#### Core 모듈
- **`cache/`**: 인메모리 및 영구 캐싱
- **`database/`**: MySQL 연결 및 쿼리 실행
- **`document/`**: PDF 처리 및 텍스트 분석
- **`llm/`**: AI 모델 통합 및 관리
- **`query/`**: 질의 처리 및 라우팅

#### API 모듈
- **`endpoints.py`**: FastAPI 엔드포인트 정의
- **`django_client.py`**: Django 백엔드 연동
- **`typescript_client.ts`**: 프론트엔드 연동

### 확장 방법

1. **새로운 모델 추가**
   ```python
   # core/llm/에 새 모델 클래스 생성
   class NewModel(LLMInterface):
       def generate_response(self, prompt: str) -> str:
           # 구현
           pass
   ```

2. **새로운 검색 방법 추가**
   ```python
   # core/query/에 새 검색 클래스 생성
   class NewSearch(SearchInterface):
       def search(self, query: str) -> List[Document]:
           # 구현
           pass
   ```

## 🐛 문제 해결

### 일반적인 문제들

1. **모델 로딩 실패**
   ```bash
   # 모델 다운로드 확인
   python setup_sbert.py
   
   # 캐시 정리
   rm -rf ~/.cache/huggingface/
   ```

2. **메모리 부족**
   ```bash
   # Docker 메모리 제한 확인
   docker stats chatbot
   
   # 시스템 메모리 확인
   free -h
   ```

3. **벡터 저장소 오류**
   ```bash
   # ChromaDB 재설정
   rm -rf vector_store/chroma/
   python run_server.py
   ```

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f chatbot

# 특정 시간 로그
docker-compose logs --since="2024-01-01T00:00:00" chatbot

# 로그 파일 직접 확인
tail -f logs/chatbot_detailed.log
```

## 📈 모니터링

### 헬스체크
```bash
# 서비스 상태 확인
curl http://localhost:8008/health

# 상세 상태 확인
curl http://localhost:8008/system-status
```

### 성능 메트릭
- **응답 시간**: 평균, 95th percentile
- **처리량**: 초당 요청 수
- **오류율**: 실패한 요청 비율
- **리소스 사용량**: CPU, 메모리, 디스크

## 🔒 보안 고려사항

### 데이터 보안
- **로컬 처리**: 민감한 데이터는 로컬에서만 처리
- **암호화**: 전송 및 저장 시 데이터 암호화
- **접근 제어**: API 키 기반 인증

### 모델 보안
- **신뢰할 수 있는 모델**: 검증된 오픈소스 모델만 사용
- **정기 업데이트**: 보안 패치 및 모델 업데이트
- **취약점 스캔**: 정기적인 보안 검사

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **문서**: `/docs` 폴더의 상세 문서
- **로그**: `logs/` 폴더의 시스템 로그

---

**개발팀**: IFRO_SEJONG Team  
**최종 업데이트**: 2024년 12월  
**버전**: 2.0.0