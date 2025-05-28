# テストデータとテスト実行環境

## 4. テストデータ

### 4.1 基本テストケース

- 単純なファクトとルール
- 算術・比較演算
- リスト操作
- 再帰処理

### 4.2 複雑なテストケース

- 既存の Prolog プログラム（冒険ゲーム、パズル）
- エラーケース
- エッジケース

### 4.3 パフォーマンステストケース

- 大量データ処理
- 深い再帰
- 複雑な単一化

## 5. テスト実行環境

### 5.1 必要なツール

- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジ測定
- **pytest-benchmark**: パフォーマンス測定
- **pytest-mock**: モッキング

### 5.2 設定ファイル

- `pytest.ini`: pytest 設定
- `conftest.py`: 共通フィクスチャ
- `.coveragerc`: カバレッジ設定

### 5.3 既存のテストデータファイル

プロジェクトには以下のテストデータファイルが利用可能です：

- `tests/data/myadven.prolog` - 冒険ゲームの Prolog プログラム
- `tests/data/puzzle1.prolog` - パズル解決の Prolog プログラム
- `tests/data/test.prolog` - 一般的なテストケース

これらのファイルはシステムテストで実際の Prolog プログラムの動作検証に使用します。

## 関連文書

- [システム概要とテスト戦略](./01_system_overview_and_strategy.md) - 全体戦略
- [テストスイート構成](./02_test_suite_structure.md) - テスト構成の詳細
- [テスト品質指標と継続的テスト](./04_quality_metrics_and_ci.md) - 品質管理
