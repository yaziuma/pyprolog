from typing import Dict, Optional

# from prolog.core.types import Variable, Term, Atom, Number, String, PrologType
# 上記のフルインポートは循環参照のリスクがあるため、型ヒントでは文字列リテラルを使用
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prolog.core.types import PrologType, Variable  # Variable はここでは不要かも


class BindingEnvironment:
    def __init__(self, parent: Optional["BindingEnvironment"] = None):
        self.bindings: Dict[str, "PrologType"] = {}
        self.parent: Optional["BindingEnvironment"] = parent

    def bind(self, var_name: str, value: "PrologType"):
        """変数を値に束縛する"""
        # Prologでは再束縛は通常単一化の失敗として扱われる。
        # ここでは単純に上書きするが、単一化ロジックで矛盾をチェックする。
        # 既に束縛されていて、異なる値に束縛しようとした場合は、
        # unify ロジック側で失敗として扱われるべき。
        # ここでチェックを入れると、unify のロジックと重複する可能性がある。
        # 例えば、X=Y, X=a. の場合、Yもaに束縛される。
        # unify(X,Y) -> env1 (X -> Y)
        # unify(X,a) in env1 -> deref(X)=Y, deref(a)=a. unify(Y,a) -> env2 (X->Y, Y->a)
        # この bind は、dereference 後の変数に対する束縛に使われる。
        self.bindings[var_name] = value

    def get_value(self, var_name: str) -> Optional["PrologType"]:
        """変数の値を取得する。見つからなければNoneを返す"""
        if var_name in self.bindings:
            return self.bindings[var_name]
        if self.parent:
            return self.parent.get_value(var_name)
        return None

    def copy(self) -> "BindingEnvironment":
        """環境のシャローコピーを作成する"""
        # 親環境は共有し、現在のレベルの束縛のみをコピーする
        new_env = BindingEnvironment(self.parent)
        new_env.bindings = self.bindings.copy()  # 現在の束縛をコピー
        return new_env

    def __repr__(self) -> str:
        items = []
        env: Optional[BindingEnvironment] = self
        level = 0
        while env:
            level_items = []
            for k, v in env.bindings.items():
                # 変数自身への束縛は表示しない (例: X=X)
                if (
                    isinstance(v, Variable) and v.name == k
                ):  # Variable型をインポートする必要がある
                    continue
                level_items.append(f"{k}: {v}")
            if level_items:
                items.append(f"L{level}: {{{', '.join(level_items)}}}")
            env = env.parent
            level += 1
        return "Env(" + "; ".join(items) + ")"


# __repr__ で Variable を使うため、ここでインポート (TYPE_CHECKING の外)
from prolog.core.types import Variable
