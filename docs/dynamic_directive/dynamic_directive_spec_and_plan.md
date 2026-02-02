# Dynamic Directive & Existence Semantics

## Fixed Spec + Implementation Plan（最終確定版）

## 1. Goals / Non-Goals

### Goals（サポートする）

* **dynamic directive**：`:- dynamic p/1.` のみ

  * predicate indicator は既存AST表現の解釈で扱う（新ASTノード追加なし）
* **procedure existence semantics** を動的更新後も安定させる

  * `asserta/1`, `assertz/1`, `retract/1`, `retractall/1` の後でも意味論が崩れない
* **predicate registry** を `LogicInterpreter` に導入し、existence 判定を安定化
* **Parser.parse() の戻り値を変更しない**（rulesのみ返す）
* directives は **Parser内部に保持**し、呼び出し側が参照して適用
* **registry更新は `LogicInterpreter.add_rule()` に一元化**
* 最小差分・保守性最優先

### Non-Goals（明確に非対応）

* ISO / SWI 完全互換
* `multifile`, `thread_local`, `unknown` flag, `abolish/1`
* `:- dynamic p/1.` 以外の directive
* 新ASTノードの追加、Parserの戻り値型変更

---

## 2. Final Spec（仕様確定）

## 2.1 Existence semantics（procedure existence）

**`LogicInterpreter.solve_goal()` の判定順序（固定）**

1. `true/0`, `fail/0`：既存挙動維持（特殊扱いのまま）
2. `(name, arity)` が **predicate_registry に無い**
   → `existence_error(procedure, name/arity)`
3. `(name, arity)` が **predicate_registry にある** が **clause 0**
   → **fail**（existence_error ではない）
4. clause がある → 通常探索・評価

**例**

* 未定義（未登録）

  ```prolog
  q(X).           % existence_error(procedure, q/1)
  ```
* dynamic 宣言のみ（節なし）

  ```prolog
  :- dynamic p/1.
  p(X).           % fail
  ```
* 全節削除後（存在は保持される）

  ```prolog
  :- dynamic p/1.
  assertz(p(1)).
  retract(p(1)).
  p(X).           % fail
  ```

---

## 2.2 Dynamic directive（受理条件・エラー条件を完全固定）

### 受理するのはこれだけ

```prolog
:- dynamic p/1.
```

### predicate indicator の妥当性（固定）

`p/1` は既存パーサが生成する AST を用い、以下の形のみを受理する：

* **演算子 `/` の Term**
* 左項：Atom（predicate名）
* 右項：Number（arity、整数として解釈可能）

受理できない形（例：arityが整数でない、Atomでない等）は **directive parse error** とする。

### dynamic以外のdirective（固定）

* `:- dynamic p/1.` 以外の directive は **必ず parse error**

  * **ignore はしない**
  * 「非対応を黙殺」はデバッグを破壊するため禁止

### ASTについて（固定）

* 新しいASTノードは追加しない
* directiveは Rule/Fact AST に混在させない（Parser内部に保持）

---

## 2.3 Predicate registry（存在レジストリ）

### データ構造（固定）

* `LogicInterpreter.predicate_registry: set[(name:str, arity:int)]`

### registryキーの正規化（固定）

* name：Atom名の文字列
* arity：int

### 更新ルール（固定）

| 操作                | registry   |
| ----------------- | ---------- |
| `:- dynamic p/1.` | add        |
| `asserta/1`       | add（未登録なら） |
| `assertz/1`       | add（未登録なら） |
| `retract/1`       | 削除しない      |
| `retractall/1`    | 削除しない      |
| `abolish/1`       | 非対応        |

---

## 2.4 Retract ordering（削除順序）

* 削除順序は仕様として固定しない（LIFO/FIFOどちらでも可）
* ただし最低保証（固定）：

  * `retract/1` は **1回で必ず1節だけ**削除
  * 繰り返しで全節が消える
  * 削除後に **幽霊節（index残骸）が残らない**

---

## 3. Architecture & Data Flow（確定）

## 3.1 データ配置

* `LogicInterpreter`：`predicate_registry` を保持
* `Parser`：directive を内部保持

  * `Parser.parse()` は rules だけ返す（固定）

## 3.2 directive の保持形式（固定）

Parserは directive を次の軽量形式で保持する：

* `("dynamic", name:str, arity:int)` のリスト
  例：`[("dynamic", "p", 1), ...]`

※ predicate indicator の Term を保持して伝播する設計は採らない（最小差分・実装容易性のため）。

## 3.3 1回の consult/load における順序（固定）

1. parse：`rules = Parser.parse()`
2. directives取得：`directives = Parser.directives`
3. **directiveを先に全適用**：`apply_dynamic` を呼ぶ
4. その後 rules を `add_rule()` で追加

この順序を **常に**守る（同一ファイル内・複数ファイルでも consult単位で同じ）。

---

## 4. Impact Map（ファイル/関数別・確定責務）

