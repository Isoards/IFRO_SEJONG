"""
v5.2 Action Generator
Action 후보 생성 엔진

핵심 기능:
- 쿼리/의도에서 Action 후보 생성
- Score = 0.5*intent + 0.3*history + 0.2*reasoning
- Top-3 후보 선정
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from src.domain.actions import (
    Action, ActionCandidate, ActionTier, ActionStatus, RiskLevel,
    ActionTrace, get_tier_for_action_type
)
from config.constants import ActionType
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.reasoning import ReasoningResult

logger = get_logger(__name__)


class ActionGenerator:
    """
    v5.2 Action Generator
    
    Action 후보 점수:
    Score = 0.5*intent_match + 0.3*history_success + 0.2*reasoning_confidence
    
    상위 3개만 후보로 선정
    """
    
    MAX_CANDIDATES = 3
    
    # Intent → ActionType 매핑
    INTENT_ACTION_MAP = {
        # 조회 계열
        "search": ActionType.RETRIEVE,
        "find": ActionType.RETRIEVE,
        "show": ActionType.RETRIEVE,
        "get": ActionType.RETRIEVE,
        "list": ActionType.RETRIEVE,
        
        # 추론 계열
        "why": ActionType.REASON,
        "how": ActionType.REASON,
        "explain": ActionType.REASON,
        "analyze": ActionType.REASON,
        "what if": ActionType.REASON,
        "predict": ActionType.REASON,
        "cause": ActionType.REASON,
        "effect": ActionType.REASON,
        
        # 실행 계열
        "execute": ActionType.EXECUTE,
        "run": ActionType.EXECUTE,
        "trigger": ActionType.EXECUTE,
        "update": ActionType.EXECUTE,
        "create": ActionType.EXECUTE,
    }
    
    def __init__(
        self,
        action_history: Optional[Dict[str, Dict[str, float]]] = None
    ):
        # Action 히스토리: {action_type: {success_rate, avg_confidence}}
        self.action_history = action_history or {}
    
    async def generate(
        self,
        query: str,
        entities: List[str],
        reasoning_result: Optional["ReasoningResult"] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ActionCandidate]:
        """
        쿼리와 컨텍스트에서 Action 후보 생성
        
        Args:
            query: 사용자 쿼리
            entities: 관련 엔티티 이름들
            reasoning_result: 추론 결과 (있으면)
            context: 추가 컨텍스트
        """
        candidates = []
        
        # 1. Intent 분석
        detected_intents = self._analyze_intent(query)
        
        # 2. 각 Intent에 대해 Action 후보 생성
        for intent, intent_score in detected_intents:
            action_type = self.INTENT_ACTION_MAP.get(intent, ActionType.RETRIEVE)
            
            # Action 생성
            action = self._create_action(
                query=query,
                intent=intent,
                action_type=action_type,
                entities=entities,
                reasoning_result=reasoning_result
            )
            
            # 점수 계산
            history_success = self._get_history_success(action_type)
            reasoning_conf = reasoning_result.confidence if reasoning_result else 0.5
            
            # v5.2 공식: Score = 0.5*intent + 0.3*history + 0.2*reasoning
            score = (
                0.5 * intent_score +
                0.3 * history_success +
                0.2 * reasoning_conf
            )
            
            candidate = ActionCandidate(
                action=action,
                score=score,
                intent_match=intent_score,
                history_success=history_success,
                reasoning_confidence=reasoning_conf
            )
            
            candidates.append(candidate)
        
        # 3. 점수 기준 정렬 및 Top-N 선택
        candidates.sort(key=lambda c: c.score, reverse=True)
        top_candidates = candidates[:self.MAX_CANDIDATES]
        
        logger.info(
            "action_candidates_generated",
            query=query[:50],
            candidate_count=len(top_candidates)
        )
        
        return top_candidates
    
    def _analyze_intent(self, query: str) -> List[tuple[str, float]]:
        """
        쿼리에서 Intent 분석
        
        Returns:
            List of (intent, score)
        """
        query_lower = query.lower()
        detected = []
        
        for intent_keyword in self.INTENT_ACTION_MAP.keys():
            if intent_keyword in query_lower:
                # 키워드 위치 기반 점수 (앞에 있을수록 높음)
                position = query_lower.find(intent_keyword)
                position_score = 1.0 - (position / max(len(query_lower), 1)) * 0.3
                detected.append((intent_keyword, min(1.0, position_score)))
        
        # 기본 Intent (아무것도 없으면)
        if not detected:
            detected.append(("search", 0.5))
        
        return detected
    
    def _create_action(
        self,
        query: str,
        intent: str,
        action_type: ActionType,
        entities: List[str],
        reasoning_result: Optional["ReasoningResult"]
    ) -> Action:
        """Action 객체 생성"""
        tier = get_tier_for_action_type(action_type)
        
        # 추론 결과가 있으면 trace에 포함
        trace = None
        if reasoning_result:
            trace = ActionTrace(
                reasoning_steps=[{"trace": t} for t in getattr(reasoning_result, 'trace', [])],
                source_entities=entities
            )
        
        return Action(
            name=f"{intent}_{action_type.value}",
            description=f"Generated for query: {query[:100]}",
            action_type=action_type,
            tier=tier,
            trigger_intent=intent,
            trigger_entities=entities,
            trigger_keywords=query.split()[:5],
            confidence=reasoning_result.confidence if reasoning_result else 0.5,
            trace=trace,
            status=ActionStatus.PENDING
        )
    
    def _get_history_success(self, action_type: ActionType) -> float:
        """히스토리 기반 성공률 조회"""
        history = self.action_history.get(action_type.value, {})
        return history.get("success_rate", 0.5)
    
    def update_history(
        self,
        action_type: ActionType,
        success: bool,
        confidence: float
    ):
        """Action 히스토리 업데이트"""
        key = action_type.value
        if key not in self.action_history:
            self.action_history[key] = {
                "success_rate": 0.5,
                "avg_confidence": 0.5,
                "count": 0
            }
        
        history = self.action_history[key]
        count = history["count"]
        
        # 이동 평균 업데이트
        new_count = count + 1
        history["success_rate"] = (
            history["success_rate"] * count + (1.0 if success else 0.0)
        ) / new_count
        history["avg_confidence"] = (
            history["avg_confidence"] * count + confidence
        ) / new_count
        history["count"] = new_count
