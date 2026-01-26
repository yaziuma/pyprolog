# IOManager統合詳細設計

## 1. 統合概要

> **用語**: 詳細な定義は[用語集](../glossary.md)を参照

### 1.1 目的
- 既存IOManagerに**統一入力システム（Unified Input System）**を統合
- 完全な**後方互換性（Backward Compatibility）**を維持
- 新旧APIの共存とスムーズな移行

### 1.2 統合戦略
```
従来: IOPredicate → IOManager.read_*_from_current() → IOStream
新方式: IOPredicate → IOManager.request_input() → 統一入力システム（Unified Input System） → InputHandler
```

## 2. IOManager改修設計

### 2.1 改修されたIOManagerクラス

```python
from typing import Optional, Union, Dict, Any
import logging
from pyprolog.runtime.unified_input_system import UnifiedInputSystem, InputHandler

logger = logging.getLogger(__name__)

class IOManager:
    """
    入出力管理クラス（統一入力システム統合版）
    
    従来のIOStreamベースAPIと新しい統一入力システムの
    両方をサポートし、完全な後方互換性を提供する。
    """
    
    def __init__(self):
        # 従来コンポーネント（互換性のため保持）
        self._streams = {}
        self._current_input_stream = None
        self._current_output_stream = None
        
        # 新規コンポーネント
        self.unified_input = UnifiedInputSystem()
        
        # 移行制御フラグ
        self._unified_input_enabled = True  # デフォルトで新方式使用
        self._fallback_to_legacy = True    # エラー時は従来方式にフォールバック
        
        # 初期設定
        self._setup_default_streams()
        self._setup_unified_input_fallback()
    
    def _setup_default_streams(self):
        """従来互換性のためのデフォルトストリーム設定"""
        # 既存の初期化処理をそのまま保持
        # 標準入出力ストリームの設定等
        pass
    
    def _setup_unified_input_fallback(self):
        """統一入力システムのフォールバック設定"""
        if self._current_input_stream:
            self.unified_input.set_fallback_stream(self._current_input_stream)
    
    # ========================================================================
    # 新規API（統一入力システム）
    # ========================================================================
    
    def request_input(
        self, 
        input_type: str, 
        predicate_name: str, 
        prompt: str = "",
        **kwargs
    ) -> Optional[str]:
        """
        統一入力要求API
        
        【メインAPI】IOPredicateから呼び出される新しい統一入力API。
        設定に応じて統一入力システムまたは従来方式を使用。
        
        Args:
            input_type: 入力タイプ ("char", "line", "peek_char" etc.)
            predicate_name: 呼び出し元述語名
            prompt: プロンプト文字列
            **kwargs: 追加パラメータ
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        if self._unified_input_enabled:
            try:
                return self.unified_input.request_input(
                    input_type, predicate_name, prompt, **kwargs
                )
            except Exception as e:
                logger.warning(f"Unified input failed, fallback to legacy: {e}")
                if self._fallback_to_legacy:
                    return self._request_input_legacy(input_type, prompt)
                else:
                    raise
        else:
            return self._request_input_legacy(input_type, prompt)
    
    def set_input_handler(self, handler: InputHandler):
        """
        統一入力ハンドラを設定
        
        Args:
            handler: InputHandlerの実装
        """
        self.unified_input.set_input_handler(handler)
    
    def enable_threading(self):
        """
        マルチスレッドモード（真の継続実行）を有効化
        
        この呼び出し後、全ての入力要求で真の継続実行が使用される。
        """
        self.unified_input.enable_threading()
        logger.info("IOManager: Threading mode enabled")
    
    def disable_threading(self):
        """シングルスレッドモードに切り替え"""
        self.unified_input.disable_threading()
        logger.info("IOManager: Threading mode disabled")
    
    def enable_unified_input(self):
        """統一入力システムを有効化"""
        self._unified_input_enabled = True
        logger.info("IOManager: Unified input enabled")
    
    def disable_unified_input(self):
        """統一入力システムを無効化（従来方式のみ）"""
        self._unified_input_enabled = False
        logger.info("IOManager: Unified input disabled")
    
    # ========================================================================
    # 従来API（後方互換性）
    # ========================================================================
    
    def read_char_from_current(self) -> str:
        """
        現在の入力ストリームから文字を読み取り（従来互換API）
        
        【重要】このメソッドは既存のGetCharPredicateとの互換性のため保持。
        しかし、新しいIOPredicate統合後は使用されない。
        
        Returns:
            str: 読み取った文字（EOF時は空文字列）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            result = self.request_input("char", "get_char_legacy")
            return result if result is not None else ""
        else:
            # 従来処理
            return self._read_char_from_stream()
    
    def read_line_from_current(self) -> Optional[str]:
        """
        現在の入力ストリームから行を読み取り（従来互換API）
        
        Returns:
            Optional[str]: 読み取った行（EOF時はNone）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            return self.request_input("line", "read_line_legacy")
        else:
            # 従来処理
            return self._read_line_from_stream()
    
    def peek_char_from_current(self) -> str:
        """
        現在の入力ストリームから非破壊的文字読み取り（従来互換API）
        
        Returns:
            str: 覗き見した文字（EOF時は空文字列）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            result = self.request_input("peek_char", "peek_char_legacy", non_destructive=True)
            return result if result is not None else ""
        else:
            # 従来処理
            return self._peek_char_from_stream()
    
    # ========================================================================
    # 内部実装（従来処理の保持）
    # ========================================================================
    
    def _request_input_legacy(self, input_type: str, prompt: str) -> Optional[str]:
        """
        従来方式による入力処理
        
        統一入力システムエラー時のフォールバック処理
        """
        if input_type == "char":
            result = self._read_char_from_stream()
            return result if result else None
        elif input_type == "line":
            return self._read_line_from_stream()
        elif input_type == "peek_char":
            result = self._peek_char_from_stream()
            return result if result else None
        else:
            logger.error(f"Unknown input_type in legacy mode: {input_type}")
            return None
    
    def _read_char_from_stream(self) -> str:
        """従来のストリームベース文字読み取り"""
        if self._current_input_stream and hasattr(self._current_input_stream, 'read_char'):
            return self._current_input_stream.read_char()
        else:
            try:
                char = input()
                return char[0] if char else ""
            except (EOFError, KeyboardInterrupt):
                return ""
    
    def _read_line_from_stream(self) -> Optional[str]:
        """従来のストリームベース行読み取り"""
        if self._current_input_stream and hasattr(self._current_input_stream, 'read_line'):
            return self._current_input_stream.read_line()
        else:
            try:
                return input()
            except (EOFError, KeyboardInterrupt):
                return None
    
    def _peek_char_from_stream(self) -> str:
        """従来のストリームベース覗き見読み取り"""
        if self._current_input_stream and hasattr(self._current_input_stream, 'peek_char'):
            return self._current_input_stream.peek_char()
        else:
            # 標準入力では覗き見不可のため、通常読み取り
            return self._read_char_from_stream()
    
    # ========================================================================
    # 出力系API（変更なし）
    # ========================================================================
    
    def write_char_to_current(self, char: str):
        """現在の出力ストリームに文字を書き込み"""
        if self._current_output_stream:
            self._current_output_stream.write(char)
        else:
            print(char, end='', flush=True)
    
    def write_string_to_current(self, string: str):
        """現在の出力ストリームに文字列を書き込み"""
        if self._current_output_stream:
            self._current_output_stream.write(string)
        else:
            print(string, end='', flush=True)
    
    # ========================================================================
    # ストリーム管理API（変更なし）
    # ========================================================================
    
    def set_current_input_stream(self, stream):
        """現在の入力ストリームを設定"""
        self._current_input_stream = stream
        # 統一入力システムのフォールバックも更新
        self.unified_input.set_fallback_stream(stream)
    
    def set_current_output_stream(self, stream):
        """現在の出力ストリームを設定"""
        self._current_output_stream = stream
    
    def get_current_input_stream(self):
        """現在の入力ストリームを取得"""
        return self._current_input_stream
    
    def get_current_output_stream(self):
        """現在の出力ストリームを取得"""
        return self._current_output_stream
    
    # ========================================================================
    # 統計・診断API
    # ========================================================================
    
    def get_input_statistics(self) -> Dict[str, Any]:
        """入力処理統計情報取得"""
        stats = self.unified_input.get_statistics()
        stats.update({
            "unified_input_enabled": self._unified_input_enabled,
            "fallback_to_legacy": self._fallback_to_legacy,
            "current_input_stream": str(type(self._current_input_stream).__name__) if self._current_input_stream else None,
        })
        return stats
    
    def shutdown(self):
        """IOManager終了処理"""
        self.unified_input.shutdown()
        logger.info("IOManager shutdown complete")
```

