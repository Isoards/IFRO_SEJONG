# 변경사항 로그 (CHANGELOG)

이 파일은 프로젝트의 주요 변경사항을 추적합니다.

## [2024-12-19] - 프로젝트 구조 정리

### 변경된 파일들
- **파일명 변경**: `vector_store_new/` → `vector_store/` (기존 vector_store 삭제)
- **파일명 변경**: `data/corpus_new.jsonl` → `data/corpus_v1.jsonl`
- **파일명 변경**: `data/corpus_new.jsonl.bak` → `data/corpus_v1.jsonl.bak`

### 변경 이유
- 새로운 PDF 처리 방식으로 생성된 벡터 DB를 메인으로 사용
- 버전 관리 체계 도입 (v1, v2, ...)
- 프로젝트 구조 단순화

### 영향받는 코드
- 모든 스크립트에서 기본 경로가 업데이트됨
- `vector_store` 디렉토리가 새로운 FAISS 기반 인덱스로 교체됨
- `corpus_v1.jsonl`이 새로운 기본 코퍼스 파일로 설정됨

### 수정된 파일 목록
- `scripts/manual_cli.py`: 기본 corpus 경로를 corpus_v1.jsonl로 변경
- `scripts/run_qa_benchmark.py`: 기본 corpus 경로를 corpus_v1.jsonl로 변경
- `scripts/build_vector_index.py`: 기본 corpus 경로를 corpus_v1.jsonl로 변경
- `scripts/autorun.py`: 모든 corpus 참조를 corpus_v1.jsonl로 변경
- `scripts/build_corpus_from_pdfs.py`: 기본 출력 경로를 corpus_v1.jsonl로 변경
- `scripts/convert_corpus_to_txt.py`: 입력 경로를 corpus_v1.jsonl로 변경
- `server/app.py`: corpus 경로를 corpus_v1.jsonl로 변경
- `README.md`: 문서의 모든 예제 경로를 corpus_v1.jsonl로 업데이트
- `튜토리얼.md`: 튜토리얼의 모든 예제 경로를 corpus_v1.jsonl로 업데이트

### 다음 버전 계획
- 향후 변경사항이 있을 때마다 `corpus_v2.jsonl`, `corpus_v3.jsonl` 등으로 버전 관리
- 각 버전별 변경사항을 이 파일에 기록

---
*이 파일은 프로젝트의 모든 주요 변경사항을 추적하기 위해 생성되었습니다.*
