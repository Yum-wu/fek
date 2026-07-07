"""策略引擎 —— FEK 的核心创新点，现已集成上下文老虎机学习层。

将复杂度评分映射为具体的计算策略。默认用阈值规则（冷启动即可跑、行为可预期）；
当学习层积累足够反馈后，自动切换到由 bandit 决策（自适应），
并保留阈值规则作为 fallback。正是这个唯一决策点，使 FEK 成为
"执行智能"而非一段写死的固定流水线。

学习层详见 fek/learning（docs/learn-design.md）。
"""

from __future__ import annotations

from ..core.types import Complexity, Strategy
from ..learning.bandit import ContextualBandit
from ..learning import create_learner
from ..learning.persist import load as _load_policy, save as _save_policy
from ..learning.reward import DEFAULT_LAMBDA, DEFAULT_MU, compute_reward

DEFAULT_STATE_PATH = "fek_policy.json"


class PolicyEngine:
    def __init__(
        self,
        low_threshold: float = 0.33,
        high_threshold: float = 0.66,
        learning: bool = True,
        warmup: int = 8,
        epsilon: float = 0.15,
        reward_lambda: float = DEFAULT_LAMBDA,
        reward_mu: float = DEFAULT_MU,
        bandit: ContextualBandit | None = None,
        learner_name: str = "epsilon_greedy",
        state_path: str | None = DEFAULT_STATE_PATH,
    ):
        self.low = low_threshold
        self.high = high_threshold
        self.learning = learning
        self.warmup = warmup
        self.state_path = state_path
        # 奖励函数权重（成本/延迟惩罚力度），可调以适配不同预算偏好
        self.reward_lambda = reward_lambda
        self.reward_mu = reward_mu
        # 三臂：SINGLE / MULTI_AGENT / MOA
        self.arms = list(Strategy)
        # 优先用外部传入的 bandit；否则通过 learner 工厂构建（满足 RFC 0009「可切换」）
        self.bandit = bandit or create_learner(learner_name, epsilon=epsilon)
        if state_path:
            loaded = _load_policy(state_path)
            if loaded is not None:
                self.bandit = ContextualBandit.from_dict(loaded)
        # 阈值规则的微小可学习偏移（作为 fallback 路径的自适应，保留原行为）
        self._drift = 0.0

    # ---- 阈值规则决策（冷启动 fallback）----
    def _rule_select(self, score: float) -> Strategy:
        s = score + self._drift
        if s < self.low:
            return Strategy.SINGLE
        if s < self.high:
            return Strategy.MULTI_AGENT
        return Strategy.MOA

    def select(self, score: float, band: Complexity | None = None) -> Strategy:
        # 学习层已热身 -> 用 bandit（按复杂度档位分桶，自适应选臂）
        if self.learning and band is not None and self.bandit.total_feedback >= self.warmup:
            return self.bandit.select(band.value, self.arms)
        # 否则回退阈值规则，保证评委零配置可跑、行为可预期
        return self._rule_select(score)

    def explain(self, score: float, band: Complexity | None = None) -> str:
        # s 用于规则比较（内部含漂移），但展示始终用原始分（用户友好）
        s = max(score + self._drift, 0.0)
        display_score = max(score, 0.0)
        # 学习层视角
        if self.learning and band is not None and self.bandit.total_feedback >= self.warmup:
            ctx = band.value
            best = self.bandit.best_arm(ctx, self.arms)
            lines = [
                f"评分 {display_score:.2f}，复杂度档 {ctx}，学习层已热身（{self.bandit.total_feedback} 条反馈）："
            ]
            for a in self.arms:
                m = self.bandit.mean_reward(ctx, a)
                n = self.bandit.count(ctx, a)
                tag = " <- 选中" if a == best else ""
                lines.append(f"  {a.zh}（{a.value}） 平均奖励 {m:+.3f} (n={n}){tag}")
            return "\n".join(lines)
        # 规则视角（显示原始分数，不暴露漂移值）
        if s < self.low:
            return f"评分 {display_score:.2f} < {self.low:.2f} -> 单模型 SINGLE（单模型已足够）"
        if s < self.high:
            return f"{self.low:.2f} <= 评分 {display_score:.2f} < {self.high:.2f} -> 多智能体 MULTI_AGENT（角色拆分更有帮助）"
        return f"评分 {display_score:.2f} >= {self.high:.2f} -> 混合专家 MOA（高不确定性，并行多模型 + 融合）"

    def learn(
        self,
        score: float,
        band: Complexity,
        strategy: Strategy,
        quality: float,
        cost_usd: float,
        latency_ms: float,
    ) -> None:
        """用一次执行轨迹更新学习层。

        - 计算奖励（质量 - 成本/延迟惩罚）
        - 更新 bandit 对应档位下该策略的均值
        - 同时保留阈值规则的微小漂移（让 fallback 也能随质量自适应）
        """
        reward = compute_reward(quality, cost_usd, latency_ms, self.reward_lambda, self.reward_mu)
        if self.learning and band is not None:
            self.bandit.update(band.value, strategy, reward)
        # 阈值规则的微小自适应（保持原行为）
        if quality < 0.5:
            self._drift -= 0.05
        elif quality > 0.9:
            self._drift += 0.01
        self._drift = max(-0.3, min(0.3, self._drift))

    # ---- 持久化 ----
    def save(self, path: str | None = None) -> None:
        p = path or self.state_path
        if p:
            _save_policy(self.bandit.to_dict(), p)

    def load(self, path: str | None = None) -> bool:
        p = path or self.state_path
        if not p:
            return False
        loaded = _load_policy(p)
        if loaded is not None:
            self.bandit = ContextualBandit.from_dict(loaded)
            return True
        return False
