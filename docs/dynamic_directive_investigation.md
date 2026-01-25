# pyprolog dynamic 宣言調査メモ

## 前提（必ず最初に伝える）
目的は「pyprolog に dynamic 宣言（:- dynamic p/1.）を構文として受理し、述語存在 semantics を最小スコープで安定させること」。
ISO完全準拠や SWI 完全互換は不要。ベンチマーク性能と意味論の安定が最優先。
実装は行わず、コードベース調査と設計案の提示のみを行う。

---

## 調査A：parser / AST 周り（最重要・入口）

### A-1. トップレベル構文の流れ
- **トップレベル parse 関数**: `Parser.parse()` が「ファイル/文字列全体」の解析入口で、`while` ループで `_parse_rule()` を繰り返し、各ルール/ファクトの末尾に `.` を要求する設計。
- **rule / fact の確定時点**: `_parse_rule()` が先頭項（head）を解析した後、`COLONMINUS (:-)` が続けば `Rule(head, body)`、続かなければ `Fact(head)` として確定する。
- **どこから呼ばれるか**: `Runtime.add_rule()` と `Runtime.consult()` が `Scanner(...).scan_tokens()` → `Parser(...).parse()` を呼び、`Rule`/`Fact` のみを DB に追加している。

### A-2. `:-` が落ちている理由の特定
- **tokenizer が `:-` をトークンとして持っているか**: `Scanner._scan_token()` が `':'` の直後に `'-'` を見れば `TokenType.COLONMINUS` を作るため、`:-` はトークンとして存在する。
- **parser のどの分岐で「Expected expression」になっているか**:
  - `Parser._parse_rule()` は先頭で `_parse_expression_with_precedence(1199)` を呼ぶ。
  - 入力 `:- dynamic p/1.` では先頭トークンが `COLONMINUS` なので、`_parse_expression_with_precedence()` → `_parse_primary()` に落ち、`COLONMINUS` を受理できないため `self._error(..., "Expected expression")` となる。
- **「式開始禁止」になっている箇所**: `Parser._parse_primary()` の `if self._match(...)` ブロックに `COLONMINUS` が含まれておらず、末尾で無条件に `Expected expression` を投げるのが直接原因。

### A-3. Directive を入れる最小差分案（調査のみ）
最小差分の候補は以下。
1. **トップレベル parse ループで directive 専用分岐を追加**
   - `parse()` もしくは `_parse_rule()` 冒頭で `COLONMINUS` を検出し、ディレクティブ項（`dynamic p/1` など）を 1 項として読み込む。
   - AST を追加するか、既存 `Fact/Rule` を流用するかは次項で分岐。
2. **AST ノード追加（Directive）を導入**
   - `Directive(functor=Atom('dynamic'), args=[Term('/', [Atom('p'), Number(1)])])` 等の形で保持。
   - 既存 Rule/Fact とは異なるので、トップレベルで `Directive` を認識する必要がある。
