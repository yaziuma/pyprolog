# IOPredicate基底クラス詳細設計

## 1. 設計概要

> **用語**: 詳細な定義は[用語集](../glossary.md)を参照

### 1.1 目的
- 入出力述語の共通処理を統合
- **統一入力システム（Unified Input System）**への統一インターフェース提供
- コードの重複削減と保守性向上

### 1.2 クラス階層
```
BuiltinPredicate
    ↓
IOPredicate (抽象基底クラス)
    ↓
├── GetCharPredicate
├── ReadLinePredicate  
├── PeekCharPredicate
└── 将来の入力述語...
```

## 2. IOPredicate基底クラス実装

### 2.1 完全な実装

```python
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
import threading
import time

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
            # エラーログ出力後、述語失敗
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
        return runtime.io_manager.request_input(
            input_type=self._get_input_type(),
            predicate_name=self._get_predicate_name(),
            prompt=self._get_prompt()
        )
    
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
```

## 3. 具体的述語実装例

### 3.1 GetCharPredicate実装

```python
class GetCharPredicate(IOPredicate):
    """get_char/1述語実装"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "get_char"
    
    def _get_input_type(self) -> str:
        return "char"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """
        文字入力のPrologターム変換
        
        変換ルール:
        - EOF (None or "") → Atom("end_of_file")
        - 数字文字 → Number
        - その他文字 → Atom
        - 複数文字の場合は最初の文字のみ使用
        """
        if input_value is None or input_value == "":
            return self._handle_eof()
        
        # 最初の文字のみ使用
        char = input_value[0] if len(input_value) > 0 else ""
        
        if char.isdigit():
            return Number(int(char))
        else:
            return Atom(char)
    
    def _get_prompt(self) -> str:
        return "文字を入力してください: "
```

### 3.2 ReadLinePredicate実装

```python
class ReadLinePredicate(IOPredicate):
    """read_line/1述語実装"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "read_line"
    
    def _get_input_type(self) -> str:
        return "line"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """
        行入力のPrologターム変換
        
        変換ルール:
        - EOF (None) → Atom("end_of_file")  
        - 数値変換可能 → Number
        - その他 → Atom
        """
        if input_value is None:
            return self._handle_eof()
        
        # 数値変換試行
        number_term = self._try_convert_to_number(input_value)
        return number_term if number_term else Atom(input_value)
    
    def _get_prompt(self) -> str:
        return "行を入力してください: "
```

### 3.3 PeekCharPredicate実装

```python
class PeekCharPredicate(IOPredicate):
    """peek_char/1述語実装（非破壊的読み取り）"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "peek_char"
    
    def _get_input_type(self) -> str:
        return "peek_char"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """覗き見文字のPrologターム変換"""
        if input_value is None or input_value == "":
            return self._handle_eof()
        return Atom(input_value)
    
    def _get_additional_request_params(self) -> Dict[str, Any]:
        """非破壊的読み取りフラグ"""
        return {"non_destructive": True}
    
    def _get_prompt(self) -> str:
        return "peek_char: "
```

## 4. 統合効果

### 4.1 コード削減効果

**統合前 (現在のbuiltins.py):**
```python
# GetCharPredicate: 94行
# ReadLinePredicate: 37行  
# PeekCharPredicate: 80行
# 合計: 211行 + 重複ロジック
```

**統合後:**
```python
# IOPredicate基底クラス: 120行（共通処理）
# GetCharPredicate: 25行
# ReadLinePredicate: 20行
# PeekCharPredicate: 25行
# 合計: 190行（重複なし）
```

**削減効果: 約20行 + 重複ロジック除去**

### 4.2 保守性向上

- **共通ロジック修正**: 1箇所のみ
- **新述語追加**: テンプレートに従い高速実装
- **エラーハンドリング**: 一貫した処理
- **テスト**: 基底クラステストで網羅的検証

### 4.3 拡張性

```python
# 新しい入力述語の実装例
class ReadPasswordPredicate(IOPredicate):
    def _get_input_type(self) -> str:
        return "password"
    
    def _get_additional_request_params(self) -> Dict[str, Any]:
        return {"mask_char": "*", "echo": False}
    
    # 他は基底クラスの共通処理を活用
```

この設計により、入出力述語の実装が大幅に簡素化され、統一入力システムとの統合も自然に実現できます。