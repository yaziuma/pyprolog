from prolog.core.types import (
    Term,
    Variable,
    Atom,
    Number,
    Rule,
    Fact,
    PrologType,
    ListTerm,
    String,
)
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.errors import PrologError
from typing import TYPE_CHECKING, Tuple, Iterator, List, Union, Dict  # Dict を追加

if TYPE_CHECKING:
    from prolog.runtime.interpreter import (
        Runtime,
    )  # 循環インポートを避けるための型ヒント


class LogicInterpreter:
    def __init__(self, rules: List[Union[Rule, Fact]], runtime: "Runtime"):
        self.rules: List[Union[Rule, Fact]] = rules
        self.runtime: "Runtime" = runtime  # Runtime への参照を保持
        self._unique_var_counter = 0  # 変数リネーム用

    def _rename_variables(
        self, term_or_rule: Union[PrologType, Rule, Fact]
    ) -> Union[PrologType, Rule, Fact]:
        """ルールまたは項内の変数を一意な名前にリネームする（深層コピー）"""
        self._unique_var_counter += 1
        mapping: Dict[str, Variable] = {}  # 元の変数名 -> 新しい変数オブジェクト

        def rename_recursive(current_term: PrologType) -> PrologType:
            if isinstance(current_term, Variable):
                if current_term.name not in mapping:
                    new_name = f"_V{self._unique_var_counter}_{current_term.name}"
                    mapping[current_term.name] = Variable(new_name)
                return mapping[current_term.name]
            elif isinstance(current_term, Term):
                # functor は Atom なのでリネーム不要
                new_args = [rename_recursive(arg) for arg in current_term.args]
                return Term(current_term.functor, new_args)
            elif isinstance(current_term, ListTerm):  # ListTerm も考慮
                new_elements = [rename_recursive(el) for el in current_term.elements]
                new_tail_val = current_term.tail
                renamed_tail_val = (
                    rename_recursive(new_tail_val) if new_tail_val is not None else None
                )
                # ListTermのtailはVariable, Atom, ListTerm, Noneのいずれか
                if not (
                    isinstance(renamed_tail_val, (Variable, Atom, ListTerm))
                    or renamed_tail_val is None
                ):
                    raise PrologError(
                        f"Internal error: Renamed tail of ListTerm is not a valid type: {type(renamed_tail_val)}"
                    )
                return ListTerm(new_elements, renamed_tail_val)
            # Atom, Number, String は変数を内部に持たないのでそのまま返す
            return current_term

        if isinstance(term_or_rule, Rule):
            renamed_head = rename_recursive(term_or_rule.head)
            renamed_body = rename_recursive(term_or_rule.body)
            # Rule の head と body は Term であることが期待される
            if not isinstance(renamed_head, Term) or not isinstance(renamed_body, Term):
                raise PrologError("Internal error: Renamed head or body is not a Term.")
            return Rule(renamed_head, renamed_body)
        elif isinstance(term_or_rule, Fact):
            renamed_head = rename_recursive(term_or_rule.head)
            if not isinstance(renamed_head, Term):
                raise PrologError("Internal error: Renamed head of Fact is not a Term.")
            return Fact(renamed_head)
        else:  # PrologType (Term, Atom, Variable, etc.)
            return rename_recursive(term_or_rule)

    def unify(
        self, term1: PrologType, term2: PrologType, env: BindingEnvironment
    ) -> Tuple[bool, BindingEnvironment]:
        """
        2つの項を現在の環境で単一化しようと試みる。
        成功すれば (True, 新しい環境)、失敗すれば (False, 元の環境) を返す。
        """
        # 新しい環境を作成して、元の環境に影響を与えないようにする
        current_env = env.copy()

        # dereference: 変数をその束縛値で置き換える (再帰的に)
        t1 = self.dereference(term1, current_env)
        t2 = self.dereference(term2, current_env)

        if t1 == t2:  # 同一の具体化された項 (occurs check は別途必要なら)
            return True, current_env

        if isinstance(t1, Variable):
            # Occurs check: t1 が t2 内に出現しないか確認
            if self._occurs_check(t1, t2, current_env):
                return False, env  # Occurs check 失敗、元の環境を返す
            current_env.bind(t1.name, t2)
            return True, current_env
        if isinstance(t2, Variable):
            # Occurs check: t2 が t1 内に出現しないか確認
            if self._occurs_check(t2, t1, current_env):
                return False, env  # Occurs check 失敗
            current_env.bind(t2.name, t1)
            return True, current_env

        if isinstance(t1, Atom) and isinstance(t2, Atom):
            return t1.name == t2.name, current_env
        if isinstance(t1, Number) and isinstance(t2, Number):
            return t1.value == t2.value, current_env
        if isinstance(t1, String) and isinstance(t2, String):  # Stringの単一化
            return t1.value == t2.value, current_env

        if isinstance(t1, Term) and isinstance(t2, Term):
            if t1.functor == t2.functor and len(t1.args) == len(t2.args):
                temp_env = current_env.copy()  # 各引数の単一化は一時的な環境で行う
                all_args_unified = True
                for i in range(len(t1.args)):
                    unified, temp_env_after_arg_unify = self.unify(
                        t1.args[i], t2.args[i], temp_env
                    )
                    if not unified:
                        all_args_unified = False
                        break
                    temp_env = temp_env_after_arg_unify  # 成功した環境を引き継ぐ

                if all_args_unified:
                    return True, temp_env  # 全引数が成功した場合の環境を返す
                else:
                    return False, env  # 失敗時は元の環境を返す

        # ListTerm の単一化は、パーサーが '.'/2 形式の Term を生成するため、
        # Term の単一化ロジックでカバーされる。
        # もし ListTerm 型を直接扱う場合は、ここに追加のロジックが必要。

        return False, env  # 上記のいずれにもマッチしない場合は単一化失敗

    def _occurs_check(
        self, var: Variable, term: PrologType, env: BindingEnvironment
    ) -> bool:
        """var が term 内に出現するかどうかをチェック (env を考慮)"""
        term_deref = self.dereference(term, env)
        if var == term_deref:  # 変数自体が具体化された項と一致
            return True
        if isinstance(term_deref, Term):
            for arg in term_deref.args:
                if self._occurs_check(var, arg, env):
                    return True
        # ListTerm の場合も再帰的にチェック (現在はTermでカバー)
        return False

    def dereference(self, term: PrologType, env: BindingEnvironment) -> PrologType:
        """変数を環境内でその値に置き換える（再帰的）"""
        if isinstance(term, Variable):
            bound_value = env.get_value(term.name)
            if (
                bound_value is not None and bound_value != term
            ):  # 自分自身への束縛はループを避ける
                # 循環参照を避けるため、dereference の深さに制限を設けるか、
                # 既に訪れた変数を記録する必要があるかもしれない。
                # ここでは単純な再帰。
                return self.dereference(bound_value, env)
        return term

    def solve_goal(
        self, goal: Term, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """
        単一のゴールを解決し、成功した環境のイテレータを返す。
        """
        # 組み込み述語の処理 (Runtime側でも処理されるが、LogicInterpreter固有のものもここに)
        # 例: true/0, fail/0, !/0 (カット)
        if isinstance(goal, Atom):  # アトムのゴール (例: true, fail)
            if goal.name == "true":
                yield env
                return
            elif goal.name == "fail":
                return  # 何も yield しない (失敗)
            # 他のアトムのゴールは通常の述語として扱われる (functor=goal, args=[])
            # その場合、Term(goal, []) の形に変換して処理を続けるか、
            # あるいは、Atom のゴールは常にアリティ0の述語として扱う。
            # ここでは、Atom のゴールはアリティ0の Term と同等とみなし、
            # データベース検索に進む。
            # goal = Term(goal, []) # この変換は呼び出し元 (Runtime.execute) で行う方が良いかも

        if not isinstance(goal, Term):
            # 通常、ゴールは Term (または Atom でアリティ0の Term と解釈される)
            raise PrologError(f"Goal must be a Term or Atom, got {type(goal)}: {goal}")

        # カットの処理
        if goal.functor.name == "!" and not goal.args:
            # カットは特殊な処理。ここでは単純に成功として現在の環境を返す。
            # バックトラックの制御は呼び出し元 (Runtime.execute や、より高レベルのループ) で行う。
            # LogicInterpreter はカットの存在を通知するメカニズムが必要かもしれない。
            # ここでは、カット自体は成功する述語として扱う。
            yield env
            # TODO: カットのフラグを立てるなどして、バックトラックを制限する処理を Runtime 側で行う
            return

        # データベース (ルールとファクト) を検索
        for db_entry in self.rules:
            renamed_entry = self._rename_variables(
                db_entry
            )  # ルール/ファクト内の変数をリネーム

            current_head: Term
            if isinstance(renamed_entry, Rule):
                current_head = renamed_entry.head
            elif isinstance(renamed_entry, Fact):
                current_head = renamed_entry.head
            else:
                # _rename_variables が Rule か Fact を返すはず
                raise PrologError(
                    "Internal error: Renamed DB entry is not Rule or Fact."
                )

            # ゴールとヘッドの単一化を試みる
            unified, new_env_after_unify = self.unify(goal, current_head, env)

            if unified:
                if isinstance(renamed_entry, Fact):
                    yield new_env_after_unify  # ファクトなら成功
                elif isinstance(renamed_entry, Rule):
                    # ルールの場合、ボディのゴールを解決する
                    # ボディがコンジャンクション (Term(',', G1, G2)) の場合、再帰的に解決
                    # Runtime.execute を使ってボディを解決 (Runtimeが演算子や組み込みを処理できるため)
                    # yield from self.runtime.execute(renamed_entry.body, new_env_after_unify)
                    # 上記は Runtime の execute を直接呼ぶ。
                    # LogicInterpreter は論理的な解決に集中し、Runtime が全体のフローを制御する。
                    # ここでは、ルールのボディを解決するためのイテレータを返す。
                    # Runtime.execute がこのイテレータを処理する。

                    # solve_conjunction を使うか、Runtime に委譲するか。
                    # ここでは、Runtime.execute がコンジャンクションも扱えると仮定し、
                    # 単一のボディゴールを渡す。
                    # コンジャンクションの処理は Runtime.execute 内で行われる。
                    # (例: `Term(',', G1, G2)` が来たら、G1 を解決し、その結果で G2 を解決)

                    # この solve_goal は単一のゴールを解決する。
                    # ルールのボディも単一のゴール (コンジャンクションを含む) である。
                    # そのため、Runtime.execute にボディを渡すのが適切。
                    yield from self.runtime.execute(
                        renamed_entry.body, new_env_after_unify
                    )