3. **AST 追加なし（特別扱い）**
   - parser が `COLONMINUS` を検出した時点で「directive のみを抽出」し、`parse()` の戻り値には含めず、`consult`/`add_rule` など上位層でハンドリングする。
   - 既存 Rule/Fact を流用する案は、`Fact(Term(':-', ...))` に混ぜると `LogicInterpreter` 側の「`Term(':-', [H,B]) を rule とみなすパッチ」へ引っかかるため、**directive を rule と誤認**するリスクが高い。

---

## 調査B：dynamic 宣言の表現方法（AST or 中間表現）

### B-1. AST 拡張案
Directive ノードを導入する場合の影響範囲は以下。
- **parser**: `COLONMINUS` 先頭で Directive を構築する分岐を追加。
- **Runtime.add_rule / consult**: `Rule`/`Fact` 以外の AST を受け取り、`dynamic` などの directive を解釈して registry を更新する責務を追加。
- **LogicInterpreter**: existence 判定で registry を参照する実装が必要。

### B-2. AST を増やさない案
成立は可能だが、**「どこで directive を処理するか」**を明確にする必要がある。
- **成立させるなら**:
  - parser が `COLONMINUS` を検出した瞬間に directive 情報（`name/arity` の一覧）を抽出し、`parse()` の戻り値には含めない方式。
  - directive 情報は `Runtime.consult()` / `add_rule()` の層で受け取り、registry だけ更新するのが最小。
- **後段に渡すべき情報**:
  - `predicate name` と `arity` のペアの集合（`set[(name, arity)]`）のみで十分。
  - 余計な AST を保持しないため、`dynamic` 以外の directive を扱わない前提なら、`dynamic` 専用のデータ構造で良い。

---

## 調査C：述語存在（existence）判定の現状整理

### C-1. existence_error の唯一の発火点
- `LogicInterpreter.solve_goal()` にのみ存在する。
  - `actual_goal` が `true/0`・`fail/0` 以外で、`rules_by_pred` にキーが存在しない場合、`existence_error(procedure, name/arity)` を投げる。
  - 参照しているデータ構造は `LogicInterpreter.rules_by_pred` のみ。

### C-2. 現行仕様の形式化
**「述語が存在する」= `rules_by_pred` に (name, arity) のキーが存在すること。**
（実際の clause 数は問われないが、キーがなければ existence_error。）

---

## 調査D：predicate registry 導入時の最小責務

### D-1. registry が必要になる理由の整理
- 現行は `rules_by_pred` が「存在」の唯一判定。
- dynamic 宣言だけで clause が 0 の場合、`rules_by_pred` にキーが作られないため、`solve_goal` が existence_error を投げる。
- `retract` により最後の clause が消えると `rules_by_pred` からキーが削除されるため、**dynamic 宣言済みでも存在しない扱い**になる。
- したがって、**宣言済みで clause が 0 の状態を保持する別レジストリ**が必要。

### D-2. registry の最小データ構造案
- **最小構成**: `set[(name, arity)]` で十分。
- **保持場所**:
  - `Runtime` に置き、`LogicInterpreter.solve_goal()` から参照する形がシンプル。
  - もしくは `LogicInterpreter` が所有し、`Runtime` から更新メソッドを呼ぶ形でもよいが、builtin/consult から共通アクセスできる設計が必要。

### D-3. solve_goal の existence 判定変更点
- 現在の `solve_goal` の existence 判定ブロック
  - `if key not in self.rules_by_pred: raise existence_error`
- これを以下に変更する必要がある:
  1. **registry にも存在しない** → `existence_error`
  2. **registry にはあるが clause 0** → `fail`（候補集合が空）
  3. **registry と rules の両方にある** → 従来どおり探索
- 変更箇所は `LogicInterpreter.solve_goal()` の existence 判定ブロック（`rules_by_pred` を直接見る部分）に挿入するのが最小。

---

## 調査E：dynamic / retract 系 builtin の責務再確認

### E-1. asserta/assertz/retract/retractall の現在の更新対象
- **asserta/assertz**
  - `runtime.logic_interpreter.add_rule()` を呼ぶ。
  - `add_rule()` は `runtime.rules` と `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len` を更新。
- **retract**
  - `runtime.logic_interpreter.remove_rule()` を呼ぶ。
  - `remove_rule()` は `runtime.rules` と `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len` を更新。
- **retractall**
  - 現行コードに実装は見当たらない（未実装）。

### E-2. registry を入れた場合の追加責務
- **dynamic 宣言**: registry に (name, arity) を追加。
- **asserta/assertz**: registry に存在しない場合は追加（宣言無しでも assert されたら存在扱いにするかどうかの方針次第）。
- **retract / retractall**: registry からは削除しない（宣言を維持するため）。
- **abolish**: 未実装なら対象外。

---

## 調査F：最終ガードレールとの整合性確認

### GR1
```
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).    % fail
```
- 現行コード: `:- dynamic` が parse error で落ちるため未対応。
- たとえ directive を通しても、`retract` 後は `rules_by_pred` からキー削除 → `p/1` は existence_error を投げる。
- **壊れる箇所**: `Parser._parse_primary()` と `LogicInterpreter.solve_goal()` の existence 判定。

### GR2
```
q(X).    % existence_error（未宣言・未定義）
```
- 現行コード: `rules_by_pred` にキーが無ければ existence_error を投げるため、この動作は成立。
- registry を導入する場合、**未宣言・未定義なら registry に無い**ため existence_error は維持可能。

### GR3
```
:- dynamic p/1.
assertz(p(1)). assertz(p(2)). assertz(p(3)).
retract(p(X)).   % X=1,2,3 の順、各回で削除
```
- 現行コード: `DynamicRetractPredicate` は `runtime.rules` を後ろから走査し、最初にマッチしたものを削除する。
- `assertz` は末尾に追加するため、`retract(p(X))` は最後に追加した `p(3)` を先に削除する。
- したがって **期待順序（1,2,3）ではなく 3,2,1** になり、ガードレール未対応。

---

## Codex への注意書き（最後に必ず）
- 実装コードは書かないこと
- 推測ではなく「コードから読める事実」を優先すること
- 不明点は「未確認」と明示すること
- 最終的に「最小実装で済む設計ルート」を1つ提案すること

---

## 最小実装で済む設計ルート（提案）
- **directive をトップレベルで認識する小規模パスを追加**し、`:- dynamic p/1.` だけを通す。
  - parser は `COLONMINUS` 先頭を検出したら directive 解析に切り替え、`dynamic` と predicate spec (`p/1`) を抽出する。
  - AST を増やさず、directive 情報だけを `Runtime.consult` / `add_rule` に返す（`Rule/Fact` のリストとは別に処理）。
- **predicate registry を最小構成（set[(name, arity)]) で導入**し、existence 判定に使用。
  - `solve_goal` の存在判定は `registry` を優先参照し、registry だけ存在する場合は `fail` にする。
- **assertz/asserta は registry を補完**し、`retract` では registry を削除しない。

（未確認: parser の operator `/` の扱いが `p/1` 解析に十分かどうかは、実装時に確認が必要。）
