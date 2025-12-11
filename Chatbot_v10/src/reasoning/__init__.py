"""
v5.2 Reasoning Engine
심볼릭 추론 엔진 패키지

모듈:
- PathReasoner: 경로 기반 추론
- MechanismReasoner: 메커니즘 전파
- ScenarioSimulator: 영향도 시뮬레이션
"""
from src.reasoning.base import (
    BaseReasoner,
    ReasoningResult,
    ReasoningResultType,
    ReasoningPath,
    PropagationEffect
)
from src.reasoning.path_reasoner import PathReasoner
from src.reasoning.mechanism_reasoner import MechanismReasoner
from src.reasoning.scenario_simulator import ScenarioSimulator, ScenarioInput

__all__ = [
    "BaseReasoner",
    "ReasoningResult",
    "ReasoningResultType",
    "ReasoningPath",
    "PropagationEffect",
    "PathReasoner",
    "MechanismReasoner",
    "ScenarioSimulator",
    "ScenarioInput"
]
