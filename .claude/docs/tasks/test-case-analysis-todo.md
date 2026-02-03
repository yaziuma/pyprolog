# 今後の課題: テストケース分析

**日付**: 2026-02-03
**優先度**: 中
**ステータス**: TODO

## 課題

631個のテストケースの内容を分析し、以下の形式で出力する：

```
ケース: [テスト名]
チェックしている内容: [何をテストしているか]
結果: [PASS/FAIL]
```

## 失敗した方法

❌ **Gemini CLI による分析**:
- コストと時間を浪費
- 指定形式に従わない出力
- テストの実行を繰り返すだけで本質的な分析なし

## 正しいアプローチ

✅ **テストコードを直接読む**:

1. **各テストファイルを読む**:
   ```bash
   find tests -name "test_*.py" -type f
   ```

2. **テスト関数の docstring/コードを解析**:
   - pytest の test 関数名から意図を推測
   - docstring があれば内容を抽出
   - assert 文から何を検証しているか特定

3. **カテゴリごとに整理**:
   - runtime: インタープリタコア
   - core: データ型
   - integration: E2E
   - tools: 開発ツール
   - parser: 構文解析
   - etc.

4. **重複/冗長性を特定**:
   - 同じ内容をテストしているケースを検出
   - 統合可能なテストを提案

## 実装方針

### Step 1: テストコード読み込み
```python
import ast
import inspect

def extract_test_info(test_file):
    """Extract test function names and their purposes."""
    with open(test_file) as f:
        tree = ast.parse(f.read())

    tests = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                # Extract docstring
                docstring = ast.get_docstring(node)
                # Infer purpose from name
                purpose = infer_purpose(node.name)
                tests.append({
                    'name': node.name,
                    'purpose': docstring or purpose
                })
    return tests
```

### Step 2: 実行結果との結合
```python
def run_tests_and_capture():
    """Run pytest and capture individual test results."""
    result = subprocess.run(
        ['pytest', 'tests/', '-v', '--tb=no'],
        capture_output=True,
        text=True
    )
    # Parse output for PASSED/FAILED
    return parse_pytest_output(result.stdout)
```

### Step 3: 出力生成
```python
def generate_report(test_info, test_results):
    """Generate report in specified format."""
    for test in test_info:
        status = test_results.get(test['name'], 'UNKNOWN')
        print(f"ケース: {test['name']}")
        print(f"チェックしている内容: {test['purpose']}")
        print(f"結果: {status}")
        print()
```

## 期待される出力例

```
ケース: test_arithmetic_edge_cases::test_large_numbers
チェックしている内容: 大きな数値の算術演算が正しく処理されるか
結果: PASS

ケース: test_unification::test_occurs_check
チェックしている内容: occurs check による循環参照検出
結果: PASS

ケース: test_recursive_rules::test_left_recursion
チェックしている内容: 左再帰の検出とエラー処理
結果: FAIL (既知の制限)
```

## 成果物

1. **テストケース分析レポート**: `test-cases-report.md`
   - 631ケース全てを上記形式で記載

2. **重複分析**: `test-redundancy-analysis.md`
   - 重複/冗長なテストの特定
   - 統合推奨案

3. **カバレッジマップ**: `test-coverage-map.md`
   - 機能ごとのテストカバレッジ
   - 不足している領域の特定

## 見積もり

- **所要時間**: 2-3時間
- **方法**: Python スクリプト + 手動レビュー
- **コスト**: ゼロ（ローカル実行）

## 教訓

**原則**: 完成形を明確にし、適切な指示でGeminiにコードを読ませる。

### 失敗の原因
1. **完成形が不明確だった**
   - 出力形式の具体例をGeminiに提供しなかった
   - 期待する分析の深さを明示しなかった

2. **Geminiへの指示が曖昧だった**
   - 「テストケースを分析して」だけでは不十分
   - 「この形式で出力」を明確に指示すべきだった

3. **ユーザーに確認しなかった**
   - 完成形が想定できない場合は、必ずユーザーに聞く
   - サンプル出力を作成し、承認を得るべきだった

### 正しいアプローチ
1. **完成形を明確にする**
   - 具体的な出力例を作成
   - ユーザーに確認して承認を得る

2. **Geminiに適切な指示を出す**
   - テストコードを読ませる（人間より高速・正確）
   - 期待する形式と具体例を提示
   - 631ケース分の大量処理に活用

3. **不明な場合はユーザーに聞く**
   - 想定できない要件は必ず確認
   - 中間成果物で方向性を検証

---

**作成者**: Claude Sonnet 4.5
**レビュー**: 未
**承認**: 未
