"""
Prolog構文フォーマッター

事実・ルールを標準Prolog構文で整形する機能を提供
"""

from typing import List, Union, Optional
from pyprolog.core.types import Rule, Fact, Term, Atom, Variable, Number, PrologType
import logging
from pyprolog.util.functor_mapper import FunctorMapper
from pyprolog.util.variable_mapper import VariableMapper

logger = logging.getLogger(__name__)


class PrologFormatter:
    """Prolog構文フォーマッター"""

    def __init__(
        self,
        variable_mapper: Optional[VariableMapper] = None,
        functor_mapper: Optional[FunctorMapper] = None,
    ):
        """
        フォーマッターを初期化

        Args:
            variable_mapper: 変数名マッピング用オブジェクト
            functor_mapper: ファンクター名マッピング用オブジェクト
        """
        self.variable_mapper = variable_mapper
        self.functor_mapper = functor_mapper

    def format_fact(self, fact: Fact) -> str:
        """
        事実をProlog構文文字列に変換

        Args:
            fact: 変換対象の事実

        Returns:
            Prolog構文文字列
        """
        try:
            term_str = self._format_term(fact.head)
            return f"{term_str}."
        except Exception as e:
            logger.warning("Failed to format fact %s: %s", fact, e)
            return f"% Error formatting fact: {fact}"

    def format_rule(self, rule: Rule) -> str:
        """
        ルールをProlog構文文字列に変換

        Args:
            rule: 変換対象のルール

        Returns:
            Prolog構文文字列
        """
        try:
            head_str = self._format_term(rule.head)
            body_str = self._format_term(rule.body)
            return f"{head_str} :- {body_str}."
        except Exception as e:
            logger.warning("Failed to format rule %s: %s", rule, e)
            return f"% Error formatting rule: {rule}"

    def format_rules_list(self, rules: List[Union[Rule, Fact]]) -> str:
        """
        ルール・事実リストの一括変換

        Args:
            rules: 変換対象のルール・事実リスト

        Returns:
            整形されたProlog構文文字列
        """
        if not rules:
            return "% Empty knowledge base\n"

        formatted_lines = []

        # 述語別にグループ化
        predicate_groups = self._group_by_predicate(rules)

        for predicate_key in sorted(predicate_groups.keys()):
            predicate_rules = predicate_groups[predicate_key]

            # 述語ごとにコメントヘッダーを追加
            formatted_lines.append(f"% {predicate_key}")

            # 各ルール・事実を整形
            for rule in predicate_rules:
                if isinstance(rule, Fact):
                    formatted_lines.append(self.format_fact(rule))
                elif isinstance(rule, Rule):
                    formatted_lines.append(self.format_rule(rule))
                else:
                    logger.warning("Unknown rule type: %s", type(rule))
                    formatted_lines.append(f"% Unknown rule type: {rule}")

            formatted_lines.append("")  # 述語グループ間の空行

        return "\n".join(formatted_lines)

    def format_predicate_rules(
        self, rules: List[Union[Rule, Fact]], predicate_name: str, arity: int
    ) -> str:
        """
        特定述語のルール・事実のみを整形

        Args:
            rules: ルール・事実リスト
            predicate_name: 対象述語名
            arity: 対象述語のアリティ

        Returns:
            整形されたProlog構文文字列
        """
        filtered_rules = self._filter_rules_by_predicate(rules, predicate_name, arity)

        if not filtered_rules:
            return f"% No clauses found for {predicate_name}/{arity}\n"

        formatted_lines = [f"% {predicate_name}/{arity}"]

        for rule in filtered_rules:
            if isinstance(rule, Fact):
                formatted_lines.append(self.format_fact(rule))
            elif isinstance(rule, Rule):
                formatted_lines.append(self.format_rule(rule))

        return "\n".join(formatted_lines) + "\n"

    def _format_term(self, term: PrologType) -> str:
        """
        項を文字列に変換

        Args:
            term: 変換対象の項

        Returns:
            項の文字列表現
        """
        if isinstance(term, Atom):
            return self._format_atom(term)
        elif isinstance(term, Variable):
            return self._format_variable(term)
        elif isinstance(term, Number):
            return str(term.value)
        elif isinstance(term, Term):
            return self._format_compound_term(term)
        else:
            logger.warning("Unknown term type: %s", type(term))
            return str(term)

    def _format_atom(self, atom: Atom) -> str:
        """
        Atomを文字列に変換

        Args:
            atom: 変換対象のAtom

        Returns:
            Atom文字列表現
        """
        # ファンクターマッピングがある場合は日本語に復元
        if self.functor_mapper:
            original_name = self.functor_mapper.map_english_to_non_ascii(atom.name)
            if original_name != atom.name:
                return original_name

        # 特殊文字が含まれている場合はクォートする
        if self._needs_quotes(atom.name):
            return f"'{atom.name}'"

        return atom.name

    def _format_variable(self, variable: Variable) -> str:
        """
        Variableを文字列に変換

        Args:
            variable: 変換対象のVariable

        Returns:
            Variable文字列表現
        """
        # 変数マッピングがある場合は日本語に復元
        if self.variable_mapper:
            original_name = self.variable_mapper.map_english_to_japanese(variable.name)
            if original_name != variable.name:
                return original_name

        return variable.name

    def _format_compound_term(self, term: Term) -> str:
        """
        複合項を文字列に変換

        Args:
            term: 変換対象の複合項

        Returns:
            複合項の文字列表現
        """
        functor_str = self._format_term(term.functor)

        if not term.args:
            return functor_str

        # リスト記法の特別処理
        if (
            isinstance(term.functor, Atom)
            and term.functor.name == "."
            and len(term.args) == 2
        ):
            return self._format_list(term)

        # 演算子の特別処理
        if self._is_infix_operator(term):
            return self._format_infix_operator(term)

        # 通常の関数記法
        args_str = ", ".join(self._format_term(arg) for arg in term.args)
        return f"{functor_str}({args_str})"

    def _format_list(
        self, term: Term, collected_elements: Optional[List[str]] = None
    ) -> str:
        """
        リスト構造を[a,b,c]形式で整形

        Args:
            term: リスト構造のTerm
            collected_elements: 既に収集された要素（再帰用）

        Returns:
            リスト文字列表現
        """
        if collected_elements is None:
            collected_elements = []

        if (
            isinstance(term, Term)
            and isinstance(term.functor, Atom)
            and term.functor.name == "."
        ):
            # [Head|Tail]構造
            if len(term.args) >= 1:
                head_str = self._format_term(term.args[0])
                collected_elements.append(head_str)

                if len(term.args) >= 2:
                    tail = term.args[1]
                    # 空リストで終端
                    if isinstance(tail, Atom) and tail.name == "[]":
                        return f"[{', '.join(collected_elements)}]"
                    # リスト続行
                    elif (
                        isinstance(tail, Term)
                        and isinstance(tail.functor, Atom)
                        and tail.functor.name == "."
                    ):
                        return self._format_list(tail, collected_elements)
                    # 不完全リスト [a,b|Tail]
                    else:
                        tail_str = self._format_term(tail)
                        return f"[{', '.join(collected_elements)}|{tail_str}]"

        # 空リスト
        if isinstance(term, Atom) and term.name == "[]":
            if collected_elements:
                return f"[{', '.join(collected_elements)}]"
            else:
                return "[]"

        # リスト構造でない場合は通常の項として処理
        return self._format_term(term)

    def _is_infix_operator(self, term: Term) -> bool:
        """
        中置演算子かどうかを判定

        Args:
            term: 判定対象のTerm

        Returns:
            中置演算子の場合True
        """
        if not isinstance(term.functor, Atom) or len(term.args) != 2:
            return False

        infix_operators = {
            "=",
            "\\=",
            "==",
            "\\==",
            "is",
            "=:=",
            "=\\=",
            "<",
            "=<",
            ">",
            ">=",
            "+",
            "-",
            "*",
            "/",
            "mod",
            "**",
            ",",
            ";",
            "->",
            "\\+",
        }

        return term.functor.name in infix_operators

    def _format_infix_operator(self, term: Term) -> str:
        """
        中置演算子を整形

        Args:
            term: 中置演算子のTerm

        Returns:
            中置演算子の文字列表現
        """
        left_str = self._format_term(term.args[0])
        right_str = self._format_term(term.args[1])
        operator = term.functor.name

        return f"{left_str} {operator} {right_str}"

    def _needs_quotes(self, atom_name: str) -> bool:
        """
        Atom名にクォートが必要かどうか判定

        Args:
            atom_name: Atom名

        Returns:
            クォートが必要な場合True
        """
        if not atom_name:
            return True

        # 小文字で始まり、英数字とアンダースコアのみの場合はクォート不要
        if atom_name[0].islower() and atom_name.replace("_", "").isalnum():
            return False

        # 演算子の場合はクォート不要
        operators = {
            "=",
            "\\=",
            "==",
            "\\==",
            "is",
            "=:=",
            "=\\=",
            "<",
            "=<",
            ">",
            ">=",
            "+",
            "-",
            "*",
            "/",
            "mod",
            "**",
            ",",
            ";",
            "->",
            "\\+",
            "!",
            "[]",
        }
        if atom_name in operators:
            return False

        # その他の場合はクォート必要
        return True

    def _group_by_predicate(self, rules: List[Union[Rule, Fact]]) -> dict:
        """
        ルール・事実を述語別にグループ化

        Args:
            rules: ルール・事実リスト

        Returns:
            述語名/アリティをキーとした辞書
        """
        groups = {}

        for rule in rules:
            try:
                if isinstance(rule, Fact):
                    head = rule.head
                elif isinstance(rule, Rule):
                    head = rule.head
                else:
                    continue

                predicate_key = self._get_predicate_key(head)
                if predicate_key not in groups:
                    groups[predicate_key] = []
                groups[predicate_key].append(rule)

            except Exception as e:
                logger.warning("Error grouping rule %s: %s", rule, e)
                continue

        return groups

    def _get_predicate_key(self, term: Term) -> str:
        """
        項から述語キー（name/arity）を取得

        Args:
            term: 対象の項

        Returns:
            述語キー文字列
        """
        if isinstance(term, Term):
            functor_name = self._get_functor_name(term.functor)
            arity = len(term.args)
            return f"{functor_name}/{arity}"
        elif isinstance(term, Atom):
            functor_name = self._get_functor_name(term)
            return f"{functor_name}/0"
        else:
            return f"unknown/{0}"

    def _get_functor_name(self, functor: PrologType) -> str:
        """
        ファンクターから名前を取得

        Args:
            functor: ファンクター

        Returns:
            ファンクター名
        """
        if isinstance(functor, Atom):
            # ファンクターマッピングで日本語復元を試行
            if self.functor_mapper:
                original_name = self.functor_mapper.map_english_to_non_ascii(
                    functor.name
                )
                return original_name
            return functor.name
        else:
            return str(functor)

    def _filter_rules_by_predicate(
        self, rules: List[Union[Rule, Fact]], predicate_name: str, arity: int
    ) -> List[Union[Rule, Fact]]:
        """
        指定述語のルール・事実をフィルタリング

        Args:
            rules: ルール・事実リスト
            predicate_name: 対象述語名
            arity: 対象アリティ

        Returns:
            フィルタされたルール・事実リスト
        """
        filtered = []

        for rule in rules:
            try:
                if isinstance(rule, Fact):
                    head = rule.head
                elif isinstance(rule, Rule):
                    head = rule.head
                else:
                    continue

                # 述語名・アリティをチェック
                if self._matches_predicate(head, predicate_name, arity):
                    filtered.append(rule)

            except Exception as e:
                logger.warning("Error filtering rule %s: %s", rule, e)
                continue

        return filtered

    def _matches_predicate(self, term: Term, predicate_name: str, arity: int) -> bool:
        """
        項が指定述語にマッチするかチェック

        Args:
            term: チェック対象の項
            predicate_name: 対象述語名
            arity: 対象アリティ

        Returns:
            マッチする場合True
        """
        if isinstance(term, Term):
            term_functor_name = self._get_functor_name(term.functor)
            term_arity = len(term.args)
        elif isinstance(term, Atom):
            term_functor_name = self._get_functor_name(term)
            term_arity = 0
        else:
            return False

        # 名前の完全一致またはマッピング一致をチェック
        name_match = term_functor_name == predicate_name

        # ファンクターマッピングがある場合は双方向チェック
        if not name_match and self.functor_mapper:
            # 日本語→英語マッピング
            mapped_predicate = self.functor_mapper.map_non_ascii_to_english(
                predicate_name
            )
            name_match = term_functor_name == mapped_predicate

            # 英語→日本語マッピング
            if not name_match:
                mapped_term = self.functor_mapper.map_english_to_non_ascii(
                    term_functor_name
                )
                name_match = mapped_term == predicate_name

        return name_match and term_arity == arity
