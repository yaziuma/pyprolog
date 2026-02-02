# PyProlog 統一入力システム 設計書

## ドキュメント構成

### 概要設計
- [overview.md](overview.md) - システム概要とアーキテクチャ方針

### 詳細設計

#### システム設計
- [01_system_architecture.md](01_system_architecture.md) - システム全体設計
- [02_core_components.md](02_core_components.md) - コアコンポーネント詳細設計

#### 統合設計  
- [03_predicate_integration.md](03_predicate_integration.md) - 入力述語統合設計
- [04_api_specification.md](04_api_specification.md) - API設計仕様

#### 品質・実装
- [05_error_handling.md](05_error_handling.md) - エラーハンドリング設計
- [06_testing.md](06_testing.md) - テスト設計
- [07_implementation.md](07_implementation.md) - 実装仕様

## 設計書の読み方

### 実装者向け
1. **概要把握**: overview.md
2. **システム理解**: 01_system_architecture.md → 02_core_components.md  
3. **実装詳細**: 03_predicate_integration.md → 07_implementation.md
4. **品質保証**: 05_error_handling.md → 06_testing.md

### 利用者向け
1. **概要把握**: overview.md
2. **API理解**: 04_api_specification.md
3. **エラー対応**: 05_error_handling.md

### レビューア向け
1. **設計方針**: overview.md → 01_system_architecture.md
2. **技術詳細**: 02_core_components.md → 03_predicate_integration.md
3. **品質検証**: 05_error_handling.md → 06_testing.md