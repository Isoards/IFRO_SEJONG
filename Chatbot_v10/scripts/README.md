# 🔧 Chatbot v10 스크립트 모음

이 폴더에는 Chatbot v10을 관리하기 위한 실행 스크립트들이 있습니다.

## 📁 스크립트 목록

| 스크립트 | 설명 |
|----------|------|
| `reset_ontology.cmd` | **전체 초기화** (DB, 벡터, 모든 학습기록 삭제) |
| `reset_user_data.cmd` | **사용자 데이터만 초기화** (도메인 지식 유지) |
| `train.cmd` | 학습 실행 (Docker 컨테이너 재시작) |
| `train_local.cmd` | 🆕 **로컬 학습** (Docker 없이 venv로 직접 실행) |
| `show_logs.cmd` | 컨테이너 로그 실시간 확인 |
| `check_status.cmd` | 학습 상태 및 API 상태 확인 |

## 🐳 Docker vs 로컬 환경

| 환경 | 학습 스크립트 | 설명 |
|------|--------------|------|
| **Docker** | `train.cmd` | Docker 컨테이너 내에서 학습 |
| **로컬** | `train_local.cmd` | Python venv로 직접 학습 (Ollama 필요) |

### 로컬 환경 사전 요구사항
1. Python 가상환경 설정 완료 (`venv\`)
2. Ollama 실행 중 (http://localhost:11434)

## 📂 데이터 폴더 구조

```
data/
├── domain/          # 🏢 도메인 지식 (기본, 우선 학습)
├── user/            # 👤 사용자 전용 데이터 (개인화, 이후 학습)
└── .ingested_files  # 📋 학습 기록
```

## 🚀 사용 시나리오

### 1. 처음 시작하기

```
1. data/domain/ 에 도메인 지식 파일 추가
2. data/user/ 에 사용자 데이터 파일 추가 (선택)
3. train.cmd 실행
4. show_logs.cmd 로 진행 확인
```

### 2. 사용자 데이터만 변경하기

도메인 지식은 유지하고 사용자 데이터만 재학습:

```
1. reset_user_data.cmd 실행
2. data/user/ 에 새 데이터 추가
3. train.cmd 실행
```

### 3. 전체 재학습

모든 데이터 초기화 후 재학습:

```
1. reset_ontology.cmd 실행
2. data/domain/, data/user/ 에 데이터 추가
3. train.cmd 실행
```

### 4. 상태 확인

```
check_status.cmd 실행
```

## 📋 학습 순서

1. **domain/** 폴더 먼저 학습 (기본 지식)
2. **user/** 폴더 이후 학습 (개인화)

## 📄 지원 파일 형식

- `.txt` - 일반 텍스트
- `.md` - 마크다운 문서  
- `.pdf` - PDF 문서
