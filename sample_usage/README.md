# PyProlog使用サンプル集

このディレクトリには、PyPrologの実用的な使用例が含まれています。

## サンプル構成

### 1. [基本的な使用例](basic_usage.py)
- ランタイムの初期化
- 基本的なクエリ実行
- 変数束縛の確認

### 2. [ファイル読み込みサンプル](file_loading_sample.py)
- Prologファイルの読み込み
- 複数ファイルの統合
- エラーハンドリング

### 3. [動的ルール追加サンプル](dynamic_rules_sample.py)
- 実行時のルール追加
- データベースの動的更新
- 複雑なルール構築

### 4. [計算処理サンプル](arithmetic_sample.py)
- 算術演算（加算、減算、乗算、除算、べき乗）
- 比較演算（等価、大小比較）
- 複雑な数式の評価
- 再帰的な数値計算

### 5. [I/O機能サンプル](io_sample.py)
- 入出力ストリーム管理
- ファイルとの連携
- 対話的処理

### 6. [統合デモ](integrated_demo.py)
- 全機能を組み合わせた実用例
- テキストファイル読み込み
- Pythonからの動的追加
- 計算処理の組み込み
- I/Oを使った対話処理

## 実行方法

```bash
# 各サンプルを個別に実行
python sample_usage/basic_usage.py
python sample_usage/file_loading_sample.py
python sample_usage/dynamic_rules_sample.py
python sample_usage/arithmetic_sample.py
python sample_usage/io_sample.py

# 統合デモの実行
python sample_usage/integrated_demo.py
```

## サンプルファイル一覧

### Prologファイル
- `family.pl` - 家族関係のサンプルデータ
- `rules.pl` - 基本的なルール集
- `math_rules.pl` - 数学計算ルール
- `knowledge_base.pl` - 知識ベースサンプル

### データファイル
- `input_data.txt` - 入力データサンプル
- `queries.txt` - クエリ集
- `math_problems.txt` - 数学問題サンプル

### Pythonサンプル
- `basic_usage.py` - 基本使用例
- `file_loading_sample.py` - ファイル読み込み
- `dynamic_rules_sample.py` - 動的ルール追加
- `arithmetic_sample.py` - 計算処理サンプル
- `io_sample.py` - I/O機能
- `integrated_demo.py` - 統合デモ

## 学習の流れ

1. **基本機能の理解** - `basic_usage.py`で基本的な使い方を学ぶ
2. **ファイル操作** - `file_loading_sample.py`でファイル読み込みを学ぶ
3. **動的操作** - `dynamic_rules_sample.py`で実行時のルール追加を学ぶ
4. **計算機能** - `arithmetic_sample.py`で数値計算を学ぶ
5. **I/O機能** - `io_sample.py`で入出力処理を学ぶ
6. **統合活用** - `integrated_demo.py`で全機能を組み合わせて使う

各サンプルは独立して実行可能で、段階的に機能を学習できるよう設計されています。