from typing import TYPE_CHECKING, Optional

import rpds

_MISSING = object()

if TYPE_CHECKING:
    from pyprolog.core.types import PrologType


class BindingEnvironment:
    def __init__(
        self,
        parent: Optional["BindingEnvironment"] = None,
        bindings: rpds.HashTrieMap | None = None,
        stats: dict | None = None,
        stats_enabled: bool = False,
    ):
        self.bindings: rpds.HashTrieMap = (
            bindings if bindings is not None else rpds.HashTrieMap()
        )
        self.parent: BindingEnvironment | None = parent
        self.stats_enabled = stats_enabled
        self.stats = stats or {
            "deref_calls": 0,
            "deref_steps": 0,
            "occurs_calls": 0,
            "unify_calls": 0,
            "term_allocs": 0,
            "term_allocs_rename": 0,
            "term_allocs_deep_deref": 0,
            "term_allocs_other": 0,
            "solve_calls_total": 0,
            "solve_calls_by_pred": {},
            "candidate_entries_scanned_total": 0,
            "candidate_entries_scanned_by_pred": {},
            "unify_success_total": 0,
            "unify_fail_total": 0,
            "unify_success_by_pred": {},
            "builtin_calls_by_name": {},
            "index_hit_total": 0,
            "index_miss_total": 0,
            "index2_hit": 0,
            "index2_miss_or_fallback": 0,
            "avg_candidates_per_goal": 0.0,
            "current_goal_key": None,
        }

    def bind(self, var_name: str, value: "PrologType"):
        """変数を値に束縛する"""
        self.bindings = self.bindings.insert(var_name, value)

    def get_value(self, var_name: str) -> Optional["PrologType"]:
        """変数の値を取得する。見つからなければNoneを返す"""
        value = self.bindings.get(var_name, _MISSING)
        if value is not _MISSING:
            return value
        if self.parent:
            return self.parent.get_value(var_name)
        return None

    def is_unbound(self, var_name: str) -> bool:
        """Checks if a variable is unbound in the current environment and its parents."""
        return self.get_value(var_name) is None

    def copy(self) -> "BindingEnvironment":
        """環境のシャローコピーを作成する"""
        return BindingEnvironment(
            self.parent,
            bindings=self.bindings,
            stats=self.stats,
            stats_enabled=self.stats_enabled,
        )

    def __repr__(self) -> str:
        from pyprolog.core.types import Variable

        items = []
        env: BindingEnvironment | None = self
        level = 0
        while env:
            level_items = []
            for k, v in env.bindings.items():
                if isinstance(v, Variable) and v.name == k:
                    continue
                level_items.append(f"{k}: {v}")
            if level_items:
                items.append(f"L{level}: {{{', '.join(level_items)}}}")
            env = env.parent
            level += 1
        return "Env(" + "; ".join(items) + ")"

    def merge_with(self, other):
        """
        他の環境またはバインディング辞書とマージ

        Args:
            other: マージする対象（BindingEnvironmentまたはdict）

        Returns:
            BindingEnvironment: マージされた新しい環境
        """
        merged = self.copy()

        if isinstance(other, BindingEnvironment):
            for var_name, value in other.bindings.items():
                merged.bind(var_name, value)

            if other.parent:
                if merged.parent:
                    merged.parent = merged.parent.merge_with(other.parent)
                else:
                    merged.parent = other.parent.copy()
        elif isinstance(other, dict):
            for var_name, value in other.items():
                merged.bind(var_name, value)

        return merged

    def to_dict(self):
        """
        バインディング環境を辞書に変換
        自己参照（変数が自分自身に束縛されている）は除外される
        """
        from pyprolog.core.types import Variable

        result = {}
        if self.parent:
            result.update(self.parent.to_dict())

        for k, v in self.bindings.items():
            # 自己参照をスキップ
            if isinstance(v, Variable) and v.name == k:
                continue
            result[k] = v
        return result
