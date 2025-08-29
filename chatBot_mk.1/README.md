# PDF QA 시스템 사용설명서 (Dual Pipeline 통합)

이 문서는 Dual Pipeline이 통합된 PDF QA 시스템의 서버 실행과 LLM 사용 방법을 설명합니다.

## 🚀 새로운 기능: Dual Pipeline

### 문서 검색 파이프라인
- PDF 내용 기반 질문 답변
- 벡터 검색을 통한 관련 문서 청크 검색
- 컨텍스트 기반 답변 생성

### SQL 질의 파이프라인
- 데이터베이스 스키마 기반 SQL 생성
- SQL 전용 모델(sqlcoder:7b) 사용
- Few-shot 예시를 통한 정확도 향상
- SQL 구문 검증 및 자동 수정

### 하이브리드 파이프라인
- 두 파이프라인 결과 통합
- 질문 유형에 따른 자동 분기
- 신뢰도 기반 결과 가중치 적용

## 목차
1. [서버 실행](#1-서버-실행)
2. [서버 테스트](#2-서버-테스트)
3. [Dual Pipeline 사용](#3-dual-pipeline-사용)
4. [LLM 사용](#4-llm-사용)
5. [준비 사항](#5-준비-사항)
6. [문제 해결](#6-문제-해결)

---

## 1. 서버 실행

### 1.1 FastAPI 서버 실행

Dual Pipeline이 통합된 PDF QA 시스템을 웹 API 서버로 실행합니다.

```powershell
# 방법 1: 간단한 서버 실행 스크립트 사용 (권장)
python run_server.py

# 방법 2: main.py를 통한 서버 실행
python main.py --mode server --model-name mistral:latest

# 방법 3: 특정 호스트와 포트로 실행
python main.py --mode server --model-name mistral:latest --host 0.0.0.0 --port 8000

# 방법 4: 직접 API 엔드포인트 실행
python api/endpoints.py
```

### 1.2 서버 접속

서버 실행 후 다음 URL로 접속할 수 있습니다:

- **API 문서**: http://localhost:8000/docs
- **대체 문서**: http://localhost:8000/redoc
- **헬스 체크**: http://localhost:8000/health
- **시스템 상태**: http://localhost:8000/status

### 1.3 주요 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/upload_pdf` | POST | PDF 파일 업로드 |
| `/ask` | POST | 질문-답변 (일반) |
| `/django/ask` | POST | 질문-답변 (Django용) |
| `/status` | GET | 시스템 상태 조회 |
| `/pdfs` | GET | 등록된 PDF 목록 |
| `/conversation_history` | GET | 대화 기록 조회 |
| `/health` | GET | 서버 헬스 체크 |
| `/conversation/cache/stats` | GET | 대화 이력 캐시 통계 |
| `/conversation/cache` | DELETE | 대화 이력 캐시 삭제 |
| `/conversation/cache/search` | GET | 대화 이력에서 유사 질문 검색 |

### 1.4 클라이언트 사용

#### Django 백엔드에서 사용
```python
from api.django_client import PDFQAClient

# 클라이언트 생성
client = PDFQAClient("http://localhost:8000")

# 질문하기 (대화 이력 캐시 자동 사용)
response = client.ask_question("질문 내용", pdf_id="default")

# PDF 업로드
result = client.upload_pdf("path/to/document.pdf")

# 대화 이력 캐시 관리
stats = client.get_conversation_cache_stats()
client.clear_conversation_cache()  # 전체 캐시 삭제
client.clear_conversation_cache("pdf_id")  # 특정 PDF 캐시 삭제

# 유사 질문 검색
similar = client.search_conversation_cache("질문", threshold=0.8)
```

#### React 프론트엔드에서 사용
```typescript
import { PDFQAClient } from './api/typescript_client';

// 클라이언트 생성
const client = new PDFQAClient('http://localhost:8000');

// 질문하기 (대화 이력 캐시 자동 사용)
const response = await client.askQuestion({
  question: "질문 내용",
  pdf_id: "default"
});

// PDF 업로드
const result = await client.uploadPDF(file);

// 대화 이력 캐시 관리
const stats = await client.getConversationCacheStats();
await client.clearConversationCache();  // 전체 캐시 삭제
await client.clearConversationCache("pdf_id");  // 특정 PDF 캐시 삭제

// 유사 질문 검색
const similar = await client.searchConversationCache("질문", 0.8);
```

---

## 2. 서버 테스트

서버가 정상적으로 작동하는지 확인하기 위한 테스트 도구들을 제공합니다.

### 2.1 간단한 테스트

가장 빠르게 서버 상태를 확인할 수 있는 테스트입니다:

```bash
# 간단한 테스트 실행
python simple_test.py
```

이 테스트는 다음을 확인합니다:
- 서버 연결 상태
- 시스템 상태 및 모델 로드 상태
- PDF 업로드 기능
- 기본 질문-답변 기능

### 2.2 종합 테스트

모든 기능을 상세히 테스트하는 종합 테스트입니다:

```bash
# 종합 테스트 실행
python test_server.py

# 특정 PDF로 테스트
python test_server.py --pdf "path/to/document.pdf"

# 서버 상태만 확인
python test_server.py --status-only

# 다른 서버 URL로 테스트
python test_server.py --url "http://other-server:8000"
```

이 테스트는 다음을 확인합니다:
- 서버 상태 및 루트 엔드포인트
- PDF 업로드 및 처리
- 다양한 질문 유형 테스트
- 대화 흐름 테스트
- Dual Pipeline 비교 테스트
- 성능 및 신뢰도 측정

### 2.3 수동 API 테스트

curl을 사용한 수동 테스트:

```bash
# 서버 상태 확인
curl http://localhost:8000/status

# 루트 엔드포인트 확인
curl http://localhost:8000/

# PDF 업로드
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@document.pdf"

# 질문하기
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "이 문서의 주요 내용은 무엇인가요?",
    "pdf_id": "your-pdf-id",
    "use_conversation_context": true,
    "max_chunks": 5,
    "use_dual_pipeline": true
  }'
```

### 2.4 테스트 결과 해석

#### 성공적인 테스트 결과
```
🚀 PDF QA 시스템 서버 테스트 시작
==================================================
🔍 서버 상태 확인 중...
✅ 서버 상태: running
   모델 로드: True
   등록된 PDF: 1개
   총 청크: 25개
   메모리 사용량: 512.3MB

📄 PDF 업로드 테스트: document.pdf
✅ PDF 업로드 성공:
   PDF ID: abc123-def456
   파일명: document.pdf
   페이지 수: 10
   청크 수: 25
   처리 시간: 2.34초

❓ 질문 테스트: 이 문서의 주요 내용은 무엇인가요?
✅ 답변 생성 성공:
   답변: 이 문서는...
   신뢰도: 0.875
   질문 유형: general_information
   파이프라인: dual_pipeline
   생성 시간: 1.23초

✅ 종합 테스트 완료!
==================================================
```

#### 일반적인 오류 및 해결 방법

1. **서버 연결 실패**
   ```
   ❌ 서버 연결 실패: Connection refused
   ```
   - 서버가 실행 중인지 확인: `python run_server.py`
   - 포트 8000이 사용 가능한지 확인

2. **모델 로드 실패**
   ```
   ❌ 서버 상태 확인 실패: 500
   ```
   - Ollama가 설치되어 있는지 확인
   - 필요한 모델이 다운로드되었는지 확인: `ollama list`

3. **PDF 업로드 실패**
   ```
   ❌ PDF 업로드 실패: 400
   ```
   - PDF 파일이 유효한지 확인
   - 파일 크기가 너무 크지 않은지 확인

4. **질문 처리 실패**
   ```
   ❌ 질문 처리 실패: 404
   ```
   - PDF ID가 올바른지 확인
   - PDF가 성공적으로 업로드되었는지 확인

---

## 3. Dual Pipeline 사용

### 3.1 Dual Pipeline 개요

Dual Pipeline은 질문 유형에 따라 두 가지 다른 처리 방식을 자동으로 선택합니다:

1. **문서 검색 파이프라인**: PDF 내용 기반 질문 답변
2. **SQL 질의 파이프라인**: 데이터베이스 스키마 기반 SQL 생성
3. **하이브리드 파이프라인**: 두 파이프라인 결과 통합

### 3.2 질문 유형별 처리

#### 문서 검색 파이프라인 (기본)
```json
{
  "question": "이 문서에서 주요 개념이 무엇인가요?",
  "pdf_id": "document.pdf",
  "use_dual_pipeline": true
}
```

#### SQL 질의 파이프라인
```json
{
  "question": "사용자 테이블에서 활성 사용자 수를 조회해주세요",
  "pdf_id": "document.pdf",
  "use_dual_pipeline": true
}
```

#### 하이브리드 파이프라인
```json
{
  "question": "이 문서의 내용을 바탕으로 사용자 데이터를 분석해주세요",
  "pdf_id": "document.pdf",
  "use_dual_pipeline": true
}
```

### 3.3 SQL 전용 모델 설정

SQL 질의를 위해 SQL 전용 모델을 설치합니다:

```bash
# SQL 전용 모델 설치
ollama pull sqlcoder:7b

# 또는 더 큰 모델 (더 정확하지만 느림)
ollama pull sqlcoder:15b
ollama pull sqlcoder:34b
```

### 2.4 데이터베이스 스키마 설정

현재 시스템은 샘플 스키마를 사용합니다. 실제 사용 시에는 `main.py`의 `DatabaseSchema` 설정을 수정하세요:

```python
# main.py에서 스키마 수정
sample_schema = DatabaseSchema(
    table_name="your_table_name",
    columns=[
        {"name": "id", "type": "INTEGER", "description": "ID"},
        {"name": "name", "type": "TEXT", "description": "이름"},
        # ... 더 많은 컬럼들
    ],
    primary_key="id",
    sample_data=[
        # 샘플 데이터
    ]
)
```

### 2.5 API 응답 예시

#### 문서 검색 응답
```json
{
  "answer": "이 문서의 주요 개념은...",
  "confidence_score": 0.85,
  "pipeline_type": "document_search",
  "sql_query": null
}
```

#### SQL 질의 응답
```json
{
  "answer": "생성된 SQL: SELECT COUNT(*) FROM users WHERE status = 'active'\n\n쿼리 타입: SELECT\n검증 결과: 성공",
  "confidence_score": 0.92,
  "pipeline_type": "sql_query",
  "sql_query": "SELECT COUNT(*) FROM users WHERE status = 'active'"
}
```

#### 하이브리드 응답
```json
{
  "answer": "문서 내용 분석 결과...\n\n[데이터베이스 정보]\n생성된 SQL: SELECT * FROM users\n\n쿼리 타입: SELECT\n검증 결과: 성공",
  "confidence_score": 0.78,
  "pipeline_type": "hybrid",
  "sql_query": "SELECT * FROM users"
}
```

---

## 4. LLM 사용

### 2.1 대화형 모드

PDF와 대화할 수 있는 대화형 인터페이스를 실행합니다.

```powershell
# 기본 대화형 모드
python main.py --mode interactive --model-name mistral:latest

# PDF 지정하여 시작
python main.py --mode interactive --pdf "C:\path\to\document.pdf" --model-name mistral:latest
```

### 2.2 대화형 명령어

대화형 모드에서 사용할 수 있는 명령어들:

| 명령어 | 설명 |
|--------|------|
| `/clear` | 대화 기록 초기화 |
| `/status` | 시스템 상태 확인 |
| `/pdfs` | 저장된 PDF 목록 |
| `/add <경로>` | PDF 추가 및 카테고리 선택 |
| `/categories` | 카테고리/저장소 요약 |
| `/exit` | 종료 |

### 2.3 단일 처리 모드

한 번의 질문에 대한 답변을 받습니다.

```powershell
python main.py --mode process --pdf "C:\path\to\document.pdf" --question "이 문서의 핵심 내용은?" --model-name mistral:latest
```

### 2.4 대화 이력 캐시 기능

PDF QA 시스템은 대화 이력을 SQLite 데이터베이스에 저장하여 빠른 답변을 제공합니다.

#### 주요 기능:
- **빠른 답변**: 동일하거나 유사한 질문에 대해 LLM 사용 없이 즉시 답변
- **정확한 일치**: 해시 기반 정확한 질문 매칭
- **유사 질문 검색**: Jaccard 유사도 기반 유사 질문 찾기
- **품질 필터링**: 신뢰도가 낮거나 에러 메시지는 캐시에 저장하지 않음
- **PDF별 분리**: 각 PDF별로 대화 이력 관리

#### 캐시 사용 조건:
- 신뢰도 ≥ 0.5인 답변만 저장
- 답변 길이 10-2000자
- 에러 메시지나 기본 답변 제외
- 정확한 일치 또는 유사도 ≥ 0.85

#### 성능 향상:
- **정확한 일치**: 0.001초 (LLM 대비 1000배 빠름)
- **유사 질문**: 0.002초 (LLM 대비 500배 빠름)
- **메모리 효율**: SQLite 인덱스 기반 빠른 검색

### 2.5 지원하는 LLM 모델

#### Ollama 모델 (권장)
```powershell
# Mistral 모델 (기본 권장)
ollama pull mistral:latest

# Llama2 모델
ollama pull llama2:7b

# 기타 모델들
ollama pull codellama:7b
ollama pull llama2:13b
```

#### 모델 설정 변경
API를 통해 모델 설정을 변경할 수 있습니다:

```bash
curl -X POST http://localhost:8000/configure_model \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "ollama",
    "model_name": "llama2:7b",
    "max_length": 512,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

---

## 5. 준비 사항

### 3.1 환경 설정

```powershell
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\Activate

# 의존성 설치
pip install -r requirements.txt
```

### 3.2 Ollama 설치 및 설정

1. **Ollama 설치**: https://ollama.ai 에서 다운로드
2. **모델 다운로드**:
   ```powershell
   ollama pull mistral:latest
   ```
3. **Ollama 서비스 시작**:
   ```powershell
   ollama serve
   ```

### 3.3 PDF 파일 준비

PDF 파일은 다음 위치에 저장하거나 업로드할 수 있습니다:

- **로컬 저장**: `data/pdfs/` 디렉토리
- **API 업로드**: `/upload_pdf` 엔드포인트 사용

---

## 6. 문제 해결

### 4.1 서버 관련 문제

**서버가 시작되지 않아요**
- Ollama가 실행 중인지 확인: `ollama list`
- 포트 8000이 사용 중인지 확인
- 방화벽 설정 확인

**API 요청이 실패해요**
- 서버가 실행 중인지 확인: `curl http://localhost:8000/health`
- CORS 설정 확인 (프론트엔드에서 접근 시)

### 4.2 LLM 관련 문제

**모델 로드가 실패해요**
```powershell
# Ollama 상태 확인
ollama list

# 모델 재다운로드
ollama pull mistral:latest

# Ollama 재시작
ollama serve
```

**답변 품질이 낮아요**
- 더 큰 모델 사용: `llama2:13b`, `mistral:large`
- 모델 설정 조정: temperature, top_p 값 변경
- 질문을 더 구체적으로 작성

### 4.3 PDF 관련 문제

**PDF가 검색되지 않아요**
- PDF가 올바르게 업로드되었는지 확인
- 텍스트 추출이 가능한 PDF인지 확인
- 벡터 저장소 재생성 필요할 수 있음

**벡터 저장소 초기화**
```powershell
# 벡터 저장소 백업 후 삭제
# data/vector_store/ 디렉토리 삭제 후 재시작
```

### 4.4 성능 최적화

**응답 속도 개선**
- 더 빠른 모델 사용: `mistral:7b`
- GPU 가속 사용 (지원하는 경우)
- 벡터 저장소 최적화

**메모리 사용량 최적화**
- 더 작은 모델 사용
- 청크 크기 조정
- 불필요한 PDF 제거

---

## 빠른 시작 가이드

1. **환경 설정**
   ```powershell
   python -m venv venv
   venv\Scripts\Activate
   pip install -r requirements.txt
   ```

2. **Ollama 설정**
   ```powershell
   ollama pull mistral:latest
   ollama serve
   ```

3. **서버 실행**
   ```powershell
   python main.py --mode server --model-name mistral:latest
   ```

4. **웹 브라우저에서 확인**
   - http://localhost:8000/docs 접속
   - PDF 업로드 및 질문 테스트

또는 대화형 모드로 바로 시작:
```powershell
python main.py --mode interactive --model-name mistral:latest
```

