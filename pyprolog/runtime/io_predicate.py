"""
IOPredicate基底クラス

入出力述語の共通処理を統合し、テンプレートメソッドパターンを使用して
統一入力システムとの統合を提供する。
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any, TYPE_CHECKING
import logging

from pyprolog.core.types import PrologType, Atom, Number
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.errors import PrologError
from pyprolog.runtime.builtins import BuiltinPredicate, try_convert_atom_to_number

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime

logger = logging.getLogger(__name__)


class IOPredicate(BuiltinPredicate, ABC):
    """
    入出力述語の共通基底クラス
    
    テンプレートメソッドパターンを使用し、共通処理を基底クラスに集約。
    サブクラスは入力タイプ固有の処理のみ実装する。
    """
    
    def __init__(self, *args):
        """
        コンストラクタ
        
        Args:
            *args: Prolog述語の引数
        """
        super().__init__(*args)
        self._validate_arguments()
    
    # ============================================================================
    # 抽象メソッド（サブクラスで実装必須）
    # ============================================================================
    
    @abstractmethod
    def _get_expected_arg_count(self) -> int:
        """
        期待する引数数を返す
        
        Returns:
            int: 期待する引数数
        """
        pass
    
    @abstractmethod 
    def _get_predicate_name(self) -> str:
        """
        述語名を返す
        
        Returns:
            str: 述語名（例: "get_char", "read_line"）
        """
        pass
    
    @abstractmethod
    def _get_input_type(self) -> str:
        """
        入力タイプを返す（統一入力システム用）
        
        Returns:
            str: 入力タイプ（例: "char", "line", "peek_char"）
        """
        pass
    
    @abstractmethod
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """
        入力値をPrologタームに変換
        
        Args:
            input_value: 入力値（Noneの場合EOF）
            
        Returns:
            PrologType: 変換されたPrologターム
        """
        pass
    
    # ============================================================================
    # 共通実装（テンプレートメソッドパターン）
    # ============================================================================
    
    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """
        共通実行フロー（テンプレートメソッド）
        
        以下の手順で実行:
        1. 統一入力システム経由で入力取得
        2. 入力値をPrologタームに変換  
        3. 引数と統一化実行
        
        Args:
            runtime: Prolog実行環境
            env: 束縛環境
            
        Yields:
            BindingEnvironment: 統一化成功時の束縛環境
        """
        try:
            # Step 1: 統一入力システム経由で入力取得
            input_value = self._request_input(runtime)
            
            # Step 2: Prologターム変換
            target_term = self._convert_to_prolog_term(input_value)
            
            # Step 3: 統一化実行
            yield from self._unify_with_argument(runtime, env, target_term)
            
        except Exception as e:
            # テスト用例外（PrologInputRequiredException）は再発生させる
            if "PrologInputRequiredException" in e.__class__.__name__:
                raise
            # その他のエラーはログ出力後、述語失敗
            logger.error(f"{self._get_predicate_name()}/1 execution error: {e}")
            return  # 述語失敗（何もyieldしない）
    
    def _validate_arguments(self):
        """
        引数数検証
        
        Raises:
            PrologError: 引数数が不正な場合
        """
        expected_count = self._get_expected_arg_count()
        actual_count = len(self.args)
        
        if actual_count != expected_count:
            raise PrologError(
                f"{self._get_predicate_name()}/{expected_count} expects "
                f"{expected_count} argument(s), got {actual_count}"
            )
    
    def _request_input(self, runtime: "Runtime") -> Optional[str]:
        """
        統一入力システム経由での入力要求
        
        【重要】ここで真の継続実行が発生する可能性がある。
        スレッドモード時は、この呼び出しでスレッドブロッキングが発生し、
        入力取得まで実行が中断される。しかし、スタックフレームは完全保持。
        
        Args:
            runtime: Prolog実行環境
            
        Returns:
            Optional[str]: 入力値（Noneの場合EOF）
        """
        # 統一入力システムが利用可能かチェック
        if hasattr(runtime.io_manager, 'request_input'):
            # 新しい統一入力システム使用
            return runtime.io_manager.request_input(
                input_type=self._get_input_type(),
                predicate_name=self._get_predicate_name(),
                prompt=self._get_prompt(),
                **self._get_additional_request_params()
            )
        else:
            # フォールバック: 従来方式
            return self._request_input_legacy(runtime)
    
    def _request_input_legacy(self, runtime: "Runtime") -> Optional[str]:
        """
        従来方式による入力処理（フォールバック）
        
        Args:
            runtime: Prolog実行環境
            
        Returns:
            Optional[str]: 入力値
        """
        input_type = self._get_input_type()
        if input_type == "char":
            result = runtime.io_manager.read_char_from_current()
            return result if result else None
        elif input_type == "line":
            return runtime.io_manager.read_line_from_current()
        elif input_type == "peek_char":
            result = runtime.io_manager.peek_char_from_current()
            return result if result else None
        else:
            logger.error(f"Unknown input_type in legacy mode: {input_type}")
            return None
    
    def _unify_with_argument(
        self, 
        runtime: "Runtime", 
        env: BindingEnvironment, 
        target_term: PrologType
    ) -> Iterator[BindingEnvironment]:
        """
        引数との統一化（共通処理）
        
        Args:
            runtime: Prolog実行環境
            env: 束縛環境
            target_term: 統一化対象のPrologターム
            
        Yields:
            BindingEnvironment: 統一化成功時の新しい束縛環境
        """
        prolog_arg = self.args[0]  # 通常、最初の引数が対象変数
        
        unified, next_env = runtime.logic_interpreter.unify(
            prolog_arg, target_term, env
        )
        
        if unified:
            yield next_env
    
    # ============================================================================
    # ユーティリティメソッド（サブクラスでオーバーライド可能）
    # ============================================================================
    
    def _get_prompt(self) -> str:
        """
        プロンプト文字列を取得
        
        Returns:
            str: プロンプト文字列
        """
        return f"{self._get_predicate_name()}: "
    
    def _handle_eof(self) -> Atom:
        """
        EOF処理（共通実装）
        
        Returns:
            Atom: "end_of_file"原子
        """
        return Atom("end_of_file")
    
    def _try_convert_to_number(self, value: str) -> Optional[PrologType]:
        """
        数値変換試行（共通ユーティリティ）
        
        Args:
            value: 変換対象文字列
            
        Returns:
            Optional[PrologType]: 数値変換成功時はNumber、失敗時はNone
        """
        if not value:
            return None
            
        number_value = try_convert_atom_to_number(value)
        if number_value is not None:
            return Number(number_value)
        return None
    
    def _get_additional_request_params(self) -> Dict[str, Any]:
        """
        追加の入力要求パラメータ
        
        サブクラスで特別なパラメータが必要な場合にオーバーライド
        （例: peek_charの非破壊的読み取りフラグ）
        
        Returns:
            Dict[str, Any]: 追加パラメータ辞書
        """
        return {}