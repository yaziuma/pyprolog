# PyProlog制限分析レポート

## 概要

本ドキュメントは、PyPrologインタープリタの制限と問題点を詳細に分析し、特に日本語医療診断テストの失敗原因を特定することを目的とする。

## 調査結果サマリー

### ✅ 正常に動作する機能

1. **基本的なunification**: `X = hello` のような単純な代入
2. **事実の検索**: `disease_symptom(cold, fever, 0.8)` のような事実クエリ
3. **ルールの実行**: `test_rule(X) :- X = hello` のような単純なルール
4. **複合項の作成**: `Term(functor, args)` による構造化データ
5. **リスト操作**: `[a, b, c]` のようなリスト構造
6. **組み込み述語**: `write/1`, `nl/0`, `member/2`, `append/3` など
7. **算術演算**: `is/2`, `>/2`, `</2` などの数値演算
8. **複雑な compound term**: `[diagnosis(cold, 0.88)]` のような構造

### ❌ 問題のある機能パターン

#### 1. 特定の医療診断述語の実行失敗

**現象**: 
- `gadp_test/5` や `patient_diagnosis/5` が実行されるが、goalが成功しない
- デバッグメッセージは出力されるが、unificationで失敗

**詳細分析**:
```prolog
% 失敗例（医療診断KBから）
gadp_test(Arg1, Arg2, Arg3, Arg4, OutputResult) :-
    write('Debug: GADP_TEST CALLED with ground args'), nl,
    OutputResult = [diagnosis(cold, 0.88)].

% 成功例（テスト用）
medical_test(OutputResult) :- 
    write(debug), 
    OutputResult = [diagnosis(cold, 0.88)].
```

**判明した事実**:
- 同じパターンでも単独テストでは成功する
- 医療診断KBファイル内での実行時のみ失敗
- 基本的なunificationロジックには問題なし

## 技術的深堀り分析

### Unificationメカニズム

PyPrologのunificationは `logic_interpreter.py:80-178` で実装されており、以下の流れで動作：

1. **Dereferencing**: 変数の束縛を解決
2. **Type checking**: 項の型を判定
3. **Occurs check**: 循環参照を検出
4. **Binding**: 変数を値に束縛

```python
def unify(self, term1: PrologType, term2: PrologType, env: BindingEnvironment) -> Tuple[bool, BindingEnvironment]:
    current_env = env.copy()
    t1 = self.dereference(term1, current_env)
    t2 = self.dereference(term2, current_env)
    
    if t1 == t2:
        return True, current_env
        
    if isinstance(t1, Variable):
        if self._occurs_check(t1, t2, current_env):
            return False, env
        current_env.bind(t1.name, t2)
        return True, current_env
    # ... 他のケース
```

### Goal実行メカニズム

Goal実行は `logic_interpreter.py:234-269` で処理され：

1. **Goal normalization**: AtomをTermに変換
2. **Built-in handling**: 特別な述語（true, fail）の処理
3. **Rule matching**: データベースのルールとマッチング

### テスト結果との矛盾

**予期しない成功パターン**:
- 単独で実行すると成功: `medical_test(R) :- write(debug), R = [diagnosis(cold, 0.88)].`
- 医療KBファイル内では失敗: 同じロジック

**推測される問題**:
1. **名前空間の競合**: 複数の述語が同じ名前空間で競合
2. **パースエラーの隠蔽**: KBファイル内の一部でパースエラーが発生
3. **変数スコープの問題**: 複雑なKBでの変数管理
4. **メモリ管理**: 大きなKBファイルでのリソース枯渇

## 成功テストから見えるパターン

### 326個の成功テスト分析

成功しているテストの共通パターン：

1. **単一目的のテスト**: 1つの機能に集中
2. **小さなKB**: 少数のルール/事実のみ
3. **シンプルな構造**: 複雑な入れ子構造を避ける
4. **明確な型**: 曖昧さのない型定義

### 実際に動作する医療診断パターン

```python
# 成功例：基本的な医療情報クエリ
result = runtime.query("disease_symptom(cold, fever, 0.8).")  # ✅ 成功

# 成功例：シンプルな診断ロジック  
runtime.add_rule("simple_diagnose(X) :- disease_symptom(cold, fever, _), X = cold.")
result = runtime.query("simple_diagnose(Y).")  # ✅ 成功

# 失敗例：複雑な医療診断ロジック
result = runtime.query("patient_diagnosis([fever, cough], 30, [], [], Result).")  # ❌ 失敗
```

## 根本原因の仮説

### 1. KBファイルサイズ制限説

**仮説**: 75ルール/事実の大きなKBファイルでパフォーマンス問題
**証拠**: 
- 単独テストは成功
- 大きなKBでのみ失敗
**検証方法**: KBを段階的に縮小してテスト

### 2. パース時の隠れたエラー説

**仮説**: KBファイル内の特定の構文でパースエラーが発生
**証拠**: 
- ログに "Parse error at '(': Expected '.' after rule or fact" が出現
- パースは続行されるが、一部の述語が正しく登録されない
**検証方法**: パースエラー箇所の特定と修正

### 3. 変数スコープ競合説

**仮説**: 複数述語間での変数名競合
**証拠**: 
- 同じ変数名（Result, OutputResult）の多用
- 複雑なネストした構造
**検証方法**: 変数名の一意化

## 実装されている高度な機能

PyPrologは実際には多くの高度な機能を実装している：

### Built-in述語群

1. **型テスト**: `var/1`, `atom/1`, `number/1`
2. **項操作**: `functor/3`, `arg/3`, `=../2` (univ)
3. **動的述語**: `asserta/1`, `assertz/1`, `retract/1`
4. **リスト操作**: `member/2`, `append/3`
5. **メタ述語**: `findall/3`
6. **I/O述語**: `get_char/1`, `write/1`, `nl/0`

### 演算子システム

- 70個の演算子を定義
- 優先順位とassociativityをサポート
- 算術、比較、論理演算子

### 日本語サポート

- 日本語変数名のマッピング機能
- VariableMapperによる文字変換
- Unicode対応のスキャナー

## 推奨される修正アプローチ

### 1. 段階的デバッグ

```bash
# Step 1: KBサイズの問題を検証
# 医療KBを半分に分割してテスト

# Step 2: パースエラーの修正
# ログのパースエラーを特定して修正

# Step 3: 変数名の一意化
# 述語間での変数名競合を解消
```

### 2. 詳細ログの有効化

```python
# デバッグレベルでのログ出力を有効化
import logging
logging.getLogger('pyprolog').setLevel(logging.DEBUG)
```

### 3. 最小再現例の作成

医療診断KBから問題のある述語のみを抽出して最小再現例を作成。

## 結論

PyPrologは基本的に健全で機能的なPrologインタープリタである。問題は以下に集約される：

1. **規模の問題**: 大きなKBファイルでの処理制限
2. **パース品質**: 一部の構文でのパースエラー処理
3. **エラー報告**: 失敗時の詳細な診断情報不足

これらは修正可能な実装上の問題であり、Prologの基本アルゴリズムやunificationメカニズムには根本的な欠陥はない。

## 次のステップ

1. パースエラーの特定と修正
2. 大きなKBファイルでのメモリ/パフォーマンス最適化
3. より詳細なエラー診断機能の追加
4. 医療診断KBの段階的なデバッグ

---

**作成日**: 2025-06-21  
**分析者**: Claude Code  
**対象バージョン**: PyProlog v0.2.1