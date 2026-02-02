# pyprolog dynamic 宣言調査メモ（最終版）

## 目的（先頭固定）
- `:- dynamic p/1.` を **構文として受理**
- 述語存在（existence）を **最低限安定**
- ISO/SWI完全互換は不要、**ベンチと意味論の安定**が最優先
- 実装はしないで、**調査と設計案のみ**

---

## A. Parser が `:-` を受理できない原因（コード位置付き）

1. **入口フロー**
   - `Runtime.add_rule()` → `Scanner(...).scan_tokens()` → `Parser(...).parse()`
   - `Runtime.consult()` → `Scanner(...).scan_tokens()` → `Parser(...).parse()`
   - 解析単位は `Parser.parse()` のループ内で `_parse_rule()` を繰り返す設計。
   - 終端の `.` は `Parser.parse()` が `TokenType.DOT` を要求して確定。

2. **COLONMINUS トークン生成位置**
   - `Scanner._scan_token()` が `':'` の直後に `'-'` を検出した場合に `TokenType.COLONMINUS` を生成する。

3. **`Expected expression` の発火地点**
   - `Parser._parse_rule()` 冒頭で `_parse_expression_with_precedence(1199)` を呼ぶ。
   - 先頭トークンが `COLONMINUS` の場合、`_parse_expression_with_precedence()` → `_parse_primary()` に落ちる。
   - `_parse_primary()` の `self._match(...)` に `COLONMINUS` が含まれていないため、最後の `self._error(..., "Expected expression")` が発火。

4. **落ちる分岐の具体箇所**
   - `_parse_primary()` の `if self._match(...)` に `COLONMINUS` が入っていないことが直接原因。

> 最小修正で直すなら、`_parse_rule()` 冒頭に `COLONMINUS` 先頭の分岐を追加して directive ルートへ誘導するのが最小。

---

## B. Directive を受理する最小ルート案（2案）

### 案1：ASTノードを増やさない
- directive を `Rule/Fact` に混ぜず、`name/arity` だけを収集して上位層へ渡す。
- `Term(':-', ...)` を rule と誤認する既存パッチ（`LogicInterpreter` 側）と衝突しない設計。
- **影響範囲**:
  - parser: `_parse_rule()` 冒頭で `COLONMINUS` を検出して directive 情報を抽出
  - runtime: `add_rule/consult` が directive 情報を受け取り registry を更新
  - logic_interpreter: existence 判定を registry 参照へ変更

### 案2：Directive ノードを追加
- `Directive(Atom('dynamic'), [Term('/', [Atom('p'), Number(1)])])` のような構造を導入。
- `Parser.parse()` が `Directive` を返すようになり、`Runtime.add_rule/consult` が directive を解釈して registry を更新する責務が増える。
- **影響範囲**:
  - parser: 新AST生成
  - runtime: `Rule/Fact` 以外のノードを受理する分岐追加
  - logic_interpreter: existence 判定で registry を参照

> **最小で安全**なのは案1（AST追加なし）。directive を rule と誤認する既存パッチの影響を避けられるため。

---

## C. “述語存在”の現状仕様（1文）と変更点

- **現状仕様**: `LogicInterpreter.solve_goal()` が `rules_by_pred` に `(name, arity)` キーが無い場合、`existence_error` を投げる（`true/0`・`fail/0` を除く）。
- **唯一の発火点**: `LogicInterpreter.solve_goal()` の existence 判定ブロックのみ。

---

## D. predicate registry の最小設計

1. **registry が必要な理由（コードパス）**
   - dynamic 宣言のみで clause が 0 → `rules_by_pred` にキーが無い → `solve_goal` が `existence_error`。
   - `retract` で最後の clause が消える → `rules_by_pred` のキーが削除される → 同様に `existence_error`。

2. **最小データ構造**
   - `set[(name, arity)]` で十分。

3. **配置場所（最小）**
   - `Runtime` に置き、`LogicInterpreter.solve_goal()` から参照するのが最小。

4. **solve_goal の existence 判定差し込み位置**
   - `LogicInterpreter.solve_goal()` の「未定義述語は existence_error」ブロックで、`rules_by_pred` 参照前に registry を参照。
   - 分岐:
     - registry 無し → `existence_error`
     - registry 有り & clause 0 → `fail`
     - clause 有り → 通常探索

---

## E. builtin の更新責務（追加で必要なことだけ）

- **現状更新対象**:
  - `asserta/assertz` → `rules` / `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len`
  - `retract` → 同上
  - `retractall` / `abolish` → 未実装

- **registry 導入後の最小責務**:
  - `dynamic` 宣言 → registry に (name, arity) を追加
  - `asserta/assertz` → registry に無ければ追加（宣言無し assert を存在扱いにするか方針決め）
  - `retract/retractall` → registry からは削除しない

---

## F. ガードレール評価（現状コード）

- **GR1**: dynamic → assertz → retract → `p(X)` は fail になるべき
  - 現状は parser が `:-` を受理できず parse error。
  - 仮に通しても `retract` 後に `rules_by_pred` が消えるため existence_error。

- **GR2**: 未宣言未定義 `q(X)` は existence_error
  - 現行の `rules_by_pred` 判定で成立。

- **GR3**: `retract(p(X))` が 1→2→3 順で返るべき
  - 現行 `DynamicRetractPredicate` は `runtime.rules` を後ろから走査するため 3→2→1 になる。

---

## 最後に：結論（1案のみ）

**最小修正ルート**:
1. `_parse_rule()` 冒頭で `COLONMINUS` を検出し directive 専用分岐へ。
2. directive は AST に混ぜず、`name/arity` ペアだけ収集して registry を更新。
3. `LogicInterpreter.solve_goal()` の existence 判定を registry 参照に差し替える。

