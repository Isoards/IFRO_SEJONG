# v5.2 Ontology-Reasoning-Action System 가이드

이 문서는 v5.2 시스템의 핵심 원리, 아키텍처, 그리고 실행 방법을 설명하는 상세 가이드입니다.

---

## 1. 시스템 아키텍처 개요

v5.2 시스템은 **"데이터가 행동이 되는 과정"**을 3단계 계층으로 구현했습니다.

### 🏛️ 3-Tier Architecture

1.  **Domain Layer (지식 계층)**
    *   **OntologyGraph**: 엔티티(Entity)와 관계(Relation)로 구성된 지식 그래프.
    *   **One Source of Truth**: 모든 데이터는 그래프에 저장되며 중복되지 않습니다.
    *   **v5.2 특징**: 관계의 방향성(`sign`)과 신뢰도(`confidence`)를 수학적으로 모델링합니다.

2.  **Reasoning Layer (추론 계층)**
    *   단순 검색(Retrieval)을 넘어 **인과 관계(Causality)**를 분석합니다.
    *   **Path Reasoner**: 두 개념 사이의 연결 경로를 탐색하고 신뢰도를 계산합니다.
    *   **Mechanism Reasoner**: A가 변할 때 B가 어떻게 변하는지(`sign` 전파) 예측합니다.
    *   **Scenario Simulator**: 특정 사건이 전체 시스템에 미치는 파급 효과를 시뮬레이션합니다.

3.  **Action Layer (행동 계층)**
    *   추론 결과를 바탕으로 구체적인 **실행 계획(Action)**을 수립합니다.
    *   **5-Tier Taxonomy**: 조회(Retrieve)부터 워크플로우(Workflow)까지 행동을 분류합니다.
    *   **Feasibility Engine**: 실행 가능성을 점수화하여 자동 실행 여부를 결정합니다.

---

## 2. 핵심 작동 원리 (The Math)

v5.2는 흑마술 같은 AI가 아니라, **설명 가능한 수학적 모델**을 따릅니다.

### 🧮 1. 추론 신뢰도 (Reasoning Confidence)
경로가 길어질수록 신뢰도는 감소합니다.
> $$ Confidence = \Pi(c_i) \times 0.92^{(k-1)} $$
> *   $c_i$: 각 관계의 신뢰도
> *   $k$: 경로의 길이 (블록 수)
> *   $0.92$: 감쇠 계수 (단계별 8% 감소)

### 📈 2. 인과 방향성 (Sign Propagation)
A가 B를 증가시키고(+), B가 C를 감소시키면(-), A는 C를 감소시킵니다(-).
> $$ Sign_{final} = Sign_{r1} \times Sign_{r2} \times ... \times Sign_{rn} $$
> *   $(+) \times (+) = (+)$ : 긍정적 영향
> *   $(+) \times (-) = (-)$ : 부정적 영향
> *   $(-) \times (-) = (+)$ : 역기능의 억제는 긍정 (이중 부정)

### 🛡️ 3. 행동 적합성 (Feasibility Score)
이 행동을 지금 실행해도 되는가?
> $$ Score = 0.4 \times Data + 0.2 \times Resource + 0.2 \times Reasoning + 0.2 \times (1 - Risk) $$
> *   **Data Ready**: 필요한 입력 데이터가 갖춰졌는가? (40%)
> *   **Resource**: LLM, API, DB 등 자원이 가용한가? (20%)
> *   **Reasoning**: 추론의 근거가 확실한가? (20%)
> *   **Risk**: 실행 시 위험도가 낮은가? (20%)

---

## 3. 기능 실행 가이드

### 🚀 1. 서버 실행

FastAPI 기반의 API 서버를 실행하여 시스템을 가동합니다.

```bash
# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 서버 실행
python -m api.app
```

서버가 시작되면 `http://localhost:8000`에서 요청을 대기합니다.

### 📡 2. API 엔드포인트 활용

#### A. 헬스 체크
시스템이 정상적으로 작동하는지 확인합니다.
```bash
GET /healthz
```

#### B. 시스템 상태 확인
로드된 엔티티 수, LLM 연결 상태 등을 확인합니다.
```bash
GET /api/status
```

#### C. 질문하기 (RAG + 추론)
사용자의 질문을 분석하고, 온톨로지를 검색/추론하여 답변합니다.
```json
// POST /api/ask
{
  "question": "KTX가 교통 혼잡에 미치는 영향은?",
  "use_reasoning": true,
  "max_sources": 3
}
```

**응답 예시:**
```json
{
  "answer": "KTX는 도로 교통 수요를 흡수하여 교통 혼잡을 완화시킵니다.",
  "confidence": 0.85,
  "reasoning_trace": [
    "KTX -> (Inversely related) -> Traffic Congestion (sign=-1)"
  ],
  "action_suggested": "retrieve"
}
```

### 🧪 3. 테스트 실행

시스템의 정합성을 검증하기 위해 테스트 스위트를 실행합니다.

```bash
# 전체 테스트 실행
python -m pytest tests/

# 특정 모듈 테스트 (예: Reasoning)
python -m pytest tests/test_reasoning.py
```

---

## 4. 모듈별 상세 설명

### 🧠 Reasoning Engine (`src/reasoning/`)

*   **`path_reasoner.py`**: A에서 B로 가는 최단/최적 경로를 찾습니다. "서울에서 부산까지 어떻게 연결되는가?" 같은 질문에 답합니다.
*   **`mechanism_reasoner.py`**: 인과 사슬을 분석합니다. "금리가 오르면 집값은 어떻게 되는가?"를 `sign` 전파로 계산합니다.
*   **`scenario_simulator.py`**: 충격 파급 효과를 시뮬레이션합니다. "유가가 10% 오르면 경제 전반에 어떤 일이 생기는가?"를 예측합니다.

### ⚡ Action Layer (`src/actions/`)

*   **`action_generator.py`**: 사용자 의도(Intent)와 히스토리를 분석해 적절한 행동 후보를 생성합니다.
*   **`action_validator.py`**: 생성된 행동의 Feasibility Score를 계산하고, 위험한 행동(`HIGH RISK`)을 차단합니다.
*   **`action_executor.py`**: 행동을 실제로 수행하고, 모든 과정을 로그(`Trace`)로 남겨 디버깅을 돕습니다.

### 🛡️ Consistency Manager (`src/services/consistency_manager.py`)

*   시스템이 불안정해지는 것을 막는 **안전장치**입니다.
*   **Rule 1**: RL 파라미터가 한 번에 15% 이상 급변하면 강제로 조정(Clamp)합니다.
*   **Rule 2**: 온톨로지에 모순(Contradiction)이 3%를 넘으면 학습을 일시 중단(Freeze)합니다.
*   **Rule 3**: 너무 많은 연결(Degree > 40)을 가진 엔티티는 가지치기(Pruning)하여 '헤어볼' 현상을 방지합니다.

---

## 5. 문제 해결 (Troubleshooting)

*   **LLM 연결 오류**: `config/settings.py` 또는 환경변수 `OLLAMA_HOST`가 올바른지 확인하세요. (기본값: `http://localhost:11434`)
*   **서버 실행 실패**: `OntologyService` 초기화 중 오류가 발생할 수 있습니다. `logs/errors.log`를 확인하세요.
*   **추론 결과 없음**: 온톨로지에 관련 엔티티나 관계가 충분하지 않을 수 있습니다. 데이터를 추가하거나 연결을 보강하세요.
