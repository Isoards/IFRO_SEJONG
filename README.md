# IFRO (Intelligent Traffic Flow and Road Operations)
산학연계 뉴노멀 프로젝트 - 지능형 교통 흐름 및 도로 운영 시스템

## 🚀 프로젝트 개요
IFRO는 Django 백엔드와 React 프론트엔드로 구성된 지능형 교통 분석 및 관리 시스템입니다. 실시간 교통 데이터 분석, 교통사고 관리, 교차로 간 통행량 분석 등의 기능을 제공합니다. 또한 PDF QA 챗봇 시스템을 통합하여 문서 기반 질의응답 기능도 제공합니다.

## 📁 프로젝트 구조
```
IFRO/
├── django-react-backend-api-ifro/    # Django 백엔드 API
│   ├── src/
│   │   ├── dashboard/                # Django 프로젝트 설정
│   │   ├── traffic/                  # 교통 데이터 모델 및 API
│   │   ├── user_auth/                # 사용자 인증 및 관리
│   │   └── manage.py
│   ├── requirements.txt
│   └── sqldata-backup/               # 데이터베이스 백업
├── django-react-frontend-ifro/       # React 프론트엔드
│   ├── src/
│   │   ├── components/               # React 컴포넌트
│   │   │   ├── Auth/                 # 인증 관련 컴포넌트
│   │   │   ├── Dashboard/            # 대시보드 메인
│   │   │   ├── Map/                  # 지도 관련 컴포넌트
│   │   │   ├── Navigation/           # 네비게이션 컴포넌트
│   │   │   └── TrafficAnalysis/      # 교통 분석 컴포넌트
│   │   ├── api/                      # API 통신 모듈
│   │   ├── types/                    # TypeScript 타입 정의
│   │   └── utils/                    # 유틸리티 함수
│   └── package.json
├── chatBot_mk.1/                     # PDF QA 챗봇 시스템
│   ├── api/                          # FastAPI 엔드포인트
│   ├── core/                         # 핵심 처리 모듈
│   ├── data/                         # PDF 데이터 및 벡터 저장소
│   ├── utils/                        # 유틸리티 함수
│   ├── main.py                       # 메인 실행 파일
│   ├── run_server.py                 # 서버 실행 스크립트
│   ├── requirements.txt              # Python 의존성
│   └── Dockerfile                    # 챗봇 컨테이너 설정
├── docker-compose.yml                # 전체 서비스 오케스트레이션
├── start_chatbot.sh                  # 챗봇 서비스 시작 스크립트 (Linux/Mac)
├── start_chatbot.ps1                 # 챗봇 서비스 시작 스크립트 (Windows)
└── README.md
```

## 🔐 관리자 코드 시스템

### 개요
IFRO 시스템은 **자동 생성 관리자 코드**를 통해 보안을 강화하고 있습니다.

### 주요 기능
- ✅ **자동 코드 생성**: 설정된 시간마다 자동으로 새로운 코드 생성
- ✅ **사용 즉시 갱신**: 코드 사용 시 즉시 새 코드로 변경
- ✅ **미사용 시 시간 기반 갱신**: 미사용 시 설정된 시간마다 갱신
- ✅ **1회 사용 제한**: 각 코드는 최대 1회만 사용 가능
- ✅ **Django Admin 관리**: 웹 인터페이스에서 편리한 관리

### 관리자 코드 확인 방법

#### 1. Django Admin 페이지 (권장)
```bash
# Django 서버 실행
python manage.py runserver

# 브라우저에서 접속
http://localhost:8000/admin

# user_auth > Admin codes에서 확인
```

#### 2. 명령어로 확인
```bash
# 현재 관리자 코드 목록 확인
python manage.py shell -c "from user_auth.models import AdminCode; codes = AdminCode.objects.all(); [print(f'코드: {code.code} | 설명: {code.description} | 활성: {code.is_active} | 자동생성: {code.auto_generate} | 사용횟수: {code.current_uses}/{code.max_uses}') for code in codes]"
```

### 관리자 코드 생성

#### 1. 자동 생성 코드 생성
```bash
# 12시간마다 갱신되는 자동 생성 코드
python manage.py create_admin_code --auto-generate --interval-hours 12

# 24시간마다 갱신되는 자동 생성 코드
python manage.py create_admin_code --auto-generate --interval-hours 24
```

#### 2. 일반 관리자 코드 생성
```bash
# 수동으로 코드 생성 (5회 사용 가능)
python manage.py create_admin_code --code "MANUAL_CODE" --max-uses 5

# 테스트용 코드 생성
python manage.py create_admin_code --code "TEST123" --description "테스트용 관리자 코드" --max-uses 10
```

### 관리자 코드 삭제

#### 1. Django Admin에서 삭제
- **일반 관리자 코드**: 삭제 가능
- **자동 생성 코드**: 슈퍼유저만 삭제 가능

