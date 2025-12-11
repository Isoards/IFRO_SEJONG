---
description: v4.2 Validation Pyramid + Domain Dictionary + Hairball Prevention 마이그레이션
---

# v4.2 Migration Workflow ✅ 완료

## Phase 1: Validation Pyramid 구현 ✅

### 1.1 ValidationResult 확장 ✅
- [x] `layer` 필드 추가: "rule" | "small_model" | "llm_rl"
- [x] `rejected_early` 필드 추가 (L0/L1에서 조기 reject 표시)
- [x] `layer_scores` 필드 추가 (각 레이어별 점수)

### 1.2 BaseValidator 리팩토링 ✅
- [x] `rule_check(item)` 추상 메서드 추가
- [x] `small_model_check(item)` 메서드 추가 (기본 pass-through)
- [x] `validate()` 메서드를 Pyramid Orchestrator로 변경
- [x] `LayerResult`, `LayerDecision` dataclass 추가

### 1.3 FragmentValidator v4.2 ✅
- [x] L0: 문법/형식 규칙 (SVO 구조, 최소 길이, stopword)
- [x] L1: Small classifier (pass-through)
- [x] L2: LLM semantic validity
- [x] 레거시 호환성 메서드 (`validate_fragment`, `validate_batch`)

### 1.4 EntityValidator v4.2 ✅
- [x] L0: 길이 < N, 전부 숫자, stopword, 대명사 → reject
- [x] L1: Small model (휴리스틱 기반)
- [x] L2: LLM 도메인 의미 검증
- [x] 레거시 호환성 메서드 (`validate_entity`)

### 1.5 RelationValidator v4.2 ✅
- [x] L0: Self-loop 방지, 동일/반대 방향 모순 체크
- [x] L1: Small model coarse check
- [x] L2: LLM 의미 검증
- [x] Transitive Reduction 후보 판단
- [x] Degree Limit 체크

## Phase 2: Domain Dictionary 추가 ✅

### 2.1 DomainDictionary 클래스 구현 ✅
- [x] `src/storage/domain_dictionary.py` 신규 생성
- [x] 스키마: `entity_id | canonical_name | aliases | tags`
- [x] 메서드: `get_canonical()`, `add_alias()`, `suggest_aliases()`
- [x] SQLite 기반 영속화
- [x] 메모리 캐시 + Alias 인덱스

### 2.2 EntityValidator 연동 ✅
- [x] Dictionary 기반 중복 엔티티 감지
- [x] `resolve_to_canonical()` 메서드

## Phase 3: Graph Store v4.2 ✅

### 3.1 스키마 변경 ✅
- [x] RelationModel에 `relation_type_mode` 필드 추가
- [x] RelationModel에 `validation_layer` 필드 추가

### 3.2 Direct/Indirect 분리 ✅
- [x] `get_direct_relations()` 메서드
- [x] `get_indirect_relations()` 메서드
- [x] `get_entity_degree()` 메서드
- [x] `update_relation_type_mode()` 메서드
- [x] `get_graph_statistics()` v4.2 확장

## Phase 4: Ontology Service v4.2 ✅

### 4.1 add_direct_relation 메서드 ✅
- [x] Relation Validator 호출
- [x] 헤어볼 방지 체크 (degree limit)
- [x] relation_type="direct"로 저장
- [x] Transitive 관계는 indirect로 마킹

### 4.2 Transitive Reduction 지원 ✅
- [x] `apply_transitive_reduction()` 메서드 추가
- [x] `get_indirect_path()` 메서드 추가
- [x] 수동/배치 작업으로 시작

### 4.3 통계 v4.2 확장 ✅
- [x] Direct/Indirect 관계 수 분리
- [x] Domain Dictionary 상태 표시

## Phase 5: Config 업데이트 ✅

### 5.1 settings.py 확장 ✅
- [x] Validation Pyramid 가중치 (α, β, γ, δ)
- [x] Degree limit 설정 (in/out)
- [x] Small model endpoint (선택)
- [x] RAG context max depth

### 5.2 constants.py 확장 ✅
- [x] `ValidationLayer` enum 추가
- [x] `RelationTypeMode` enum 추가

---

## 테스트 결과

```
43 passed, 1 warning in 1.73s
```

모든 테스트 통과! 레거시 호환성 유지됨.
