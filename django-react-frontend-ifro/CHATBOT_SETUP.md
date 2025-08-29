# 챗봇 설정 가이드

## 환경변수 설정

프론트엔드에서 챗봇 서버 IP를 설정하려면 환경변수를 사용하세요.

### 1. 환경변수 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# ChatBot API Configuration
REACT_APP_CHATBOT_IP=http://localhost:8000

# Backend API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000/api
```

### 2. 환경변수 설명

- `REACT_APP_CHATBOT_IP`: 챗봇 서버의 IP 주소
  - 기본값: `http://localhost:8000`
  - 다른 서버를 사용하는 경우 이 값을 변경하세요

### 3. 서버별 설정 예시

#### 로컬 개발 환경
```env
REACT_APP_CHATBOT_IP=http://localhost:8000
```

#### 원격 서버
```env
REACT_APP_CHATBOT_IP=http://your-server-ip:8000
```

#### HTTPS 서버
```env
REACT_APP_CHATBOT_IP=https://your-domain.com
```

### 4. 환경변수 적용

환경변수를 변경한 후에는 React 앱을 재시작해야 합니다:

```bash
npm start
```

## 백엔드 API 엔드포인트

챗봇 기능을 위한 백엔드 API가 추가되었습니다:

- `POST /api/chat/message`: 일반 사용자용 챗봇 API
- `POST /api/secure/chat/message`: 인증된 사용자용 챗봇 API

## 사용법

1. 환경변수 파일을 생성하고 챗봇 서버 IP를 설정
2. 백엔드 서버가 실행 중인지 확인
3. 프론트엔드 앱을 재시작
4. 대시보드에서 챗봇 버튼을 클릭하여 사용

## 문제 해결

### 챗봇이 응답하지 않는 경우
1. 백엔드 서버가 실행 중인지 확인
2. 환경변수 `REACT_APP_CHATBOT_IP`가 올바른지 확인
3. 네트워크 연결 상태 확인
4. 브라우저 개발자 도구에서 네트워크 오류 확인
