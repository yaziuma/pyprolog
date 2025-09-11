# 実装仕様

## 7.1 ファイル構成

### 7.1.1 新規ファイル一覧

```
pyprolog/runtime/
├── unified_input_system.py     # 統一入力システムコア
├── input_event.py              # InputEvent クラス
├── input_handler.py            # InputHandler インターフェース
├── input_exceptions.py         # 入力関連例外
└── input_utils.py              # ユーティリティ関数

pyprolog/runtime/handlers/      # 標準ハンドラ（新規ディレクトリ）
├── __init__.py
├── mock_handler.py             # テスト用モックハンドラ
├── debug_handler.py            # デバッグハンドラ
└── migration_helpers.py        # 移行支援ヘルパー

tests/runtime/unified_input/    # テスト（新規ディレクトリ）
├── __init__.py
├── test_input_event.py
├── test_input_handler.py
├── test_unified_input_system.py
├── test_integration.py
└── test_compatibility.py
```

### 7.1.2 変更ファイル一覧

```
pyprolog/runtime/
├── io_manager.py               # UnifiedInputSystem統合
├── interpreter.py              # ハンドラ設定API追加
└── builtins.py                 # 述語クラス改修

pyprolog/runtime/
├── __init__.py                 # 新規クラスのエクスポート追加
```

### 7.1.3 モジュール依存関係

```
依存関係グラフ:

interpreter.py
    ↓
io_manager.py
    ↓
unified_input_system.py
    ↓ ↓ ↓
input_event.py  input_handler.py  input_exceptions.py
    ↓
input_utils.py

builtins.py → io_manager.py (既存)

テストモジュール:
test_*.py → 対応する実装モジュール
test_integration.py → 全コンポーネント
```

## 7.2 コーディング規約

### 7.2.1 命名規約

**クラス名:**
```python
# PascalCase
class InputEvent: pass
class UnifiedInputSystem: pass
class InputHandler: pass
class MockInputHandler: pass
```

**メソッド名・変数名:**
```python
# snake_case
def handle_input_request(): pass
def get_display_name(): pass
input_type = "char"
predicate_name = "get_char"
```

**定数:**
```python
# UPPER_SNAKE_CASE
class InputType:
    CHAR = "char"
    LINE = "line"
    DEFAULT_TIMEOUT = 30.0
```

**プライベートメンバ:**
```python
class UnifiedInputSystem:
    def __init__(self):
        self._handler = None           # プライベート
        self._handler_lock = None      # プライベート
        self.__internal_state = None   # 非常にプライベート（名前マングリング）
```

### 7.2.2 型ヒント仕様

**基本的な型ヒント:**
```python
from typing import Optional, Dict, List, Set, Any, Union, Callable
from abc import ABC, abstractmethod

class InputHandler(ABC):
    @abstractmethod
    def handle_input_request(self, event: 'InputEvent') -> Optional[str]:
        pass

class UnifiedInputSystem:
    def __init__(self) -> None:
        self._handler: Optional[InputHandler] = None
        self._event_history: List[InputEvent] = []
    
    def request_input(self, 
                     input_type: str, 
                     predicate_name: str, 
                     **kwargs: Any) -> Optional[str]:
        pass
```

**Generic型の使用:**
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class InputCache(Generic[T]):
    def __init__(self) -> None:
        self._cache: Dict[str, T] = {}
    
    def get(self, key: str) -> Optional[T]:
        return self._cache.get(key)
```

**型チェック用のフォワード参照:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime

class UnifiedInputSystem:
    def setup_runtime(self, runtime: 'Runtime') -> None:
        # フォワード参照使用
        pass
```

### 7.2.3 ドキュメント規約

**クラスドキュメント:**
```python
class UnifiedInputSystem:
    """
    統一入力システム - 入力要求の中央制御
    
    このクラスは全ての入力述語からの要求を統一的に処理し、
    利用者定義のInputHandlerまたはフォールバックストリームに
    ルーティングします。
    
    Attributes:
        _handler: 現在設定されている入力ハンドラ
        _fallback_stream: フォールバック用IOStream
        _event_history: 入力イベントの履歴
    
    Example:
        >>> system = UnifiedInputSystem()
        >>> system.set_input_handler(MyHandler())
        >>> result = system.request_input("char", "get_char")
    """
```

**メソッドドキュメント:**
```python
def request_input(self, input_type: str, predicate_name: str, **kwargs: Any) -> Optional[str]:
    """
    統一入力要求の処理
    
    指定された入力タイプと述語名に基づいてInputEventを生成し、
    設定されたハンドラまたはフォールバックストリームから入力を取得します。
    
    Args:
        input_type: 入力タイプ（"char", "line"等）
        predicate_name: 呼び出し元述語名
        **kwargs: 追加パラメータ（prompt, timeout等）
    
    Returns:
        入力値（文字列）、またはNone（EOF時）
    
    Raises:
        InputSystemError: システム設定エラー
        HandlerExecutionError: ハンドラ実行エラー
        FallbackError: フォールバック実行エラー
    
    Example:
        >>> result = system.request_input("char", "get_char", prompt="文字入力: ")
        >>> print(result)  # "a"
    """
```

