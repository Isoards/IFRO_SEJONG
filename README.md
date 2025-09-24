# 🚦 IFRO_SEJONG - 교통 데이터 분석 및 챗봇 시스템

## 📋 프로젝트 개요

IFRO_SEJONG은 교통 데이터를 분석하고 AI 챗봇을 통해 사용자와 상호작용하는 종합적인 교통 관리 시스템입니다.

## 🏗️ 시스템 아키텍처

```
IFRO_SEJONG/
├── 🐳 docker-compose.yml          # 전체 시스템 오케스트레이션
├── 📚 README.md                   # 프로젝트 문서
├── 🔧 .gitignore                  # Git 무시 파일 설정
├── 🎨 .gitattributes             # Git 속성 설정
├── 🎯 django-react-frontend-ifro/ # React 프론트엔드
├── 🔌 django-react-backend-api-ifro/ # Django 백엔드 API
└── 🤖 ollama-chatbot-api-ifro/ # AI 챗봇 서비스 (FastAPI)
```

## 🚀 빠른 시작

### 1. 시스템 요구사항
- Docker & Docker Compose
- 최소 8GB RAM
- 20GB 이상의 디스크 공간

### 2. 시스템 시작

#### 🚀 전체 시스템 시작
```bash
# 전체 시스템 시작 (CPU 모드)
docker-compose up -d

# GPU 최적화 모드로 시작
docker-compose -f docker-compose.gpu.yml up -d
```

#### 🔧 단계별 시작 (메모리 부족 시)
```bash
# 1단계: 데이터베이스만 시작
docker-compose up -d db

# 2단계: AI 서비스 시작
docker-compose up -d ollama chatbot

# 3단계: 백엔드 시작
docker-compose up -d backend

# 4단계: 프론트엔드 시작
docker-compose up -d frontend
```

#### 📊 시스템 관리
```bash
# 로그 확인
docker-compose logs -f

# 시스템 상태 확인
docker-compose ps

# 서비스 중지
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

### 3. GPU 최적화 (선택사항)

#### 🎯 GPU 지원 확인
```bash
# NVIDIA GPU 확인
nvidia-smi

# Docker GPU 런타임 확인
docker info | grep -i runtime
```

#### ⚡ GPU 최적화 실행
```bash
# GPU 최적화 모드로 시작
docker-compose -f docker-compose.gpu.yml up -d

# GPU 사용량 모니터링
nvidia-smi
```

### 4. 서비스 접속
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **챗봇 API**: http://localhost:8010
- **데이터베이스**: localhost:3307

## 🏛️ 서비스 구성

### 🎯 프론트엔드 (React + TypeScript)
- **위치**: `django-react-frontend-ifro/`
- **기술스택**: React 18, TypeScript, Tailwind CSS
- **주요기능**: 교통 데이터 시각화, 대시보드, 사용자 인터페이스

### 🔌 백엔드 API (Django)
- **위치**: `django-react-backend-api-ifro/`
- **기술스택**: Django 4, Django REST Framework, MySQL
- **주요기능**: 교통 데이터 API, 사용자 인증, 데이터 처리

### 🤖 AI 챗봇 (FastAPI + UnifiedPDF)
- **위치**: `ollama-chatbot-api-ifro/`
- **기술스택**: FastAPI, Python, Sentence Transformers, FAISS
- **주요기능**: PDF 문서 기반 질의응답, 자연어 처리, 대화형 인터페이스

## 🗄️ 데이터베이스

### MySQL 설정
- **포트**: 3307
- **데이터베이스**: traffic
- **문자셋**: UTF-8 (한글 지원)
- **자동 백업**: Docker 볼륨으로 데이터 영속성 보장

## 🔧 개발 환경

### 로컬 개발
```bash
# 백엔드 개발
cd django-react-backend-api-ifro/src
python manage.py runserver

# 프론트엔드 개발
cd django-react-frontend-ifro
npm start

# 챗봇 개발
cd ollama-chatbot-api-ifro
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 환경 변수
주요 환경 변수는 `docker-compose.yml`에 정의되어 있습니다:
- `DJANGO_SECRET_KEY`: Django 보안 키
- `JWT_SECRET_KEY`: JWT 토큰 보안 키
- `GEMINI_API_KEY`: Google Gemini API 키
- `MYSQL_*`: 데이터베이스 연결 정보

## 📊 모니터링 및 로그

### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend
docker-compose logs chatbot

# 실시간 로그
docker-compose logs -f chatbot
```

### 헬스체크
```bash
# 서비스 상태 확인
docker-compose ps

# 챗봇 헬스체크
curl http://localhost:8010/healthz
```

## 🛠️ 유지보수

### 데이터베이스 백업
```bash
# MySQL 데이터 백업
docker exec mysql mysqldump -u root -p1234 traffic > backup.sql

# 볼륨 백업
docker run --rm -v ifro_sejong_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz -C /data .
```

### 시스템 업데이트
```bash
# 이미지 재빌드
docker-compose build --no-cache

# 서비스 재시작
docker-compose up -d --force-recreate
```

## 🐛 문제 해결

### 일반적인 문제들

1. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000
   netstat -tulpn | grep :8008
   ```

2. **메모리 부족**
   ```bash
   # Docker 리소스 제한 확인
   docker stats
   ```

3. **데이터베이스 연결 실패**
   ```bash
   # MySQL 컨테이너 상태 확인
   docker-compose logs db
   ```

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

프로젝트 관련 문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해 주세요.

---

**개발팀**: IFRO_SEJONG Team  
**최종 업데이트**: 2024년 12월  
**버전**: 2.0.0
