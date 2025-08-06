# PyProlog 非ブロッキング入力述語 ドキュメント

## 概要

このディレクトリには、PyPrologライブラリに`peek_char/1`および`at_end_of_stream/0`述語を追加する機能に関する詳細なドキュメントが含まれています。

## 課題の背景

現在のPyPrologライブラリでは、`get_char/1`述語が入力があるまで無限に待機（ブロッキング）するため、対話的アプリケーションや外部ライブラリとして使用する際に制御フローが奪われる問題があります。

## 解決策

非破壊的入力検査機能（`peek_char/1`、`at_end_of_stream/0`）を実装し、入力の事前確認により条件付き処理を実現します。

## ドキュメント構成

### 1. [概要設計書](../peek_char_at_end_of_stream_design.md)
- 全体的な設計方針と解決アプローチ
- ライブラリ利用者の観点での使用方法
- 段階的実装計画

### 2. [詳細設計書](detailed_design.md)
- アーキテクチャとクラス設計
- 技術的実装詳細
- エラーハンドリング設計
- パフォーマンス考慮事項
- 実装ガイドライン

### 3. [テスト設計書](test_design.md)
- 包括的テスト戦略
- 単体・統合・パフォーマンステスト
- エラーケーステスト
- 互換性テスト設計

### 4. [APIリファレンス](api_reference.md)
- 述語の詳細仕様
- クラスとメソッドのリファレンス
- 使用例とサンプルコード
- トラブルシューティングガイド

## 主要機能

### peek_char/1 述語
- 次の文字を**非破壊的**に先読み
- ストリーム位置を変更しない
- 条件付き入力処理を可能にする

### at_end_of_stream/0 述語  
- EOF状態を**非破壊的**に確認
- ブロッキングしない即座の判定
- 入力の有無を事前に確認可能

## 利用場面

1. **対話的アプリケーション開発**
   - 入力待ちでUIが凍結しない制御
   - レスポンシブなユーザーインターフェース

2. **パーサー・トークナイザー実装**
   - 先読みによる構文解析
   - 条件付きトークン読み取り

3. **ライブラリとしての利用**
   - 予期しない入力待ちの回避
   - 制御可能な入力フロー

## 実装状況

現在は**設計段階**です。以下の順序で実装を予定しています：

### Phase 1: 基盤実装
- [ ] StreamStatus, StreamError例外クラス
- [ ] IOStreamインターフェース拡張  
- [ ] StringStreamの機能拡張
- [ ] 基本テストスイート

### Phase 2: コア機能
- [ ] PeekCharPredicate実装
- [ ] AtEndOfStreamPredicate実装
- [ ] IOManagerの統合
- [ ] エラーハンドリング

### Phase 3: 高度な機能
- [ ] BufferedConsoleStream実装
- [ ] StreamBuffer実装
- [ ] パフォーマンス最適化
- [ ] 包括的テスト

### Phase 4: 拡張機能
- [ ] 設定ベース機能切り替え
- [ ] パフォーマンス監視
- [ ] 移行ヘルパー
- [ ] ドキュメント整備

## 期待される効果

### 開発者体験向上
- ✅ 予測可能な動作（入力待ちによる停止回避）
- ✅ 柔軟な制御（条件付き入力処理）
- ✅ デバッグ効率（非破壊的状態確認）

### アプリケーション品質向上  
- ✅ レスポンシブネス（UIが凍結しない）
- ✅ エラー耐性（入力エラー状況の適切なハンドリング）
- ✅ ユーザビリティ（より良いインタラクション設計）

### ライブラリエコシステム拡張
- ✅ 標準互換（ISO Prolog仕様への準拠）
- ✅ 拡張性（新しいストリームタイプの容易な追加）
- ✅ 保守性（明確なインターフェースによる保守効率）

## クイックスタート（実装後）

```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import Variable

# 基本的な使用例
runtime = Runtime()
stream = StringStream("hello")
runtime.io_manager.set_input_stream(stream)

# 先読みチェック
peek_result = runtime.query("peek_char(X)")
print(f"Next char: {peek_result[0][Variable('X')]}")  # 'h'

# EOF確認
if not runtime.query("at_end_of_stream"):
    # 入力があることを確認してから読み取り
    char = runtime.query("get_char(Y)")
```

```prolog
% 条件付き読み取りの例
read_if_digit(Char) :-
    peek_char(Next),
    Next >= '0',
    Next =< '9',
    get_char(Char).
```

## 貢献・フィードバック

この設計に対するフィードバックや改善提案は歓迎します：

1. 設計の妥当性について
2. 実装の優先順位について  
3. APIの使いやすさについて
4. パフォーマンス要件について
5. テストカバレッジについて

## 関連ドキュメント

- [PyProlog メイン README](../../README.md)
- [PyProlog 実装済み機能リスト](../pyprolog_implemented_features_and_predicates.md)
- [PyProlog 制限事項分析](../pyprolog_limitations_analysis.md)

---

**最終更新**: 2025年8月6日  
**設計者**: Claude Code