"""
Validator 베이스 클래스 - v4.2 Validation Pyramid
계획서: Rule → Small Model → LLM + RL 순차 검증

v4.2 핵심 변경:
- L0: Rule Filter (빠른 reject)
- L1: Small Model Filter (선택적)
- L2: LLM + RL (최종 검증)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from pathlib import Path
from enum import Enum

from config.settings import get_settings
from config.constants import FeasibilityLevel, ValidationLayer

if TYPE_CHECKING:
    from src.services.llm_service import LLMService
    from src.storage.policy_store import PolicyStore


@dataclass
class ValidationResult:
    """검증 결과 - v4.2 확장"""
    is_valid: bool
    score: float  # 0.0 ~ 1.0
    reasons: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    feasibility_level: FeasibilityLevel = FeasibilityLevel.MEDIUM
    
    # v4.2 Validation Pyramid 추가 필드
    layer: ValidationLayer = ValidationLayer.LLM_RL  # 어느 레이어에서 결정됐는지
    rejected_early: bool = False  # L0/L1에서 조기 reject됐는지
    
    # 각 레이어별 점수 (디버깅/분석용)
    layer_scores: Dict[str, float] = field(default_factory=dict)


class LayerDecision(Enum):
    """레이어별 결정"""
    PASS = "pass"          # 다음 레이어로 진행
    REJECT = "reject"      # 즉시 reject
    APPROVE = "approve"    # 즉시 approve (L2에서만)


@dataclass
class LayerResult:
    """레이어 검증 결과"""
    score: float
    decision: LayerDecision
    reasons: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class BaseValidator(ABC):
    """
    Validator 베이스 클래스 - v4.2 Validation Pyramid Orchestrator
    
    v4.2 설계:
    - L0: Rule Filter → 빠른 reject (비용 0)
    - L1: Small Model → 중간 필터 (선택적, 낮은 비용)
    - L2: LLM + RL → 최종 검증 (높은 비용)
    
    원칙 4: 단일 책임 - 검증만 담당
    원칙 1: One Source of Truth - 정책은 PolicyStore에 영속화
    """
    
    def __init__(
        self,
        llm_service: Optional["LLMService"] = None,
        policy_store: Optional["PolicyStore"] = None,
        validator_name: Optional[str] = None
    ):
        self.settings = get_settings()
        self.llm_service = llm_service
        self.policy_store = policy_store
        self.validator_name = validator_name or self.__class__.__name__
        
        # RL 상태
        self._reward_history: List[float] = []
        self._feedback_history: List[Dict[str, Any]] = []
        
        # v4.2 가중치 (Config에서 로드)
        self._pyramid_weights = self._init_pyramid_weights()
        
        # 정책 로드 플래그
        self._policy_loaded = False
    
    def _init_pyramid_weights(self) -> Dict[str, float]:
        """v4.2 Pyramid 가중치 초기화"""
        return {
            "alpha": self.settings.validation_alpha,   # Rule
            "beta": self.settings.validation_beta,     # Small Model
            "gamma": self.settings.validation_gamma,   # LLM
            "delta": self.settings.validation_delta,   # History/RL
        }
    
    async def load_policy(self) -> bool:
        """
        영속화된 정책 로드
        
        Returns:
            로드 성공 여부
        """
        if not self.policy_store or self._policy_loaded:
            return False
        
        try:
            policy_data = await self.policy_store.load_validator_policy(self.validator_name)
            
            if policy_data:
                # v4.2: pyramid_weights로 변경
                if "pyramid_weights" in policy_data:
                    self._pyramid_weights = policy_data["pyramid_weights"]
                elif "policy_weights" in policy_data:
                    # 하위 호환성
                    old_weights = policy_data["policy_weights"]
                    self._pyramid_weights["alpha"] = old_weights.get("rule_weight", 0.35)
                    self._pyramid_weights["gamma"] = old_weights.get("llm_weight", 0.30)
                    self._pyramid_weights["delta"] = old_weights.get("history_weight", 0.20)
                
                self._reward_history = policy_data.get("reward_history", [])
                self._policy_loaded = True
                return True
        except Exception:
            pass
        
        return False
    
    async def save_policy(self) -> bool:
        """
        현재 정책 영속화
        
        Returns:
            저장 성공 여부
        """
        if not self.policy_store:
            return False
        
        try:
            await self.policy_store.save_validator_policy(
                validator_name=self.validator_name,
                policy_weights=self._pyramid_weights,  # v4.2: pyramid_weights 사용
                reward_history=self._reward_history,
                feedback_history=self._feedback_history
            )
            return True
        except Exception:
            return False
    
    # ========== v4.2 Validation Pyramid Core ==========
    
    async def validate(self, item: Any) -> ValidationResult:
        """
        v4.2 Validation Pyramid 검증 수행
        
        L0: Rule Filter → reject이면 즉시 반환
        L1: Small Model Filter → reject이면 즉시 반환
        L2: LLM + RL → 최종 점수 계산
        """
        layer_scores: Dict[str, float] = {}
        all_reasons: List[str] = []
        
        # ===== L0: Rule Filter =====
        rule_result = await self.rule_check(item)
        layer_scores["rule"] = rule_result.score
        all_reasons.extend(rule_result.reasons)
        
        if rule_result.decision == LayerDecision.REJECT:
            return ValidationResult(
                is_valid=False,
                score=rule_result.score,
                reasons=all_reasons,
                details=rule_result.details,
                feasibility_level=FeasibilityLevel.LOW,
                layer=ValidationLayer.RULE,
                rejected_early=True,
                layer_scores=layer_scores
            )
        
        # ===== L1: Small Model Filter =====
        sm_result = await self.small_model_check(item)
        layer_scores["small_model"] = sm_result.score
        all_reasons.extend(sm_result.reasons)
        
        if sm_result.decision == LayerDecision.REJECT:
            return ValidationResult(
                is_valid=False,
                score=sm_result.score,
                reasons=all_reasons,
                details=sm_result.details,
                feasibility_level=FeasibilityLevel.LOW,
                layer=ValidationLayer.SMALL_MODEL,
                rejected_early=True,
                layer_scores=layer_scores
            )
        
        # ===== L2: LLM + RL =====
        llm_score, llm_reasons = await self.llm_check(item)
        layer_scores["llm"] = llm_score
        all_reasons.extend(llm_reasons)
        
        history_score = self._history_score(item)
        layer_scores["history"] = history_score
        
        # 최종 점수 계산 (v4.2 가중치 적용)
        final_score = self._calculate_pyramid_score(
            rule_score=rule_result.score,
            sm_score=sm_result.score,
            llm_score=llm_score,
            history_score=history_score
        )
        layer_scores["final"] = final_score
        
        # 최종 결정
        is_valid = final_score >= self.settings.final_validation_threshold
        
        # 실행 가능성 수준 결정
        if final_score >= self.settings.feasibility_high_threshold:
            feasibility = FeasibilityLevel.HIGH
        elif final_score >= self.settings.feasibility_medium_threshold:
            feasibility = FeasibilityLevel.MEDIUM
        else:
            feasibility = FeasibilityLevel.LOW
        
        return ValidationResult(
            is_valid=is_valid,
            score=final_score,
            reasons=all_reasons,
            details={
                "rule_details": rule_result.details,
                "sm_details": sm_result.details,
            },
            feasibility_level=feasibility,
            layer=ValidationLayer.LLM_RL,
            rejected_early=False,
            layer_scores=layer_scores
        )
    
    @abstractmethod
    async def rule_check(self, item: Any) -> LayerResult:
        """
        L0: Rule-based 검증 (하위 클래스에서 구현)
        
        빠른 reject를 위한 규칙 기반 검증.
        비용: 0
        
        Returns:
            LayerResult with decision = PASS or REJECT
        """
        pass
    
    async def small_model_check(self, item: Any) -> LayerResult:
        """
        L1: Small Model 검증 (기본 pass-through)
        
        설정된 small_model_endpoint가 있으면 호출,
        없으면 pass-through.
        
        Returns:
            LayerResult with decision = PASS or REJECT
        """
        # 기본: pass-through
        if not self.settings.small_model_endpoint:
            return LayerResult(
                score=0.7,  # neutral score
                decision=LayerDecision.PASS,
                reasons=[],
                details={"passed_through": True}
            )
        
        # Small Model 호출 구현 (하위 클래스에서 오버라이드 가능)
        return await self._call_small_model(item)
    
    async def _call_small_model(self, item: Any) -> LayerResult:
        """
        Small Model API 호출
        하위 클래스에서 오버라이드하여 구체적 로직 구현
        """
        # 기본 구현: pass-through
        return LayerResult(
            score=0.7,
            decision=LayerDecision.PASS,
            reasons=[],
            details={"small_model": "not_implemented"}
        )
    
    async def llm_check(self, item: Any) -> Tuple[float, List[str]]:
        """
        L2: LLM 검증
        
        Returns:
            (점수, 이유 목록)
        """
        if not self.llm_service:
            return 0.7, []  # LLM 없으면 기본값
        
        prompt = self._build_llm_prompt(item)
        return await self._llm_validation(item, prompt)
    
    def _build_llm_prompt(self, item: Any) -> str:
        """LLM 검증 프롬프트 생성 - 하위 클래스에서 오버라이드"""
        return f"다음 항목의 유효성을 검증하세요: {item}"
    
    async def _llm_validation(self, item: Any, prompt: str) -> Tuple[float, List[str]]:
        """
        LLM 기반 검증
        
        Args:
            item: 검증 대상
            prompt: 검증 프롬프트
        
        Returns:
            (점수, 이유 목록)
        """
        if not self.llm_service:
            return 0.7, []  # LLM 없으면 기본값
        
        try:
            import json
            
            response = await self.llm_service.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.3
            )
            
            try:
                result = json.loads(response)
                score = float(result.get("score", 0.7))
                reasons = result.get("issues", [])
                
                return score, [f"LLM: {r}" for r in reasons]
                
            except json.JSONDecodeError:
                return 0.7, []
                
        except Exception:
            return 0.7, []
    
    def _history_score(self, item: Any) -> float:
        """
        RL 히스토리 기반 점수
        
        하위 클래스에서 오버라이드하여 구체적 로직 구현
        """
        if not self._reward_history:
            return 0.5  # 중립값
        
        # 최근 N개 보상 평균
        recent = self._reward_history[-50:]
        avg = sum(recent) / len(recent)
        
        # -1.0 ~ 1.0을 0.0 ~ 1.0으로 변환
        return (avg + 1.0) / 2.0
    
    def _calculate_pyramid_score(
        self,
        rule_score: float,
        sm_score: float,
        llm_score: float,
        history_score: float
    ) -> float:
        """
        v4.2 Pyramid 가중치 기반 점수 계산
        
        Score = Rule * α + SmallModel * β + LLM * γ + History * δ
        """
        return (
            rule_score * self._pyramid_weights["alpha"] +
            sm_score * self._pyramid_weights["beta"] +
            llm_score * self._pyramid_weights["gamma"] +
            history_score * self._pyramid_weights["delta"]
        )
    
    # ========== Feedback & RL ==========
    
    async def record_feedback(
        self,
        item_id: str,
        approved: bool,
        reason: Optional[str] = None
    ):
        """
        피드백 기록 - RL reward signal
        """
        reward = 1.0 if approved else -1.0
        
        self._feedback_history.append({
            "item_id": item_id,
            "approved": approved,
            "reason": reason,
            "reward": reward,
        })
        
        self._reward_history.append(reward)
        
        # 정책 가중치 업데이트
        await self._update_policy()
        
        # 주기적 자동 저장 (50개 피드백마다)
        if len(self._feedback_history) % 50 == 0:
            await self.save_policy()
    
    async def record_user_feedback(
        self,
        item_id: str,
        rating: int,
        feedback: Optional[str] = None
    ):
        """
        사용자 피드백 기록
        """
        # rating을 reward로 변환 (1-5 -> -1.0 ~ 1.0)
        reward = (rating - 3) / 2.0
        
        self._feedback_history.append({
            "item_id": item_id,
            "rating": rating,
            "feedback": feedback,
            "reward": reward,
        })
        
        self._reward_history.append(reward)
        await self._update_policy()
    
    async def _update_policy(self):
        """
        정책 가중치 업데이트 (v4.2 버전)
        
        RL reward 기반으로 α, β, γ, δ 조정
        """
        if len(self._reward_history) < 10:
            return  # 충분한 데이터 필요
        
        # 최근 보상 평균
        recent_rewards = self._reward_history[-50:]
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        
        learning_rate = self.settings.rl_learning_rate
        
        # 보상이 낮으면 rule 가중치 증가 (더 보수적)
        # 보상이 높으면 llm 가중치 증가 (더 공격적)
        if avg_reward < 0:
            # 성능이 낮음 - rule 기반 강화
            self._pyramid_weights["alpha"] += learning_rate
            self._pyramid_weights["gamma"] -= learning_rate * 0.5
            self._pyramid_weights["delta"] -= learning_rate * 0.5
        else:
            # 성능이 좋음 - 현재 비율 유지하면서 history 강화
            self._pyramid_weights["delta"] += learning_rate * 0.5
        
        # 정규화
        total = sum(self._pyramid_weights.values())
        self._pyramid_weights = {
            k: max(0.05, v / total)  # 최소값 보장
            for k, v in self._pyramid_weights.items()
        }
        
        # 재정규화
        total = sum(self._pyramid_weights.values())
        self._pyramid_weights = {
            k: v / total for k, v in self._pyramid_weights.items()
        }
    
    def get_policy_stats(self) -> Dict[str, Any]:
        """정책 통계 반환"""
        return {
            "validator_name": self.validator_name,
            "pyramid_weights": self._pyramid_weights,
            "total_feedbacks": len(self._feedback_history),
            "avg_reward": (
                sum(self._reward_history) / len(self._reward_history)
                if self._reward_history else 0.0
            ),
            "recent_approval_rate": self._calculate_recent_approval_rate(),
            "policy_loaded": self._policy_loaded,
        }
    
    def _calculate_recent_approval_rate(self) -> float:
        """최근 승인률 계산"""
        recent = [
            f for f in self._feedback_history[-100:]
            if "approved" in f
        ]
        if not recent:
            return 0.0
        return sum(1 for f in recent if f["approved"]) / len(recent)
