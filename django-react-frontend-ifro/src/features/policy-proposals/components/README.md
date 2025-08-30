# 정책제안 시스템 (Policy Proposal System)

교통 관리 시스템에 통합된 시민 참여형 정책제안 플랫폼입니다.

## 📋 주요 기능

### 👥 일반 사용자 (시민)

- **정책제안 작성**: 교통 관련 개선사항이나 문제점을 제안
- **제안 목록 보기**: 다른 시민들의 제안을 확인
- **제안 검색/필터링**: 카테고리, 상태, 우선순위별 검색
- **추천/비추천**: 유용한 제안에 투표
- **내 제안 관리**: 작성한 제안 확인 및 수정 (대기 중 상태만)

### 👨‍💼 관리자

- **제안 관리 대시보드**: 모든 제안의 상태 및 통계 확인
- **제안 검토**: 제출된 제안을 검토하고 상태 변경
- **관리자 답변**: 제안에 대한 공식적인 답변 작성
- **긴급 제안 알림**: 우선순위가 높은 제안 우선 처리
- **통계 및 분석**: 카테고리별, 상태별 제안 현황 파악

## 🗂️ 카테고리

- **신호등 관련** (`traffic_signal`): 신호등 설치, 수정, 최적화 관련
- **도로 안전** (`road_safety`): 횡단보도, 안전시설, 보안 관련
- **교통 흐름** (`traffic_flow`): 교통량 관리, 노선 개선 관련
- **인프라 개선** (`infrastructure`): 도로 확장, 신설, 개선 관련
- **교통 정책** (`policy`): 교통 정책, 규제, 제도 관련
- **기타** (`other`): 위 카테고리에 해당하지 않는 기타 제안

## 🚦 제안 상태

- **대기 중** (`pending`): 새로 제출된 제안, 검토 대기
- **검토 중** (`under_review`): 관리자가 검토를 시작한 상태
- **진행 중** (`in_progress`): 제안이 채택되어 실행 중인 상태
- **완료** (`completed`): 제안이 성공적으로 완료된 상태
- **반려** (`rejected`): 제안이 반려된 상태

## ⭐ 우선순위

- **낮음** (`low`): 일반적인 개선사항
- **보통** (`medium`): 어느 정도 중요한 사항 (기본값)
- **높음** (`high`): 중요하고 시급한 사항
- **긴급** (`urgent`): 즉시 처리가 필요한 안전 관련 사항

## 🛣️ 라우트 구조

```
/proposals                    # 정책제안 목록
/proposals/create            # 새 정책제안 작성
/proposals/:id               # 정책제안 상세보기
/proposals/:id/edit          # 정책제안 수정 (작성자만, 대기 중 상태만)
/admin/proposals             # 관리자 정책제안 관리 (관리자만)
```

## 🎨 UI/UX 특징

### 사용자 친화적 인터페이스

- **직관적인 카테고리 분류**: 아이콘과 색상으로 구분
- **상태별 색상 코딩**: 진행 상황을 한눈에 파악
- **우선순위 표시**: 긴급도에 따른 시각적 표시
- **검색 및 필터링**: 다양한 조건으로 제안 찾기

### 반응형 디자인

- **모바일 친화적**: 터치 스크린에 최적화
- **다양한 화면 크기 지원**: 데스크톱부터 모바일까지
- **직관적인 네비게이션**: 쉬운 페이지 이동

### 접근성

- **키보드 네비게이션**: 키보드만으로도 모든 기능 사용 가능
- **스크린 리더 지원**: 시각 장애인을 위한 적절한 라벨링
- **고대비 색상**: 시인성 향상

## 🔧 기술 스택

### Frontend

- **React 18**: 사용자 인터페이스 구축
- **TypeScript**: 타입 안전성 확보
- **React Router**: 클라이언트 사이드 라우팅
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Lucide Icons**: 일관된 아이콘 시스템

### Backend API (가정)

- **Django REST Framework**: RESTful API 서버
- **JWT 인증**: 안전한 사용자 인증
- **PostgreSQL**: 안정적인 데이터 저장

## 📊 데이터 구조

### PolicyProposal

```typescript
interface PolicyProposal {
  id: number;
  title: string; // 제목
  description: string; // 내용
  category: ProposalCategory; // 카테고리
  priority: ProposalPriority; // 우선순위
  status: ProposalStatus; // 상태
  location?: string; // 위치 설명
  intersection_id?: number; // 관련 교차로 ID
  intersection_name?: string; // 관련 교차로 이름
  coordinates?: Coordinates; // 좌표
  submitted_by: number; // 제안자 ID
  submitted_by_name: string; // 제안자 이름
  submitted_by_email: string; // 제안자 이메일
  created_at: string; // 작성일
  updated_at: string; // 수정일
  admin_response?: string; // 관리자 답변
  admin_response_date?: string; // 답변일
  admin_response_by?: string; // 답변자
  attachments?: ProposalAttachment[]; // 첨부파일
  tags?: string[]; // 태그
  votes_count?: number; // 투표 수
  views_count?: number; // 조회 수
}
```

## 🔐 권한 시스템

### 일반 사용자

- 자신의 제안만 수정/삭제 가능
- 대기 중 상태의 제안만 수정 가능
- 모든 제안에 투표 가능

### 관리자

- 모든 제안의 상태 변경 가능
- 관리자 답변 작성 가능
- 통계 및 관리 기능 접근 가능

## 🚀 향후 개선 계획

### 기능 확장

- **첨부파일 시스템**: 이미지, 문서 첨부 기능
- **이메일 알림**: 제안 상태 변경 시 자동 알림
- **대시보드 위젯**: 메인 대시보드에 제안 통계 표시
- **공개 투표**: 시민들의 의견 수렴을 위한 투표 시스템

### 성능 최적화

- **가상 스크롤**: 대용량 목록 처리
- **이미지 최적화**: 첨부 이미지 압축 및 최적화
- **캐시 시스템**: 자주 조회되는 데이터 캐싱

### 사용성 개선

- **드래그 앤 드롭**: 파일 업로드 개선
- **실시간 알림**: WebSocket을 통한 실시간 업데이트
- **다국어 지원**: 다양한 언어로 서비스 제공

## 🤝 기여 방법

1. 이슈 생성: 버그 리포트나 기능 요청
2. 풀 리퀘스트: 코드 개선이나 새 기능 추가
3. 피드백 제공: 사용자 경험 개선 의견

## 📞 연락처

IFRO 세종대학교 교통 시스템 개발팀

- 이메일: contact@ifro-sejong.ac.kr
- GitHub: https://github.com/IFRO_SEJONG