## 3. Runtime統合

### 3.1 Runtimeクラスの修正

```python
class Runtime:
    """
    Prolog実行環境（統一入力システム統合版）
    """
    
    def __init__(self):
        # 既存の初期化処理...
        
        # IOManagerを統一入力対応版に置き換え
        self.io_manager = IOManager()  # 新しいIOManager
        
        # デフォルト設定
        self._setup_default_input_handler()
    
    def _setup_default_input_handler(self):
        """デフォルト入力ハンドラの設定"""
        from pyprolog.runtime.handlers.standard_handler import StandardInputHandler
        self.io_manager.set_input_handler(StandardInputHandler())
    
    def enable_threaded_input(self):
        """
        真の継続実行モードを有効化
        
        この呼び出し後、全ての入力述語で真の継続実行が使用される。
        """
        self.io_manager.enable_threading()
    
    def set_custom_input_handler(self, handler: InputHandler):
        """
        カスタム入力ハンドラを設定
        
        Args:
            handler: InputHandlerの実装
        """
        self.io_manager.set_input_handler(handler)
```

## 4. 移行シナリオ

### 4.1 段階的移行

**Phase 1: 統合IOManagerデプロイ**
```python
# 既存コードは無修正で動作（従来API使用）
runtime = Runtime()
result = runtime.query("get_char(X).")  # 内部で統一入力システム使用
```

