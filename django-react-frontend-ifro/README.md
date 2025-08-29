# IFRO Frontend (React + TypeScript)

교통 대시보드/분석 서비스의 프론트엔드 프로젝트입니다.  
React, TypeScript, Tailwind, shadcn UI, axios 등 최신 스택을 사용합니다.

---

## 주요 기능

- **JWT 인증**: axios 인스턴스에서 토큰 자동 첨부
- **회원가입/로그인**: shadcn 스타일, 영어 UI, 클라이언트 검증
- **라우팅 가드**: 로그인하지 않으면 `/login`만 접근 가능(PrivateRoute)
- **지도 기반 대시보드**: 구역별 상세보기, 해석 패널, 즐겨찾기 등
- **UI/UX**: shadcn UI, Tailwind, 반응형 디자인
- **데이터 요청**: `/api/traffic/` baseURL, incidents/intersections 등 엔드포인트

---

## 프로젝트 구조

```
src/
  ├─ api/               # axios 인스턴스, API 함수
  ├─ components/        # UI 컴포넌트(로그인, 대시보드, 지도 등)
  ├─ types/             # 글로벌 타입 정의
  ├─ utils/             # 유틸 함수
  ├─ App.tsx            # 라우팅/앱 진입점
  └─ index.tsx
public/
  ├─ road-segments.json # 지도 데이터 예시
  └─ ...
```

---

## 실행 방법

1. **의존성 설치**
   ```sh
   npm install
   ```

2. **개발 서버 실행**
   ```sh
   npm start
   ```
   또는
   ```sh
   yarn start
   ```

3. **빌드**
   ```sh
   npm run build
   ```

---

## 주요 설정

- **API baseURL**: `/api/traffic/`
- **JWT 저장 위치**: localStorage
- **로그아웃**: NavBar 하단 User 아이콘 → Logout
- **캘린더 z-index**: 항상 최상단 표시

---

## 개발/배포 팁

- 환경변수(`.env`)로 API 주소 등 설정 가능
- 빌드 결과물은 `/build` 폴더에 생성
- Tailwind, shadcn UI 커스터마이징 가능
