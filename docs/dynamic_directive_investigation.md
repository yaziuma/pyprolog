# pyprolog dynamic 宣言調査メモ

## 目的（必ず最初に入れる）
pyprolog において `:- dynamic p/1.` を **構文として受理し、述語存在（existence）の意味論を最低限安定させる**ために必要な調査を行う。
ISO 準拠や SWI 完全互換は不要。ベンチや性能は最小影響に留める。
実装はまだ行わず、調査と設計案のみを求める。

---

## A. Parser / AST の調査（最重要）

### A.1 トップレベル構文の解析フロー
- **入口関数**: `Parser.parse()` が「ファイル/文字列全体」の解析入口で、`while` ループ内で `_parse_rule()` を繰り返す設計。
- **呼び出し階層**:
  - `Runtime.add_rule()` → `Scanner(...).scan_tokens()` → `Parser(...).parse()`
  - `Runtime.consult()` → `Scanner(...).scan_tokens()` → `Parser(...).parse()`
- **ファクト/ルールの終了判定**: `Parser.parse()` が `_parse_rule()` の戻り値を採用した後、次トークンが `.`（`TokenType.DOT`）であることを要求し、無い場合は `Expected '.' after rule or fact` を出す。

### A.2 `:-` 先頭が落ちている原因
- **tokenizer の `COLONMINUS` 生成**: `Scanner._scan_token()` で `':'` の直後に `'-'` を検出すると `TokenType.COLONMINUS` を生成する。
- **parser 側の失敗箇所**:
  - `Parser._parse_rule()` 冒頭で `_parse_expression_with_precedence(1199)` を呼ぶ。
  - 先頭トークンが `COLONMINUS` の場合、`_parse_expression_with_precedence()` → `_parse_primary()` に落ちるが、`_parse_primary()` の `self._match(...)` には `COLONMINUS` が含まれないため、末尾の `self._error(..., "Expected expression")` が発火する。

### A.3 Directive を受理するための最小分岐案
- **parser.parse() / _parse_rule() への最小変更**:
  - `_parse_rule()` の冒頭で `COLONMINUS` を検出したら「directive ルート」に分岐し、`dynamic` + predicate indicator を 1 つの単位として読み取る。
- **AST ノード導入なし vs 導入あり**:
  - **導入なし**: `Rule/Fact` と混同しないため、directive を `Rule/Fact` の戻り値に混ぜず、上位層で処理する必要がある。
  - **導入あり**: `Directive` ノードを追加し、`parse()` の戻り値に混在させるが、`Runtime.add_rule()` / `consult()` が `Rule/Fact` 以外を理解できるよう修正が必要。
- **混同回避のポイント**:
  - `Fact(Term(':-', ...))` として返すと `LogicInterpreter` 側にある「`Term(':-', [H,B])` を rule とみなすパッチ」により directive が rule と誤認されるため避けるべき。

---

## B. Directive 表現の最小設計

### B.1 AST で directive ノードを追加する場合
- **拡張すべき AST**: `Directive` ノードを新設し、`functor` と `args` を持つ形。
- **構造案**: `Directive(Atom('dynamic'), [Term('/', [Atom('p'), Number(1)])])` のように predicate indicator を保持。
- **flow への影響**:
  - `Parser.parse()` が `Directive` を返すようになる。
  - `Runtime.add_rule()` / `consult()` が `Directive` を解釈して registry を更新する責務が追加される。
  - `LogicInterpreter.solve_goal()` が registry を参照する実装が必要。

### B.2 AST を増やさない（特別扱い）案
- **成立可否**: 成立する。directive を `Rule/Fact` に混ぜず、情報だけ抽出して上位層に渡せばよい。
- **必要なデータ**: predicate indicator（`name/arity`）のペアだけで十分。
- **伝達方法**: `Parser.parse()` が副作用で「directive 情報」を収集し、`Runtime.add_rule()` / `consult()` がそれを受け取って registry を更新する方式が最小。

---

## C. 述語存在（existence）の現状の整理

### C.1 existence_error が投げられる実装箇所
- **箇所**: `LogicInterpreter.solve_goal()` のみ。
- **条件**: `actual_goal` が `true/0`・`fail/0` 以外で、`rules_by_pred` に `(name, arity)` のキーが存在しない場合。
- **参照データ構造**: `LogicInterpreter.rules_by_pred` のみ。

### C.2 現行の「述語存在判定」の仕様化
- **仕様**: `rules_by_pred` に `(name, arity)` のキーがある場合のみ「存在」と判定。
- **clause 数**: `rules_by_pred` の値（clause 数）そのものは直接参照していない。

