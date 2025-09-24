# RAG 워크플로우 사용 가이드

## 개요

이 가이드는 PDF 파일을 업로드하고 병렬 임베딩을 통해 RAG(Retrieval-Augmented Generation) 시스템을 구축하는 방법을 설명합니다.

## 시스템 요구사항

- Python 3.8+
- FastAPI
- PyTorch
- sentence-transformers
- faiss-cpu 또는 hnswlib
- pdfplumber, PyMuPDF, pymupdf4llm

## 설치된 기능

### 1. PDF 업로드 API
- **엔드포인트**: `POST /api/upload-pdf`
- **기능**: PDF 파일을 `data/pdfs` 폴더에 저장하고 자동으로 임베딩 처리
- **제한사항**: 
  - 파일 크기: 100MB 이하
  - 파일 형식: PDF만 허용

### 2. 병렬 임베딩 처리
- **스크립트**: `scripts/parallel_embedding.py`
- **기능**: 여러 PDF를 동시에 처리하여 임베딩 성능 향상
- **특징**:
  - CPU 멀티코어 활용
  - 메모리 효율적인 배치 처리
  - 벡터 중복 제거 옵션

### 3. 자동화된 워크플로우
- **스크립트**: `scripts/auto_rag_workflow.py`
- **기능**: PDF 업로드부터 RAG 테스트까지 전체 과정 자동화

## 사용 방법

### 방법 1: API를 통한 PDF 업로드

```bash
# 1. 서버 시작
cd ollama-chatbot-api-ifro
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000

# 2. PDF 업로드 (curl 사용)
curl -X POST "http://localhost:8000/api/upload-pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"

# 3. 업로드된 PDF 목록 확인
curl -X GET "http://localhost:8000/api/pdfs"

# 4. 벡터 인덱스 재구축
curl -X POST "http://localhost:8000/api/rebuild-index"
```

### 방법 2: 병렬 임베딩 직접 실행

```bash
# 병렬 임베딩 실행
python scripts/parallel_embedding.py \
    --pdf_dir data/pdfs \
    --output_corpus data/corpus_v1.jsonl \
    --output_index vector_store \
    --backend faiss \
    --max_workers 4 \
    --use_gpu

# 옵션 설명:
# --pdf_dir: PDF 파일이 있는 디렉토리
# --output_corpus: 생성될 코퍼스 파일 경로
# --output_index: 벡터 인덱스 저장 디렉토리
# --backend: 벡터 백엔드 (faiss 또는 hnsw)
# --max_workers: 최대 워커 수
# --use_gpu: GPU 사용 여부
```

### 방법 3: 자동화된 워크플로우 실행

```bash
# 전체 워크플로우 자동 실행
python scripts/auto_rag_workflow.py \
    --server_url http://localhost:8000 \
    --pdf_dir data/pdfs \
    --use_parallel \
    --max_workers 4 \
    --test_questions "교통사고 대응 방법은?" "정수장 운영법은?" \
    --output_report workflow_result.json
```

## 성능 최적화 팁

### 1. 병렬 처리 설정
- **CPU 코어 수**: `--max_workers`를 CPU 코어 수의 50-75%로 설정
- **메모리**: 대용량 PDF의 경우 배치 크기 조정 필요

### 2. 청킹 전략
- **일반 문서**: `--chunk-size 500 --chunk-overlap 100`
- **기술 문서**: `--chunk-size 800 --chunk-overlap 150`
- **표/수치 중심**: `--chunk-size 300 --chunk-overlap 50`

### 3. 벡터 백엔드 선택
- **FAISS**: 빠른 검색, 메모리 효율적
- **HNSW**: 높은 정확도, 더 많은 메모리 사용

## 모니터링 및 디버깅

### 1. 로그 확인
```bash
# 서버 로그
tail -f logs/chatbot_conversations.log

# 상세 질문/답변 로그
tail -f logs/qa_detailed.log

# 대화 기록 (JSON)
tail -f logs/conversations.jsonl
```