#### 2. 명령어로 삭제
```bash
# 특정 코드 삭제
python manage.py delete_admin_code --code "CODE_TO_DELETE"

# 자동 생성 코드만 삭제
python manage.py delete_admin_code --auto-generate

# 모든 코드 삭제
python manage.py delete_admin_code --all

# 확인 없이 강제 삭제
python manage.py delete_admin_code --auto-generate --force
```

### 사용자 관리

#### 1. Django Admin에서 관리
- **슈퍼유저만** 사용자 삭제 가능
- **슈퍼유저는 자신을 삭제할 수 없음**

#### 2. 명령어로 사용자 관리
```bash
# 특정 사용자 삭제
python manage.py delete_user --username "username"

# 특정 역할 사용자들 삭제
python manage.py delete_user --role "operator"

# 모든 일반 사용자 삭제 (슈퍼유저 제외)
python manage.py delete_user --all
```

### 프로덕션 환경 설정

#### 1. 슈퍼유저 생성
```bash
# 대화형 슈퍼유저 생성
python manage.py createsuperuser

# 자동 슈퍼유저 생성
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com \
DJANGO_SUPERUSER_PASSWORD=secure_password123 \
python manage.py createsuperuser --noinput
```

#### 2. 프로덕션 환경 자동 설정
```bash
# 슈퍼유저 + 자동 생성 관리자 코드 생성
python manage.py setup_production \
    --superuser-email admin@yourdomain.com \
    --superuser-password secure_password123 \
    --create-auto-admin-code
```

### 보안 특징
- 🔒 **자동 갱신**: 설정된 시간마다 자동으로 새 코드 생성
- 🔒 **Admin 전용**: Django Admin에서만 코드 확인 가능
- 🔒 **수정 방지**: 자동 생성 코드는 수정/삭제 제한
- 🔒 **사용 추적**: 사용 횟수 및 만료일 관리
- 🔒 **안전한 생성**: `secrets` 모듈로 암호학적으로 안전한 코드 생성

### 동작 예시

#### 시나리오 1: 사용 즉시 자동 변경
```
12:00 - 코드: "ABC12345"
12:30 - 사용자가 "ABC12345"로 가입 → 성공
12:30 - 즉시 코드 변경: "ABC12345" → "XYZ78901"
13:00 - 다른 사용자가 "ABC12345"로 가입 시도 → 실패 (코드가 이미 변경됨)
```

#### 시나리오 2: 미사용 시 시간 기반 변경
```
12:00 - 코드: "ABC12345"
18:00 - 아직 사용되지 않음
24:00 - 12시간 경과, 코드 변경: "ABC12345" → "DEF45678"
```

## 🗄️ 데이터베이스 모델

### 교통 데이터 모델
- **Intersection**: 교차로 정보 (이름, 위도, 경도)
- **TrafficVolume**: 교차로별 통행량 데이터 (방향별, 시간별)
- **TotalTrafficVolume**: 교차로별 총 통행량 및 평균 속도
- **Incident**: 교통사고 및 사건 정보

### 사용자 관리 모델
- **User**: 사용자 정보 (역할: operator/admin)
- **AdminCode**: 관리자 코드 시스템

## 🎯 주요 기능

### 프론트엔드 기능
- 🗺️ **Google Maps 통합**: 실시간 지도 표시 및 교차로 마커
- 📊 **교통 분석 대시보드**: 
  - 단순 교차로 뷰
  - 교차로 간 통행량 분석 뷰
  - 교통사고 관리 뷰
- 📈 **실시간 차트**: Recharts를 활용한 교통 데이터 시각화
- 🔍 **검색 및 필터링**: 교차로 및 사고 데이터 검색
- ⭐ **즐겨찾기 기능**: 자주 사용하는 교차로 저장
- 📅 **날짜/시간 선택**: 특정 시점의 교통 데이터 조회
- 🔐 **JWT 인증**: 안전한 사용자 인증 시스템

### 백엔드 기능
- 🔌 **RESTful API**: Django Ninja 기반 고성능 API
- 🔐 **JWT 인증**: 안전한 토큰 기반 인증
- 📊 **데이터 분석**: 교차로 간 통행량 분석
- 🗄️ **데이터베이스 관리**: SQLite (개발) / MySQL (프로덕션)
- 🔄 **자동 코드 관리**: 관리자 코드 자동 생성 및 갱신

## 🛠️ 개발 환경 설정

### 백엔드 (Django)
```bash
cd django-react-backend-api-ifro/src

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r ../requirements.txt

# 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```

