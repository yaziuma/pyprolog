# 用語集（Glossary）

## 概要

統一入力システム設計における重要用語の定義と相互関係を明確化します。
Geminiレビューで指摘された用語統一の改善として作成。

## 核心概念

### 継続（Continuation）
**定義**: プログラムの実行状態（スタックフレーム、変数、実行位置等）を保持し、後でその状態から実行を再開する機能

**pyprologでの実現**:
- Pythonスレッドのスタックフレーム保持機能を活用
- `Event.wait()`によるブロッキングで実行状態を完全保持
- 入力取得後、正確に同じ地点から実行再開

**対比**:
```
真の継続    : スタックフレーム完全保持 → 同一地点から再開
擬似継続    : 状態を明示的に保存・復元 → 近似的な再開
```

### 実行状態（Execution State）
**定義**: ある時点でのPrologクエリ実行の完全な状態情報

**含まれる情報**:
- **スタックフレーム**: 関数呼び出し階層
- **ローカル変数**: 各関数内の変数値
- **束縛環境**: Prolog変数の統一化状態
- **実行位置**: 次に実行される命令のアドレス

### 統一入力システム（Unified Input System）
**定義**: 全ての入力処理を中央制御する統合アーキテクチャ

**構成要素**:
- **UnifiedInputSystem**: 中央制御コンポーネント
- **InputHandler**: 実際の入力処理インターフェース
- **ThreadingController**: スレッド間同期制御
- **IOPredicate**: 入出力述語の基底クラス

## アーキテクチャ用語

### IOPredicate基底クラス
**定義**: 全ての入出力述語の共通基底クラス

**提供機能**:
- 引数検証の統一
- 統一入力システムへの統一インターフェース
- EOF処理・数値変換等の共通ユーティリティ
- テンプレートメソッドパターンの実装

**統合効果**:
```
統合前: 各述語で重複実装 (200+ lines)
統合後: 基底クラス + 各述語の特化部分 (190 lines total)
```

### InputHandler
**定義**: 実際の入力処理を担当する抽象インターフェース

**責務範囲**:
- 入力要求の受信・処理
- 入力値の取得・返却
- エラー状況の適切な例外発生

**実装バリエーション**:
- **StandardInputHandler**: 標準入力処理
- **GUIInputHandler**: GUI統合
- **MCPInputHandler**: Model Context Protocol統合

## スレッド関連用語

### スレッド間通信（Inter-thread Communication）
**定義**: Prologスレッドと入力処理スレッド間の協調メカニズム

**使用プリミティブ**:
- `threading.Event`: 通知・待機制御
- `threading.Lock`: 共有データ保護
- **共有オブジェクト**: InputRequest/InputResponse

**通信フロー**:
```
Prologスレッド → [Event.set()] → 入力スレッド
               ← [Event.set()] ←
```

### デーモンスレッド（Daemon Thread）
**定義**: メインプロセス終了時に自動終了するバックグラウンドスレッド

**採用理由**:
- プロセス終了時の確実なクリーンアップ
- 明示的終了処理の簡素化
- システム応答性の向上

## エラーハンドリング用語

### タイムアウト制御（Timeout Control）
**定義**: 入力待ちの無限継続を防ぐ時間制限メカニズム

**設定値**: デフォルト300秒（5分）
**タイムアウト時動作**: EOF扱いでProlog実行継続

### エラー伝播（Error Propagation）
**定義**: InputHandlerのPython例外をProlog例外に変換する仕組み

**変換マッピング**:
```
FileNotFound → existence_error(file, filename)
Permission   → permission_error(read, file, filename)
Timeout      → resource_error(timeout)
```

## 互換性用語

### 後方互換性（Backward Compatibility）
**定義**: 既存コードが無修正で動作することを保証する設計原則

**保証範囲**:
- 既存IOPredicate（GetChar/ReadLine等）の外部API
- IOManagerの従来メソッド
- 既存Prologクエリの実行結果

### フォールバック機能（Fallback Mechanism）
**定義**: 統一入力システム障害時の代替処理メカニズム

**階層化されたフォールバック**:
```
1st: UnifiedInputSystem （推奨）
2nd: 従来IOStreamAPI    （互換性）
3rd: 標準input()関数    （最終手段）
```

## パフォーマンス用語

### GIL制約（Global Interpreter Lock Constraint）
**定義**: PythonのGILによるスレッド実行制限の影響

**影響評価**:
- **CPU集約処理**: 効果限定
- **I/Oバウンド処理**: 問題なし（対話的入力は該当）
- **実用影響**: 本システムでは無視可能

### スタックフレーム保持コスト
**定義**: 実行中断時のメモリ使用量増加

**コスト要因**:
- 中断中のスタックフレーム保持
- ローカル変数の維持
- 束縛環境の保存

**許容範囲**: 対話的入力では実用上問題なし

この用語集により、設計ドキュメント全体の用語が統一され、理解しやすい文書になります。