| Area             | 主責務                    | 変更対象（候補）                       | Change Type | 変更内容                                                                                      |
| ---------------- | ---------------------- | ------------------------------ | ----------- | ----------------------------------------------------------------------------------------- |
| Parser           | `:- dynamic` を捕捉し内部保持  | Parser実装（`_parse_rule()` 入口など） | Modify      | `COLONMINUS` を見たら dynamic strict match、directiveを `directives` に格納。dynamic以外はparse error。 |
| Loader/Consult   | directives適用 → rules追加 | consult/load経路                 | Add/Modify  | parse後に directives を先に apply、次に rules を add_rule。                                         |
| LogicInterpreter | registry保持             | `LogicInterpreter`             | Add         | `predicate_registry` 追加、初期化。                                                              |
| LogicInterpreter | directive適用            | `apply_dynamic(name, arity)`   | Add         | registry addのみ（節0でも存在）。                                                                   |
| LogicInterpreter | registry更新一元化          | `add_rule()`                   | Modify      | rule追加前に `(name, arity)` を registry add（setなので重複OK）。                                      |
| LogicInterpreter | existence判定            | `solve_goal()`                 | Modify      | 4段階順序に差し替え（true/fail例外→registry判定→clause数→評価）。                                            |
| Builtins         | assert系の経路統一           | `asserta/1`, `assertz/1`       | Modify      | 最終的に `add_rule()` 経由に統一（registry更新を漏らさない）。                                                |
| Builtins         | retract系               | `retract/1`, `retractall/1`    | Modify      | registryは触らない。index幽霊節なしを維持。                                                              |

### Red flags（事故ポイント）

* `:-` は directive と rule（`H :- B`）の両方で出る
  → **dynamicの厳格パターン一致**以外は directive扱いしない
* `solve_goal()` の判定順序が崩れると existence_error/fail が逆転する
* clause追加経路が `add_rule()` をバイパスすると registryが欠ける

---

## 5. Task Breakdown（コミット単位・最小差分）

### Task 1: Parser directive capture（厳格）

* **変更**：`:- dynamic p/1.` を strict match で捕捉し `Parser.directives` に格納
* **固定**：dynamic以外のdirectiveは parse error（無視しない）
* **受入条件**：

  * `Parser.parse()` の戻り値（rules）の型・形は変わらない
  * `Parser.directives == [("dynamic","p",1), ...]` 形式になる

### Task 2: LogicInterpreter に registry を導入

* `predicate_registry` と `apply_dynamic(name, arity)` を追加
* **受入条件**：導入だけで既存挙動は変えない（まだsolve_goalは触らない）

### Task 3: `add_rule()` で registry 更新を一元化

* clause挿入前に registry add
* **受入条件**：consult/assert経由の追加で registryが必ず埋まる

### Task 4: consult/load 経路で directive を先適用

* parse後に directives を apply → rules を add
* **受入条件**：`:- dynamic p/1.` のみで `p(X).` が fail になる

### Task 5: `solve_goal()` を最終仕様に差し替え

* 4段階順序（true/fail例外→registry→clause数→評価）
* **受入条件**：セクション2.1の例が仕様通り

### Task 6: Builtins（assert/retract）整合

* `assert*` が `add_rule()` を経由することを保証
* `retract*` は registryを触らない
* **受入条件**：runtime assert直後でも registryが埋まる

### Task 7: Guardrail tests（意味論のみ）

* 3ケースだけ追加（後述）
* **受入条件**：意味論の境界（existence_error vs fail）と幽霊節なしが守られる

---

## 6. Guardrail Tests（意味論のみ・固定）

### Case A: 未定義 → existence_error

```prolog
q(X).            % existence_error(procedure, q/1)
```

### Case B: dynamic + retract → fail

```prolog
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).            % fail
```

### Case C: index整合（幽霊節なし）

```prolog
assertz(p(1)).
retract(p(1)).
p(X).            % fail
```

---

## 7. Implementation Checklist（安全順）

* [ ] Parser：`:- dynamic p/1.` だけを strict match で捕捉できている
* [ ] Parser：dynamic以外directiveは必ず parse error
* [ ] Parser：directives形式は `("dynamic", name, arity)`
* [ ] consult/load：directives → rules の順で処理（必ず先適用）
* [ ] LogicInterpreter：registry導入、`apply_dynamic` が addするだけ
* [ ] add_rule：全ルール挿入がここを通る、registry更新がここで完結
* [ ] solve_goal：4段階順序が固定されている
* [ ] Builtins：assert* は add_rule 経由、retract* は registry不干渉
* [ ] Guardrails：3本のみで意味論を守る

### 失敗時の切り分け

* directiveが効かない → Parser捕捉 or consult順序
* existence_error/fail逆転 → solve_goal順序 or registryの埋まり
* 幽霊節 → retract実装 or index更新

---

## 8. Risks & Rollback（固定）

### 主要リスク

* `:-` の誤判定で `H :- B` が directive として吸われる
* add_rule バイパス経路が残って registryが欠ける
* retract の index cleanup 不備で幽霊節

### ロールバック手順

* Task 7 → 1 の逆順で戻す（高リスク変更から剥がす）

---

## 要点まとめ（最終確定）

* **unsupported directive は必ずエラー**（ignore禁止）
* **dynamic predicate indicator 不正はエラー**
* **consult単位で directives を先に全適用→その後 rules**
* directiveは `("dynamic", name, arity)` の軽量形式で保持
* registry更新は **add_rule一元化**
* solve_goal は **4段階順序を固定**