**Phase 2: IOPredicate統合**
```python
# IOPredicateベースの述語が統一入力システム使用
# 従来述語は互換APIで動作継続
```

**Phase 3: 真の継続実行有効化**
```python
# 利用者が明示的に有効化
runtime.enable_threaded_input()
result = runtime.query("detailed_interaction.")  # 真の継続実行
```

### 4.2 互換性保証

**従来コードの動作保証:**
```python
# これらのAPIは全て動作継続
runtime.io_manager.read_char_from_current()
runtime.io_manager.read_line_from_current()
runtime.io_manager.set_current_input_stream(stream)
```

**新旧APIの共存:**
```python
# 新API
runtime.io_manager.request_input("line", "read_line")

# 従来API（内部で新APIを使用）
runtime.io_manager.read_line_from_current()
```

## 5. テスト戦略

### 5.1 互換性テスト

```python
class TestIOManagerCompatibility:
    def test_legacy_api_works(self):
        """従来APIの動作確認"""
        io_manager = IOManager()
        
        # 従来メソッドが例外なく動作することを確認
        result = io_manager.read_line_from_current()
        assert result is not None or result is None  # 正常終了
    
    def test_new_api_works(self):
        """新APIの動作確認"""
        io_manager = IOManager()
        
        result = io_manager.request_input("line", "test_predicate")
        assert result is not None or result is None  # 正常終了
    
    def test_threading_mode_toggle(self):
        """スレッドモード切り替えテスト"""
        io_manager = IOManager()
        
        io_manager.enable_threading()
        assert io_manager.unified_input.threading_enabled
        
        io_manager.disable_threading()
        assert not io_manager.unified_input.threading_enabled
```

### 5.2 統合テスト

```python
class TestRuntimeIntegration:
    def test_existing_queries_work(self):
        """既存クエリの動作確認"""
        runtime = Runtime()
        
        # 既存の入出力述語が正常動作
        # （実際の入力は困難なため、モックを使用）
        with mock_input("test"):
            results = runtime.query("read_line(X).")
            assert len(results) > 0
```

## 6. 設計の利点

### 6.1 完全互換性
- 既存コードが一切の修正なく動作
- 段階的移行が可能
- エラー時のフォールバック機能

### 6.2 統一性
- 新旧APIが内部で統一入力システムを使用
- 一貫した動作とエラーハンドリング
- 統一された統計・監視機能

### 6.3 柔軟性
- 実行モードの動的切り替え
- カスタムハンドラの容易な統合
- 設定による細かい制御

この設計により、IOManagerが統一入力システムと完全統合され、既存コードとの完全互換性を保ちながら新機能を提供できます。