# 타입 오류 해결 가이드

## 수정 완료된 사항

### 1. 타입 정의 수정
- `AIPolicyProposal`: AI 분석에서 생성되는 정책 제안 타입 (새로 추가)
- `PolicyProposal`: 시민 정책 제안 시스템에서 사용하는 기존 타입 (유지)

### 2. 파일 수정 내용

#### `/src/shared/types/global.types.ts`
```typescript
// AI 정책 평가 타입
export type PolicyEvaluation = {
  safety_priority: 'high' | 'medium' | 'low';
  infrastructure_needs: string[];
  accessibility_issues: string[];
  signal_optimization: 'needed' | 'not_needed' | 'urgent';
};

// AI 정책 제안 타입 (AI 분석용)
export type AIPolicyProposal = {
  category: 'traffic_signal' | 'road_safety' | 'traffic_flow' | 'infrastructure' | 'policy' | 'other';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low' | 'urgent';
  expected_impact: 'high' | 'medium' | 'low';
  implementation_difficulty: 'easy' | 'medium' | 'hard';
  estimated_cost: 'low' | 'medium' | 'high';
  timeline: 'short' | 'medium' | 'long';
};

// 시민 정책 제안 타입 (기존)
export interface PolicyProposal {
  id: number;
  title: string;
  description: string;
  category: ProposalCategory;
  priority: ProposalPriority;
  status: ProposalStatus;
  location?: string;
  intersection_id?: number;
  intersection_name?: string;
  coordinates?: Coordinates;
  submitted_by: number;
  submitted_by_name: string;
  submitted_by_email: string;
  created_at: string;
  updated_at: string;
  admin_response?: string;
  admin_response_date?: string;
  admin_response_by?: string;
  attachments?: ProposalAttachment[];
  tags?: string[];
  votes_count?: number;
  views_count?: number;
}
```

#### `/src/features/pdf-reports/components/sections/PolicyAnalysisSection.tsx`
- `AIPolicyProposal` 타입 사용
- 타입 명시적 지정으로 any 오류 해결

## 오류 해결 방법

### 1. 개발 서버 재시작
```bash
cd django-react-frontend-ifro
npm start
```

### 2. 타입 캐시 클리어 (필요시)
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
npm install

# 또는 TypeScript 캐시만 클리어
rm -rf node_modules/.cache
```

### 3. VSCode 재시작 (필요시)
- VSCode에서 `Ctrl+Shift+P` (또는 `Cmd+Shift+P`)
- "TypeScript: Restart TS Server" 실행

## 주요 변경사항 요약

### Backend (Python)
1. `gemini_service.py`: 정책 제안 데이터 생성 프롬프트 추가
2. `views.py`: 정책 제안 API 엔드포인트 추가
   - `GET /api/intersections/{id}/policy-proposals`
   - `POST /api/intersections/{id}/generate-citizen-proposals`

### Frontend (React/TypeScript)
1. `PolicyAnalysisSection.tsx`: 정책 분석 섹션 컴포넌트 생성
2. `PDFTemplate.tsx`: 정책 분석 섹션 통합
3. `global.types.ts`: 타입 정의 추가 및 정리

## 기대 효과

- ✅ Gemini AI 분석이 정책 제안 데이터 제공에 최적화
- ✅ 데이터 기반 정책 제안 자동 생성
- ✅ 우선순위 및 실행 가능성 평가
- ✅ 시민 제안 시스템과 연동

## 문제 해결

### 컴파일 오류가 계속 발생하는 경우

1. **권한 문제로 npm install 실패**
   ```bash
   # 소유자 변경
   sudo chown -R $USER:$USER .
   npm install
   ```

2. **타입 오류가 계속 발생**
   - VSCode TypeScript 서버 재시작
   - `tsconfig.json` 확인
   - `node_modules/@types` 폴더 확인

3. **import 경로 오류**
   - 상대 경로 확인: `../../../shared/types/global.types` → `../../../../shared/types/global.types`
   - 절대 경로 사용: `@shared/types/global.types` (tsconfig.json paths 설정 필요)

---

*이 가이드는 타입 오류 해결을 위한 참고 자료입니다. 실제 환경에 따라 추가 조치가 필요할 수 있습니다.*