### 2. 벡터 인덱스 상태 확인
```bash
# 인덱스 파일 확인
ls -la vector_store/
# - index.faiss (또는 index.hnsw)
# - meta.json
# - mapping.json

# 코퍼스 파일 확인
wc -l data/corpus_v1.jsonl
```

### 3. 성능 테스트
```bash
# RAG 시스템 테스트
python scripts/auto_rag_workflow.py \
    --test_questions "질문1" "질문2" "질문3" \
    --output_report test_result.json
```

## 문제 해결

### 1. 메모리 부족 오류
```bash
# 배치 크기 줄이기
python scripts/parallel_embedding.py --batch_size 16

# 워커 수 줄이기
python scripts/parallel_embedding.py --max_workers 2
```

### 2. PDF 텍스트 추출 실패
```bash
# OCR 활성화
python scripts/build_corpus_from_pdfs.py --ocr always

# 다른 추출기 사용
python scripts/build_corpus_from_pdfs.py --pdf-extractor pymupdf4llm
```

### 3. 임베딩 모델 로드 실패
```bash
# 모델 재다운로드
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

## API 엔드포인트 목록

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/upload-pdf` | POST | PDF 파일 업로드 |
| `/api/pdfs` | GET | 업로드된 PDF 목록 조회 |
| `/api/pdfs/{filename}` | DELETE | PDF 파일 삭제 |
| `/api/rebuild-index` | POST | 벡터 인덱스 재구축 |
| `/api/ask` | POST | RAG 질문/답변 |
| `/healthz` | GET | 서버 상태 확인 |

## 예제 사용 시나리오

### 시나리오 1: 새로운 문서 추가
```bash
# 1. PDF 업로드
curl -X POST "http://localhost:8000/api/upload-pdf" -F "file=@new_document.pdf"

# 2. 자동으로 임베딩 처리됨 (백그라운드)

# 3. 서버 재시작 (벡터 인덱스 로드)
# Ctrl+C로 서버 중지 후 재시작

# 4. 테스트
curl -X POST "http://localhost:8000/api/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "새 문서에 대한 질문", "mode": "accuracy"}'
```

### 시나리오 2: 대량 문서 처리
```bash
# 1. 모든 PDF를 data/pdfs에 복사
cp /path/to/documents/*.pdf data/pdfs/

# 2. 병렬 임베딩 실행
python scripts/parallel_embedding.py --use_gpu --max_workers 8

# 3. 서버 재시작

# 4. 성능 테스트
python scripts/auto_rag_workflow.py --use_parallel --test_questions "질문1" "질문2"
```

## 성능 벤치마크

### 처리 속도 (참고)
- **PDF 텍스트 추출**: ~1-5초/페이지
- **청킹**: ~0.1초/문서
- **임베딩**: ~0.5-2초/청크 (GPU 사용 시)
- **벡터 인덱스 구축**: ~1-10초 (문서 수에 따라)

### 메모리 사용량 (참고)
- **기본 설정**: ~2-4GB RAM
- **대용량 처리**: ~8-16GB RAM
- **GPU 사용**: +2-4GB VRAM

## 주의사항

1. **서버 재시작**: 벡터 인덱스 업데이트 후 반드시 서버 재시작 필요
2. **파일 권한**: `data/` 디렉토리에 쓰기 권한 필요
3. **디스크 공간**: 벡터 인덱스는 원본 문서 크기의 10-20% 추가 공간 필요
4. **네트워크**: 대용량 파일 업로드 시 네트워크 타임아웃 주의

## 지원 및 문의

문제가 발생하거나 추가 기능이 필요한 경우:
1. 로그 파일 확인
2. 시스템 요구사항 재확인
3. 메모리/디스크 공간 확인
4. 네트워크 연결 상태 확인
