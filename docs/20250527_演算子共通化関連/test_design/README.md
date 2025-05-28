# Prolog インタープリター テスト設計書

本ディレクトリには、Prolog インタープリターのテスト設計に関する文書が含まれています。

## 文書構成

### 1. [システム概要とテスト戦略](./01_system_overview_and_strategy.md)

- システムの主要コンポーネント
- テストレベルとテスト観点の定義

### 2. [テストスイート構成](./02_test_suite_structure.md)

- Core Types テスト
- Parser & Scanner テスト
- Operator Registry テスト
- Runtime テスト
- 統合テスト
- システムテスト
- パフォーマンステスト

### 3. [テストデータとテスト実行環境](./03_test_data_and_environment.md)

- テストデータの分類
- 必要なツールと設定ファイル

### 4. [テスト品質指標と継続的テスト](./04_quality_metrics_and_ci.md)

- カバレッジ目標
- 実行時間目標
- 自動化とレポーティング

### 5. [テスト実装の優先順位](./05_implementation_priority.md)

- Phase 別の実装計画
- 段階的なテスト構築戦略

## 使用方法

各文書は独立して読むことができますが、[システム概要とテスト戦略](./01_system_overview_and_strategy.md)から開始することを推奨します。

## 更新履歴

- 2025/05/28: 元の大きなファイルから分割
