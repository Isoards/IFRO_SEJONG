"""
상수 정의
원칙 2: 규칙, 상수는 config 파일로 분리
"""
from enum import Enum, auto


class FragmentType(str, Enum):
    """Fragment Schema 유형"""
    FACT = "fact"              # A == B (사실 관계)
    MECHANISM = "mechanism"    # A ↗ B ↘ (인과성/비례/반비례)
    CONDITION = "condition"    # X일 때 A는 B로 변화
    OUTCOME = "outcome"        # 조건 충족 시 C 발생


class RelationType(str, Enum):
    """온톨로지 관계 유형"""
    IS_A = "is_a"                    # 상위 개념
    PART_OF = "part_of"              # 부분 관계
    CAUSES = "causes"                # 원인-결과
    INFLUENCES = "influences"        # 영향 관계
    PROPORTIONAL = "proportional"    # 비례 관계
    INVERSE = "inverse"              # 반비례 관계
    DEPENDS_ON = "depends_on"        # 의존 관계
    PRECEDES = "precedes"            # 선행 관계
    EQUIVALENT = "equivalent"        # 동등 관계


class IntentType(str, Enum):
    """사용자 질의 의도 분류"""
    RETRIEVAL = "retrieval"      # 정보 조회
    ANALYSIS = "analysis"        # 분석/추론
    EXECUTION = "execution"      # 시스템 동작 요청
    CREATION = "creation"        # Action 신규 생성 요청


class ActionType(str, Enum):
    """액션 유형"""
    RETRIEVE = "retrieve"        # 조회/그래프/요약
    REASON = "reason"            # 조건 기반 추론
    EXECUTE = "execute"          # 알림/자동화/시스템 실행


class ValidationStatus(str, Enum):
    """검증 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class FeasibilityLevel(str, Enum):
    """실행 가능성 수준"""
    HIGH = "high"          # 자동 실행 가능
    MEDIUM = "medium"      # 경고 후 실행
    LOW = "low"            # Admin 승인 필요


class ValidationLayer(str, Enum):
    """v4.2 Validation Pyramid 레이어"""
    RULE = "rule"                # L0: Rule-based 필터
    SMALL_MODEL = "small_model"  # L1: Small Model 필터
    LLM_RL = "llm_rl"            # L2: LLM + RL 검증


class RelationTypeMode(str, Enum):
    """관계 저장 유형 (v4.2 헤어볼 방지)"""
    DIRECT = "direct"      # 원문/검증된 직접 관계
    INDIRECT = "indirect"  # 추론된 간접 관계


# LLM Prompt Templates
PROMPT_TEMPLATES = {
    "fragment_extraction": """
다음 텍스트에서 지식 Fragment를 추출하세요.

Fragment 유형:
- FACT: A == B 형태의 사실 관계
- MECHANISM: A가 B에 영향을 미치는 인과성 (비례/반비례)
- CONDITION: 특정 조건 X일 때 A가 B로 변화
- OUTCOME: 조건 충족 시 발생하는 결과

텍스트:
{text}

JSON 형식으로 응답하세요:
{{
    "fragments": [
        {{
            "type": "fragment_type",
            "subject": "주제 엔티티",
            "predicate": "관계/동작",
            "object": "대상 엔티티",
            "confidence": 0.0-1.0,
            "evidence": "근거 텍스트"
        }}
    ]
}}
""",
    
    "entity_resolution": """
다음 두 엔티티가 동일한 개념을 나타내는지 분석하세요.

엔티티 1: {entity1}
- 문맥: {context1}

엔티티 2: {entity2}
- 문맥: {context2}

JSON 형식으로 응답하세요:
{{
    "is_same": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "판단 근거"
}}
""",
    
    "intent_classification": """
사용자 질문의 의도를 분류하세요.

질문: {query}

의도 유형:
- RETRIEVAL: 정보 조회 (무엇인가요? 어떤 것이 있나요?)
- ANALYSIS: 분석/추론 (왜? 어떻게? 관계는?)
- EXECUTION: 시스템 동작 요청 (실행해줘, 알림 설정)
- CREATION: 신규 Action 생성 요청 (새로운 규칙 만들어줘)

JSON 형식으로 응답하세요:
{{
    "intent": "의도 유형",
    "confidence": 0.0-1.0,
    "entities": ["관련 엔티티들"],
    "keywords": ["핵심 키워드"]
}}
""",
    
    "action_generation": """
온톨로지 그래프와 사용자 질의를 기반으로 적절한 Action을 생성하세요.

질의: {query}
의도: {intent}
관련 엔티티: {entities}
관련 관계: {relations}

Action 유형:
- RETRIEVE: 정보 조회, 그래프 탐색, 요약
- REASON: 조건 기반 추론, 인과 분석
- EXECUTE: 시스템 동작, 알림, 자동화

JSON 형식으로 응답하세요:
{{
    "action_type": "액션 유형",
    "name": "액션 이름",
    "description": "설명",
    "parameters": {{}},
    "expected_output": "예상 결과 형태",
    "confidence": 0.0-1.0
}}
""",

    "rag_response": """
다음 온톨로지 정보를 기반으로 사용자 질문에 답변하세요.

질문: {query}

관련 온톨로지 정보:
{ontology_context}

지침:
1. 온톨로지 정보에 기반하여 정확하게 답변하세요.
2. 정보가 부족하면 솔직히 말하세요.
3. 관계와 맥락을 명확히 설명하세요.

답변:
"""
}
