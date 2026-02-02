# dynamic directive / existence 判定 / retract 仕様検討書

## 目的
- dynamic directive を最小変更で受理する
- dynamic 述語の existence 挙動を安定させる
- ベンチマークと意味論を壊さないための責務分離材料を整理する
- 実装は行わず、コード根拠に基づく事実整理のみを行う

---

## T1. Parser: `:- dynamic p/1.` が受理できない原因と最小ルート

### 1) parse error の正確な分岐位置
- `Parser._parse_rule()` が `_parse_expression_with_precedence(1199)` を呼ぶため、先頭が `COLONMINUS` の場合 `_parse_primary()` に落ちる。
- `_parse_primary()` は `COLONMINUS` を受理せず、`Expected expression` で失敗する。

**根拠コード**
- `Scanner` が `:-` を `TokenType.COLONMINUS` として生成。
- `Parser.parse()` → `_parse_rule()` → `_parse_expression_with_precedence()` → `_parse_primary()` → `Expected expression` へ。

### 2) `COLONMINUS` 生成〜`Expected expression` の呼び出し経路
1. `Scanner._scan_token()` が `:-` を `COLONMINUS` として発行
2. `Parser.parse()` が `_parse_rule()` を呼び出す
3. `_parse_rule()` が `_parse_expression_with_precedence(1199)` を呼ぶ
4. `_parse_expression_with_precedence()` が `_parse_primary()` を呼ぶ
5. `_parse_primary()` が `Expected expression` で失敗

### 3) AST を増やさない最小ルート案（2案）
- **案A**: `_parse_rule()` 冒頭で `COLONMINUS` を検出し directive 用分岐を作る
  - directive 情報を Parser 内の別バッファに保存し、`Rule/Fact` の戻り値列には混在させない
- **案B**: `Parser.parse()` の while ループで `COLONMINUS` を先読みし、directive を別処理として消費
  - `parse()` の戻り値は引き続き `Rule/Fact` のみを返す

**副作用リスク**
- directive を `Rule/Fact` と同列に混在させると、下流の `Runtime.add_rule()` / `consult()` で `Rule/Fact` 前提が崩れるため、戻り値に混在させない形が安全。

---

## T2. existence 判定：registry をどこに置くのが最小か

### 1) existence_error が投げられる箇所・条件
- `LogicInterpreter.solve_goal()` のみで発生。
- `rules_by_pred` に `(name, arity)` のキーがない場合に `existence_error` を投げる。

### 2) 暗黙の存在定義（1文）
- **`rules_by_pred` に `(name, arity)` のキーが存在する場合のみ「存在」と見なす**。

### 3) registry 置き場比較（LogicInterpreter / Runtime）
| 案 | 更新責務が必要な箇所 | directive / asserta / assertz / retract との整合性 | solve_goal 側変更量 | retractall/abolish 追加時の拡張余地 |
| --- | --- | --- | --- | --- |
| A. LogicInterpreter | LogicInterpreter に registry を持たせ、builtins/consult から更新経路を追加 | directive から LogicInterpreter へ伝播が必要 | `solve_goal` の存在判定を registry 参照に差し替え | registry を中心に拡張可能 |
| B. Runtime | Runtime が registry を保持し、`solve_goal` から参照 | directive/consult の責務と近く最小 | `solve_goal` で Runtime registry を参照 | Runtime で拡張しやすい |

---

## T3. dynamic 更新と index 整合性

### 1) asserta/assertz/retract が更新している内部状態
- `asserta/assertz` は `LogicInterpreter.add_rule()` により `rules` / `rules_by_pred` / `rules_by_pred_arg0` / `_rules_len` を更新。
- `retract` は `LogicInterpreter.remove_rule()` により同じ構造を更新。

### 2) assertz → retract → call で節が 0 になる挙動
- `retract` で最後の節を削除すると `rules_by_pred` からキーが削除される。
- `solve_goal` は `rules_by_pred` のキー有無のみを見るため、存在エラーが発生する。

### 3) arg0 index の削除漏れ / フォールバック条件
- `_arg0_index_key_from_head()` が `None` の場合は arg0 index を更新しない。
- `rules_by_pred_arg0` に一致バケットがない場合は primary index にフォールバック。

### 4) registry 導入後も index 更新モデルを変えずに済むか
- index 更新は `add_rule/remove_rule` に閉じているため、registry を追加しても既存 index 更新モデルは維持可能。

---

## T4. retract の走査順と guardrail 設計への影響

### 1) 現行 retract の探索・削除順
- `DynamicRetractPredicate` は `runtime.rules` を **後ろから前へ**走査し、最初に一致した節を削除。
- この順序を採用する理由はコード内に明記されていない。

### 2) 「定義順 vs 逆順」の影響整理
- 逆順（LIFO）だと `assertz` で末尾追加した節が先に削除される。
- ガードレールは「削除できること」「幽霊節が残らないこと」を重視しており、順序自体は固定していない。

### 3) 順序を固定しない場合の guardrail 最低保証
- `retract` が 1 回で少なくとも 1 節を削除できる
- 繰り返し `retract` で全節が消える
- 削除済み節が候補に残らない（index 整合）

---

## 追加整理: directive の `p/1` 抽出最短ルート
- `dynamic p/1` の `p/1` は二項演算子 `/` として解析され、
  `Term(Atom('/'), [Atom('p'), Number(1)])` の構造になる。
- これは演算子定義と `_parse_expression_with_precedence()` の二項演算子構築ルールにより確定。

---

## 追加整理: directives を parse 戻り値に含める場合の最小差分点
- `Runtime.add_rule()` は `Parser.parse()` の戻り値を `Rule/Fact` 前提で処理しており、directive を混在させるとここが最小差分点になる。
- `Runtime.consult()` も同様に `Rule/Fact` 前提の処理を行うため最小差分点になる。

---

## 追加整理: solve_goal の existence 判定条件
- `solve_goal` は `true/0` と `fail/0` を除外した上で existence 判定を実施している。
- builtin/演算子を execute 側で処理する前提が壊れないよう、`true`/`fail` 除外条件を維持する必要がある。

---

## 意思決定に使える結論要約（3〜5行）
1. `:- dynamic` が落ちる原因は `COLONMINUS` を `_parse_primary()` が受理せず `Expected expression` になる点であり、最小ルートは `_parse_rule()` または `parse()` の先読み分岐で directive を隔離すること。
2. existence 判定は `solve_goal()` が `rules_by_pred` のキーだけを見ているため、registry 参照への差し替えはここが最小。
3. asserta/assertz/retract の index 更新は `add_rule/remove_rule` に閉じているため、registry 導入後も index 更新モデルは維持可能。
4. retract の順序は現行 LIFO だが guardrail は順序固定を要求せず、削除可能性と幽霊節排除を最低保証としておくのが安全。