### 프론트엔드 (React)
```bash
cd django-react-frontend-ifro

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

## 📝 API 엔드포인트

### 인증 관련
- `POST /api/user_auth/register` - 회원가입 (관리자 코드 필요)
- `POST /api/user_auth/login` - 로그인
- `POST /api/user_auth/refresh` - 토큰 갱신

### 교통 데이터
- `GET /api/traffic/intersections` - 교차로 목록
- `GET /api/traffic/intersections/{id}/traffic-stat` - 교차로별 교통 통계
- `GET /api/traffic/incidents` - 교통사고 목록
- `GET /api/traffic/incidents/{id}` - 교통사고 상세 정보

## 🔧 기술 스택

### Backend
- **Framework**: Django 4.x
- **API**: Django Ninja (FastAPI 스타일)
- **Authentication**: Django Ninja JWT
- **Database**: SQLite (개발), MySQL (프로덕션)
- **Data Processing**: NumPy, Pandas
- **CORS**: django-cors-headers

### Frontend
- **Framework**: React 19.x
- **Language**: TypeScript 4.x
- **Styling**: Tailwind CSS 3.x
- **UI Components**: Radix UI, shadcn/ui
- **Maps**: Google Maps API, Leaflet
- **Charts**: Recharts
- **HTTP Client**: Axios
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router DOM 7.x

### Development Tools
- **Package Manager**: npm
- **Build Tool**: Create React App
- **Code Quality**: ESLint, TypeScript
- **Version Control**: Git

## 🚀 배포

### 환경 변수 설정
```bash
# Backend (.env)
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost/ifro_db
ALLOWED_HOSTS=your-domain.com

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 프로덕션 빌드
```bash
# Frontend 빌드
cd django-react-frontend-ifro
npm run build

# Backend 설정
cd django-react-backend-api-ifro/src
python manage.py collectstatic
python manage.py migrate
```

## 📊 데이터 시각화

### 지원하는 차트 타입
- 📈 **라인 차트**: 시간별 교통량 변화
- 📊 **바 차트**: 교차로별 통행량 비교
- 🥧 **파이 차트**: 방향별 교통량 분포
- 📉 **지역 차트**: 교차로 간 통행량 흐름

### 지도 기능
- 🗺️ **Google Maps**: 고성능 지도 렌더링
- 📍 **교차로 마커**: 클릭 가능한 교차로 표시
- 🚨 **사고 마커**: 교통사고 위치 표시
- 🔗 **연결선**: 교차로 간 통행량 흐름 시각화

## 🤖 PDF QA 챗봇 시스템

### 개요
PDF QA 챗봇 시스템은 문서 기반 질의응답을 제공하는 AI 시스템입니다. Dual Pipeline 아키텍처를 사용하여 문서 검색과 SQL 질의를 통합한 하이브리드 답변을 생성합니다.

### 주요 기능
- 📄 **PDF 문서 처리**: 다양한 PDF 형식 지원
- 🔍 **벡터 검색**: 의미 기반 문서 검색
- 💬 **대화 컨텍스트**: 이전 대화 기반 연속성 유지
- 🗄️ **SQL 생성**: 데이터베이스 스키마 기반 SQL 쿼리 생성
- 🔄 **Dual Pipeline**: 문서 검색 + SQL 질의 통합
- 📊 **평가 시스템**: 답변 품질 자동 평가

### 챗봇 서비스 실행

#### 1. Docker Compose로 전체 서비스 실행
```bash
# 모든 서비스 실행 (백엔드, 프론트엔드, 챗봇)
docker-compose up --build

# 챗봇 서비스만 실행
docker-compose up --build chatbot
```

#### 2. 스크립트로 챗봇 서비스만 실행
```bash
# Linux/Mac
./start_chatbot.sh

# Windows PowerShell
.\start_chatbot.ps1
```

#### 3. 수동으로 챗봇 서비스 실행
```bash
cd chatBot_mk.1
docker build -t chatbot .
docker run -p 8008:8008 chatbot
```

### 챗봇 API 엔드포인트

#### 기본 엔드포인트
- `GET /` - 서버 상태 확인
- `GET /docs` - API 문서 (Swagger UI)
- `GET /health` - 헬스 체크

#### PDF 관련
- `POST /upload-pdf` - PDF 파일 업로드
- `GET /pdfs` - 등록된 PDF 목록
- `DELETE /pdfs/{pdf_id}` - PDF 삭제

#### 질의응답
- `POST /ask` - 질문하기
- `POST /ask-with-context` - 대화 컨텍스트와 함께 질문
- `GET /conversation-history` - 대화 기록 조회

#### 시스템 관리
- `GET /system-status` - 시스템 상태 확인
- `POST /update-model-config` - 모델 설정 변경
- `POST /evaluate-answers` - 답변 품질 평가

### 접속 정보
- **서버 주소**: http://localhost:8008
- **API 문서**: http://localhost:8008/docs
- **헬스 체크**: http://localhost:8008/health

### 환경 변수 설정
```bash
# 챗봇 서비스 환경 변수
MODEL_TYPE=ollama                    # 모델 타입 (ollama/huggingface/llama_cpp)
MODEL_NAME=mistral:latest           # 모델 이름
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask  # 임베딩 모델
```

## 🔒 보안 고려사항

### 인증 및 권한
- JWT 토큰 기반 인증
- 역할 기반 접근 제어 (Operator/Admin)
- 관리자 코드 시스템으로 가입 제한

### 데이터 보안
- HTTPS 통신 강제
- CORS 설정으로 허용된 도메인만 접근
- 민감한 데이터 암호화 저장
