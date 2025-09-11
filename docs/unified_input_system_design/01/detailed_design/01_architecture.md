# システムアーキテクチャ詳細設計

## 1. 全体アーキテクチャ

> **用語**: 詳細な定義は[用語集](../glossary.md)を参照

### 1.1 システム構成図

```
┌─────────────────────────────────────────────────────────┐
│                  Prolog実行層                           │
├─────────────────────────────────────────────────────────┤
│  detailed_interaction述語                               │
│       ↓                                                 │
│  ReadLinePredicate.execute()                           │
│       ↓                                                 │
│  IOPredicate._request_input()                          │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                入出力管理層                              │
├─────────────────────────────────────────────────────────┤
│  IOManager                                              │
│       ├─ 統一入力システム（Unified Input System）     │
│       │      ├─ InputEvent                              │
│       │      ├─ InputHandler interface                  │
│       │      └─ ThreadingController                     │
│       └─ 従来IOStream（後方互換性用）                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│               スレッド実行層                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │ Prolog実行      │    │ 入力処理        │            │
│  │ スレッド        │◄──►│ スレッド        │            │
│  │                 │    │                 │            │
│  │ - 継続実行      │    │ - 入力待ち      │            │
│  │ - スタック保持  │    │ - Handler呼出   │            │
│  └─────────────────┘    └─────────────────┘            │
│           │                        │                    │
│           └────────┬───────────────┘                    │
│                    ▼                                    │
│  ┌─────────────────────────────────────┐               │
│  │     共有実行状態（Execution State）・同期制御      │
│  │ - threading.Event同期               │               │
│  │ - InputRequest/Response交換         │               │
│  │ - 実行状態（Execution State）管理  │               │
│  └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 1.2 制御フロー

**通常実行時:**
```python
Runtime.query("detailed_interaction.") 
  → PrologInterpreter実行
  → ReadLinePredicate.execute()
  → IOPredicate._request_input()
  → IOManager.request_input()
  → UnifiedInputSystem.request_input()
  → InputHandler.handle_input_request()
  → 入力値取得・return
```

**真の継続実行時:**
```python
Runtime.query("detailed_interaction.")
  → 新規Prologスレッド作成・開始
  → ReadLinePredicate.execute()
  → IOManager.request_input() 
    → 入力処理スレッドに要求送信
    → Event.wait() でブロッキング (スタックフレーム保持)
  → 入力処理スレッド
    → InputHandler.handle_input_request()
    → 入力取得完了
    → Event.set() でPrologスレッド再開
  → Prologスレッド継続実行
```

## 2. コンポーネント詳細

### 2.1 IOPredicate基底クラス

**責任:**
- 入出力述語の共通処理統合
- 統一入力システムへの統一インターフェース
- 引数検証・エラーハンドリング統一

**主要メソッド:**
```python
class IOPredicate(BuiltinPredicate):
    def execute(runtime, env) -> Iterator[BindingEnvironment]:
        """共通実行フロー - テンプレートメソッドパターン"""
        
    def _request_input(runtime) -> str:
        """統一入力要求 - 継続実行の核心"""
        
    def _convert_to_prolog_term(input_value) -> PrologType:
        """入力値→Prologターム変換 - サブクラス実装"""
```

### 2.2 UnifiedInputSystem

**責任:**
- 入力要求の中央制御
- InputHandlerへのルーティング
- スレッド間通信制御

**状態管理:**
```python
class UnifiedInputSystem:
    input_handler: Optional[InputHandler]
    threading_controller: ThreadingController
    fallback_stream: Optional[IOStream]
```

### 2.3 ThreadingController

**責任:**
- スレッド間同期制御
- 入力要求・応答の管理
- 継続実行制御

**同期プリミティブ:**
```python
class ThreadingController:
    input_event: threading.Event      # 入力要求通知
    response_event: threading.Event   # 応答通知
    input_request: InputRequest       # 要求データ
    input_response: InputResponse     # 応答データ
    state_lock: threading.Lock        # 状態保護
```

## 3. 実行モデル

### 3.1 シングルスレッドモード（従来互換）

```python
# 従来の同期実行
input_value = runtime.io_manager.request_input("line", "read_line")
# ↓ InputHandlerが直接実行
return input_handler.handle_input_request(event)
```

### 3.2 マルチスレッドモード（真の継続実行）

```python
# スレッド間通信実行
def request_input(self, input_type, predicate_name):
    # 入力処理スレッドに要求
    self.threading_controller.request_input(input_type, predicate_name)
    
    # 【重要】ここでPrologスレッドブロッキング
    # スタックフレーム・ローカル変数完全保持
    response = self.threading_controller.wait_for_response()
    
    # 入力取得後、自然に実行継続
    return response.value
```

### 3.3 モード切替制御

```python
class Runtime:
    def __init__(self):
        self.threading_enabled = False  # デフォルト: シングルスレッド
    
    def enable_threading(self):
        """真の継続実行モード有効化"""
        self.threading_enabled = True
        self.io_manager.unified_input.enable_threading()
```

## 4. エラーハンドリング

### 4.1 例外階層

```python
class UnifiedInputError(PrologError):
    """統一入力システムエラー基底クラス"""

class InputHandlerError(UnifiedInputError):
    """InputHandler実行エラー"""

class ThreadingSyncError(UnifiedInputError):
    """スレッド同期エラー"""

class InputTimeoutError(UnifiedInputError):
    """入力タイムアウトエラー"""
```

### 4.2 エラー回復戦略

**InputHandlerエラー:**
```python
try:
    return self.input_handler.handle_input_request(event)
except Exception as e:
    # フォールバック: 標準入力
    return self.fallback_stream.read_line()
```

**スレッド同期エラー:**
```python
try:
    response = self.wait_for_response(timeout=30.0)
except threading.TimeoutError:
    # タイムアウト時はEOF扱い
    return None
```

## 5. パフォーマンス考慮

### 5.1 最適化ポイント

**スレッド作成コスト:**
- 入力処理スレッドは1回だけ作成（デーモンスレッド）
- Prologスレッドは必要時のみ作成

**同期コスト:**
- Event.wait()/set()の最小限使用
- 状態ロックの範囲最小化

**メモリ使用量:**
- 中断中のスタックフレーム保持が必要
- InputRequest/Responseオブジェクトは最小限

### 5.2 性能目標

- **スレッド切替オーバーヘッド**: < 1ms
- **入力応答時間**: InputHandlerに依存（制御外）
- **メモリ使用量増加**: < 10MB per suspended query

## 6. セキュリティ考慮

### 6.1 スレッド安全性

- 共有状態への排他制御（threading.Lock使用）
- InputHandler呼び出し時の例外分離
- デーモンスレッドによるプロセス終了保証

### 6.2 リソース管理

- スレッドリークの防止
- 中断クエリのタイムアウト制御
- メモリリークの防止

この設計により、既存コードとの完全互換を保ちつつ、真の継続実行が実現可能になります。