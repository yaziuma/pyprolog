"""
パターンマッチング機能

Prolog述語名、引数パターン、全文検索のマッチング処理を提供します。
"""

import re
from typing import Tuple, Union
from pyprolog.core.types import Term, Atom, Variable
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class PatternMatcher:
    """パターンマッチング処理を提供するクラス"""

    @staticmethod
    def match_predicate_name(pattern: str, term: Union[Term, Atom]) -> bool:
        """
        述語名のパターンマッチング

        Args:
            pattern: 検索パターン
            term: 検索対象の項

        Returns:
            マッチするかどうか
        """
        try:
            if isinstance(term, Term):
                functor_name = (
                    term.functor.name
                    if hasattr(term.functor, "name")
                    else str(term.functor)
                )
            elif isinstance(term, Atom):
                functor_name = term.name if hasattr(term, "name") else str(term)
            else:
                functor_name = str(term)

            # 完全一致
            if pattern == functor_name:
                return True

            # 部分一致（大文字小文字を無視）
            if pattern.lower() in functor_name.lower():
                return True

            # 正規表現マッチング（パターンが正規表現として有効な場合）
            try:
                if re.search(pattern, functor_name, re.IGNORECASE):
                    return True
            except re.error:
                pass

            return False

        except Exception as e:
            logger.warning(f"述語名マッチングエラー '{pattern}': {e}")
            return False

    @staticmethod
    def match_argument_pattern(pattern: str, term: Term) -> Tuple[bool, float]:
        """
        引数パターンマッチング

        Args:
            pattern: 検索パターン（例: "location(_, office)"）
            term: 検索対象の項

        Returns:
            (マッチするか, 信頼度)
        """
        try:
            # パターンをパースしてTermに変換
            pattern_term = PatternMatcher.parse_argument_pattern(pattern)

            # 単一化を試行
            is_match, confidence = PatternMatcher.unify_patterns(pattern_term, term)
            return is_match, confidence

        except Exception as e:
            logger.warning(f"引数パターンマッチングエラー '{pattern}': {e}")
            return False, 0.0

    @staticmethod
    def parse_argument_pattern(pattern: str) -> Term:
        """
        文字列パターンをTermオブジェクトに変換

        Args:
            pattern: パターン文字列

        Returns:
            解析されたTerm
        """
        try:
            from pyprolog.parser.scanner import Scanner
            from pyprolog.parser.parser import Parser

            scanner = Scanner(pattern)
            tokens = scanner.scan_tokens()
            parser = Parser(tokens)

            # パターンは単一の項として解析
            parsed_items = parser.parse()
            if parsed_items and len(parsed_items) > 0:
                # 最初の項を取得
                first_item = parsed_items[0]
                if hasattr(first_item, "head"):  # Rule or Fact
                    return first_item.head
                else:  # 直接Term
                    return first_item

            # フォールバック：シンプルなAtomとして処理
            return Atom(pattern)

        except Exception as e:
            logger.warning(f"パターン解析エラー '{pattern}': {e}")
            return Atom(pattern)

    @staticmethod
    def unify_patterns(pattern_term: Term, target_term: Term) -> Tuple[bool, float]:
        """
        パターン項と対象項の単一化を試行し、マッチ度を計算

        Args:
            pattern_term: パターン項
            target_term: 対象項

        Returns:
            (単一化成功, 信頼度)
        """
        try:
            # 基本的な構造比較
            if not isinstance(pattern_term, Term) or not isinstance(target_term, Term):
                return str(pattern_term) == str(target_term), 1.0 if str(
                    pattern_term
                ) == str(target_term) else 0.0

            # ファンクター名の比較
            pattern_functor = (
                pattern_term.functor.name
                if hasattr(pattern_term.functor, "name")
                else str(pattern_term.functor)
            )
            target_functor = (
                target_term.functor.name
                if hasattr(target_term.functor, "name")
                else str(target_term.functor)
            )

            if pattern_functor != target_functor:
                return False, 0.0

            # 引数の数の比較
            pattern_args = (
                pattern_term.args
                if hasattr(pattern_term, "args") and pattern_term.args
                else []
            )
            target_args = (
                target_term.args
                if hasattr(target_term, "args") and target_term.args
                else []
            )

            if len(pattern_args) != len(target_args):
                return False, 0.0

            # 引数の比較
            matches = 0
            total = len(pattern_args)

            for p_arg, t_arg in zip(pattern_args, target_args):
                if isinstance(p_arg, Variable):
                    # 変数は何でもマッチ
                    matches += 1
                elif str(p_arg) == str(t_arg):
                    # 完全一致
                    matches += 1
                elif PatternMatcher._is_wildcard(str(p_arg)):
                    # ワイルドカード（_）はマッチ
                    matches += 1

            if total == 0:
                confidence = 1.0  # 引数なしの場合は完全一致
            else:
                confidence = matches / total

            return confidence > 0.5, confidence

        except Exception as e:
            logger.warning(f"単一化エラー: {e}")
            return False, 0.0

    @staticmethod
    def _is_wildcard(arg_str: str) -> bool:
        """引数がワイルドカードかどうかを判定"""
        return arg_str.strip() in ["_", "X", "Y", "Z"] or arg_str.startswith("_")

    @staticmethod
    def _calculate_unification_confidence(pattern: Term, target: Term) -> float:
        """単一化の信頼度を計算"""
        if str(pattern) == str(target):
            return 1.0

        # 変数の数と具体的な値の数を比較
        pattern_vars = PatternMatcher._count_variables(pattern)
        target_vars = PatternMatcher._count_variables(target)

        if pattern_vars == 0 and target_vars == 0:
            return 1.0  # 完全一致

        # 変数が多いほど信頼度は低下
        confidence = max(0.1, 1.0 - (pattern_vars * 0.2))
        return confidence

    @staticmethod
    def _count_variables(term: Term) -> int:
        """項内の変数の数を数える"""
        count = 0

        def count_vars_recursive(t):
            nonlocal count
            if isinstance(t, Variable):
                count += 1
            elif isinstance(t, Term) and hasattr(t, "args") and t.args:
                for arg in t.args:
                    count_vars_recursive(arg)

        count_vars_recursive(term)
        return count