**例外ドキュメント:**
```python
class HandlerExecutionError(InputHandlerError):
    """
    入力ハンドラ実行時のエラー
    
    ハンドラの handle_input_request() メソッド実行中に
    発生した例外をラップします。
    
    Attributes:
        event: エラー発生時のInputEvent
        cause: 元の例外
    """
```

## 7.3 実装順序

### 7.3.1 Phase 1 実装詳細

**Week 1-2: コアコンポーネント実装**

*Day 1-2: 基盤クラス実装*
```python
# 実装順序:
1. input_exceptions.py     # 例外クラス群
2. input_event.py          # InputEvent クラス
3. input_handler.py        # InputHandler インターフェース
4. input_utils.py          # ユーティリティ関数
```

*Day 3-4: 統一入力システム実装*
```python
# unified_input_system.py
5. UnifiedInputSystem クラスの基本実装
   - コンストラクタ
   - ハンドラ管理機能
   - 基本的な request_input() メソッド
```

*Day 5-7: IOManager統合*
```python
# io_manager.py 改修
6. UnifiedInputSystem インスタンス追加
7. 新しい request_input() API実装
8. レガシーAPI互換性レイヤー実装
```

**Week 3: テスト実装**
```python
# テストファイル実装順序:
9. test_input_event.py           # InputEvent 単体テスト
10. test_unified_input_system.py # UnifiedInputSystem 単体テスト
11. test_integration.py          # 基本統合テスト
```

### 7.3.2 Phase 2 実装詳細

**Week 4-5: 述語統合**

*Day 1-3: 既存述語改修*
```python
# builtins.py 改修順序:
1. GetCharPredicate.execute() 改修
   - read_char_from_current() → request_input("char", "get_char")
   
2. ReadLinePredicate.execute() 改修
   - read_line_from_current() → request_input("line", "read_line")
   
3. その他入力述語の順次改修
   - PeekCharPredicate
   - AtEndOfStreamPredicate
```

*Day 4-5: 新述語対応*
```python
# 新述語追加（例）:
4. ReadPasswordPredicate 実装
   - request_input("password", "read_password", mask_char="*")
   
5. ReadMultilinePredicate 実装
   - request_input("multiline", "read_multiline", delimiter="END")
```

**Week 6: エラーハンドリング強化**
```python
6. フォールバック機構の完全実装
7. 例外処理の詳細実装
8. リトライ・復旧機能実装
```

**Week 7: テスト完成**
```python
9. test_compatibility.py     # 互換性テスト完成
10. 全体テストスイート完成
11. カバレッジ目標達成（90%以上）
```

### 7.3.3 Phase 3 実装詳細

**Week 8-9: 高度機能実装**

*Day 1-3: ユーティリティハンドラ*
```python
# handlers/ ディレクトリ実装:
1. mock_handler.py          # MockInputHandler
2. debug_handler.py         # DebugInputHandler  
3. migration_helpers.py     # 移行支援ヘルパー
```

*Day 4-5: 監視・ログ機能*
```python
4. イベント履歴機能の完全実装
5. 統計情報取得機能
6. パフォーマンス監視機能
```

**Week 10: 最終調整**
```python
7. ドキュメント完成
8. 使用例・サンプルコード作成
9. パフォーマンステスト実施
10. 最終的な品質チェック
```

**実装マイルストーン:**

*Milestone 1 (Phase 1完了):*
- 基本的な統一入力システムが動作
- レガシーコードが無修正で動作
- 基本テストが通過

*Milestone 2 (Phase 2完了):*
- 全入力述語が統一システム対応
- エラーハンドリングが完全動作  
- 互換性テストが全て通過

*Milestone 3 (Phase 3完了):*
- 本番投入可能な品質
- 完全なドキュメント
- 充実したユーティリティ

**実装時の注意事項:**

1. **段階的統合**: 各フェーズで動作する状態を維持
2. **テスト駆動**: 実装前にテストケースを作成
3. **互換性維持**: 既存コードが常に動作することを確認
4. **パフォーマンス**: 各段階でパフォーマンス劣化がないことを確認
5. **ドキュメント**: 実装と並行してドキュメント更新

**リスク管理:**
- 各週末に進捗レビュー実施
- 問題発生時は一つ前の安定バージョンに戻る
- 重要な変更は別ブランチで実装し、テスト完了後にマージ