---

## D. predicate registry 導入時の最小責務

### D.1 なぜ registry が必要か（動的宣言の背景）
- `dynamic` 宣言だけで clause が 0 の場合、`rules_by_pred` にキーが作られない。
- その結果、`solve_goal` が existence_error を投げてしまう。
- `retract` により最後の clause が消えた場合も `rules_by_pred` のキーが削除され、宣言済みでも existence_error 扱いになる。
- よって「宣言済みで clause 0」の状態を保持するための registry が必要。

### D.2 registry の最小データ構造案
- **最小構成**: `set[(name, arity)]` で十分。
- **保持場所**:
  - `Runtime` に置き、`LogicInterpreter.solve_goal()` から参照するのが最小。
  - `LogicInterpreter` に置く場合も可だが、`Runtime` / builtin / consult から更新する経路が必要。

### D.3 solve_goal の existence 判定をどう変えるか
- **現行**: `rules_by_pred` にキーがなければ existence_error。
- **変更案**:
  1) registry に無ければ existence_error
  2) registry にあるが clauses = 0 → fail
  3) clause があれば通常検索
- **挿入位置**: `LogicInterpreter.solve_goal()` の「未定義述語は existence_error」ブロック（`rules_by_pred` を直接見る部分）に差し込むのが最小。

---

## E. builtin の更新責務（asserta/assertz/retract/retractall）

### E.1 現行で何を更新しているか
- **asserta/assertz**: `runtime.logic_interpreter.add_rule()` を呼び、`rules` / `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len` を更新。
- **retract**: `runtime.logic_interpreter.remove_rule()` を呼び、`rules` / `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len` を更新。
- **retractall**: 実装は見当たらず未実装。

### E.2 registry を入れたときの責務
- **dynamic 宣言**: registry へ (name, arity) を追加。
- **assertz/asserta**: registry に存在しない場合は追加する方針が必要（宣言無し assert を存在扱いにするかどうか）。
- **retract/retractall**: registry からは削除しない。
- **abolish**: 未実装なら扱わない。

---

## F. ガードレールとの整合（現状コードで壊れる点）

### GR1
```
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).    % fail
```
- **未対応**: parser が `:-` 先頭を受理できず parse error。
- **仮に directive を通しても**: `retract` 後は `rules_by_pred` からキーが削除されるため existence_error になる。

### GR2
```
q(X).    % existence_error（未宣言・未定義）
```
- 現行は `rules_by_pred` にキーがない場合に existence_error を投げるため成立。

### GR3
```
:- dynamic p/1.
assertz(p(1)). assertz(p(2)). assertz(p(3)).
retract(p(X)).   % X=1,2,3 の順、各回で削除
```
- 現行 `DynamicRetractPredicate` は `runtime.rules` を後ろから走査し、最初に一致した clause を削除する。
- `assertz` は末尾追加なので、`retract(p(X))` は `p(3)` → `p(2)` → `p(1)` の順に削除される。
- 期待順序（1→2→3）とは逆になり、ガードレール未対応。

---

## Codex への注意（必ず）
- 実装は書かないこと
- 推測ではなく「ソースコードを読んで結論を出すこと」
- 未確認要素は未確認と書くこと
- 最終的に「最小修正で directive 対応が可能か」を結論として1案提示すること

---

## 追加で聞きたい（実機挙動比較／optional）
※ 実機アクセスできればでOK、未確認でも構わない

**未確認**: 本環境では SWI/YAP/GNU の実機確認を行っていないため、以下は未確認。
- dynamic 宣言のみで `p(X)` を呼んだ場合の挙動
- assertion だけで動的述語削除後 `p(X)` の挙動
- retractall の存在判定への影響
- abolish の挙動（attribute 削除か existence まで消すか）

---

## まとめ（1行）
このパケットは「最小で directive を parse し、dynamic existence semantics を最低限安定させるための**コード走査＋設計案**」を求める。

---

## 最小修正で directive 対応が可能か（結論）
- **可能**: `_parse_rule()` 冒頭で `COLONMINUS` を検出し directive 専用分岐を設ける。
- **最小ルート**: directive 情報（`name/arity`）だけを収集して registry を更新し、`Rule/Fact` の AST とは分離する。
- **existence 判定**: `LogicInterpreter.solve_goal()` の存在判定を registry 参照に差し替えることで、宣言済み clause 0 の場合を `fail` にできる。

