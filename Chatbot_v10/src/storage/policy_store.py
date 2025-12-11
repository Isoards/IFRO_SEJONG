"""
Policy Store - RL 정책 가중치 영속화
Validator의 학습된 가중치를 저장/복원

원칙 1: One Source of Truth - 정책 데이터의 단일 저장소
원칙 4: 단일 책임 - 정책 영속화만 담당
"""
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from pathlib import Path

from src.storage.base import BaseStore, JSONFileStore
from src.shared.logging import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class PolicyData:
    """정책 데이터 구조"""
    
    def __init__(
        self,
        validator_name: str,
        policy_weights: Dict[str, float],
        reward_history: List[float],
        feedback_count: int,
        avg_reward: float,
        approval_rate: float,
        updated_at: Optional[datetime] = None
    ):
        self.id = validator_name
        self.validator_name = validator_name
        self.policy_weights = policy_weights
        self.reward_history = reward_history
        self.feedback_count = feedback_count
        self.avg_reward = avg_reward
        self.approval_rate = approval_rate
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "validator_name": self.validator_name,
            "policy_weights": self.policy_weights,
            "reward_history": self.reward_history,
            "feedback_count": self.feedback_count,
            "avg_reward": self.avg_reward,
            "approval_rate": self.approval_rate,
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyData":
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            validator_name=data["validator_name"],
            policy_weights=data["policy_weights"],
            reward_history=data.get("reward_history", []),
            feedback_count=data.get("feedback_count", 0),
            avg_reward=data.get("avg_reward", 0.0),
            approval_rate=data.get("approval_rate", 0.0),
            updated_at=updated_at,
        )


class PolicyStore(BaseStore[PolicyData]):
    """
    RL 정책 저장소
    
    기능:
    - Validator 정책 가중치 저장/로드
    - 히스토리 기반 정책 복원
    - 정책 통계 관리
    """
    
    DEFAULT_FILE_NAME = "rl_policies.json"
    
    def __init__(self, storage_path: Optional[Path] = None):
        super().__init__("policy")
        self.storage_path = storage_path or Path("./data/policies")
        self.file_path = self.storage_path / self.DEFAULT_FILE_NAME
        self._data: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """저장소 초기화"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
            
            self._initialized = True
            logger.info("policy_store_initialized", path=str(self.file_path))
            
        except Exception as e:
            raise self._handle_error(e, "initialize")
    
    async def _persist(self) -> None:
        """데이터를 파일에 저장"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise self._handle_error(e, "persist")
    
    async def save(self, policy: PolicyData) -> str:
        """정책 저장"""
        self._ensure_initialized()
        
        try:
            self._data[policy.validator_name] = policy.to_dict()
            await self._persist()
            
            logger.info(
                "policy_saved",
                validator=policy.validator_name,
                weights=policy.policy_weights
            )
            return policy.validator_name
            
        except Exception as e:
            raise self._handle_error(e, "save")
    
    async def save_validator_policy(
        self,
        validator_name: str,
        policy_weights: Dict[str, float],
        reward_history: List[float],
        feedback_history: List[Dict[str, Any]]
    ) -> str:
        """Validator 정책 저장 (편의 메서드)"""
        # 통계 계산
        feedback_count = len(feedback_history)
        avg_reward = sum(reward_history) / len(reward_history) if reward_history else 0.0
        
        approved_count = sum(1 for f in feedback_history if f.get("approved", False))
        approval_rate = approved_count / feedback_count if feedback_count > 0 else 0.0
        
        # 최근 히스토리만 저장 (메모리 효율)
        recent_rewards = reward_history[-1000:] if len(reward_history) > 1000 else reward_history
        
        policy = PolicyData(
            validator_name=validator_name,
            policy_weights=policy_weights,
            reward_history=recent_rewards,
            feedback_count=feedback_count,
            avg_reward=avg_reward,
            approval_rate=approval_rate,
        )
        
        return await self.save(policy)
    
    async def get(self, validator_name: str) -> Optional[PolicyData]:
        """정책 조회"""
        self._ensure_initialized()
        
        data = self._data.get(validator_name)
        if data:
            return PolicyData.from_dict(data)
        return None
    
    async def load_validator_policy(
        self,
        validator_name: str
    ) -> Optional[Dict[str, Any]]:
        """Validator 정책 로드 (편의 메서드)"""
        policy = await self.get(validator_name)
        
        if policy:
            return {
                "policy_weights": policy.policy_weights,
                "reward_history": policy.reward_history,
                "feedback_count": policy.feedback_count,
                "avg_reward": policy.avg_reward,
                "approval_rate": policy.approval_rate,
            }
        return None
    
    async def delete(self, validator_name: str) -> bool:
        """정책 삭제"""
        self._ensure_initialized()
        
        if validator_name in self._data:
            del self._data[validator_name]
            await self._persist()
            return True
        return False
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[PolicyData]:
        """모든 정책 조회"""
        self._ensure_initialized()
        
        policies = [
            PolicyData.from_dict(data) 
            for data in list(self._data.values())[offset:offset + limit]
        ]
        return policies
    
    async def get_all_policy_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 정책의 통계 조회"""
        self._ensure_initialized()
        
        stats = {}
        for name, data in self._data.items():
            stats[name] = {
                "weights": data.get("policy_weights", {}),
                "feedback_count": data.get("feedback_count", 0),
                "avg_reward": data.get("avg_reward", 0.0),
                "approval_rate": data.get("approval_rate", 0.0),
                "updated_at": data.get("updated_at"),
            }
        return stats
    
    async def close(self) -> None:
        """저장소 종료"""
        await self._persist()
        self._initialized = False
        logger.info("policy_store_closed")
