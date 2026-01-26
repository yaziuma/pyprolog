# pyprolog 縮小版仕様：dynamic 宣言・述語存在・動的更新

## 目的

本仕様は pyprolog における **「述語の存在（existence）」と dynamic 宣言」**の意味論を、
以下の制約のもとで **安定かつ実装可能な形に確定**することを目的とする。

- ISO / SWI-Prolog 完全互換は目標にしない
- 一般的な Prolog 構文が動作すること
- ベンチマークおよび動的更新で破綻しないこと
- 実装容易性と保守性を最優先する

---

## 用語整理

- **存在する述語**  
  呼び出したときに `existence_error` を出さず、探索または fail に進む述語。

- **未定義述語**  
  宣言・assert・rule 定義のいずれも行われていない述語。

- **dynamic 述語**  
  `:- dynamic p/1.` または `asserta/assertz` により動的に生成された述語。

---

## 1. Parser 仕様（directive 受理）

### 1.1 受理する directive

以下のみを **構文として正式に受理**する。

```prolog
:- dynamic p/1.
````

* `dynamic` 以外の directive（multifile, thread_local 等）は **非対応**
* directive は **Rule / Fact の AST に混在させない**

### 1.2 parse error の原因（現状）

* `Parser._parse_primary()` が `COLONMINUS (:-)` を受理しない
* そのため `:- dynamic p/1.` は `Expected expression` で失敗する

### 1.3 採用する最小ルート

**案A（確定）**
`_parse_rule()` 冒頭で `COLONMINUS` を検出し、directive 専用分岐で消費する。

* directive は AST として返さず
* `(name, arity)` 情報のみを収集し、Runtime / LogicInterpreter に伝播する

---

## 2. predicate indicator の解釈

### 2.1 表現形式

`p/1` は以下の AST として扱う。

```python
Term(Atom("/"), [Atom("p"), Number(1)])
```

### 2.2 根拠

* `/` は二項演算子として operator registry に登録済み
* 既存の式パーサで **安全に一意に解釈可能**
* 追加 AST ノード不要

---

## 3. 述語存在（existence）の最終仕様

### 3.1 存在判定ルール（確定）

| 状態               | 呼び出し結果          |
| ---------------- | --------------- |
| dynamic 宣言あり・節あり | 探索              |
| dynamic 宣言あり・節なし | fail            |
| assert により生成・節あり | 探索              |
| assert により生成・節なし | fail            |
| 未宣言・未定義          | existence_error |

### 3.2 具体例

```prolog
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).        % → fail
```

```prolog
q(X).        % → existence_error(procedure, q/1)
```

---

## 4. predicate registry（存在レジストリ）

### 4.1 導入理由

現状は以下の問題がある：

* `rules_by_pred` が空になると existence_error が出る
* dynamic 宣言のみでは存在を保持できない
* retract で最後の節を消すと「未定義扱い」になる

### 4.2 データ構造

```python
predicate_registry: set[tuple[str, int]]
```

### 4.3 配置場所（決定）

**LogicInterpreter に配置する**

理由：

* existence 判定の責務が `solve_goal()` に集中している
* rules / index / existence を同一層で完結できる

---

## 5. registry 更新責務

### 5.1 更新ルール（確定）

| 操作                | registry   |
| ----------------- | ---------- |
| `:- dynamic p/1.` | add        |
| `asserta/1`       | add（未登録なら） |
| `assertz/1`       | add（未登録なら） |
| `retract/1`       | **削除しない**  |
| `retractall/1`    | **削除しない**  |
| `abolish/1`       | ※非対応（将来検討） |

---

## 6. existence_error 判定ロジック

### 6.1 現行ロジック（要変更点）

```python
if key not in rules_by_pred:
    raise PrologError(existence_error)
```

### 6.2 差し替え後の判定順（確定）

```text
1. true / fail → 除外
2. registry に存在しない → existence_error
3. registry に存在するが clause 0 → fail
4. clause あり → 通常探索
```

---

## 7. index 更新と整合性

### 7.1 既存モデル

* add_rule / remove_rule が以下を更新：

  * rules
  * rules_by_pred
  * rules_by_pred_arg0
  * _rules_len

### 7.2 registry 導入後

* index 更新モデルは **変更しない**
* existence 判定のみ registry に切り出す

---

## 8. retract の削除順序

### 8.1 仕様判断

* **削除順序は仕様として固定しない**
* 現行の LIFO 実装を許容

### 8.2 最低保証（ガードレール）

* 1回の retract で必ず 1節削除される
* 繰り返しで全節が消える
* 削除後に幽霊節が残らない

---

## 9. ガードレールテスト要件

### GR1: 未定義述語

```prolog
q(X).  % existence_error
```

### GR2: dynamic + retract

```prolog
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).  % fail
```

### GR3: index 整合性

```prolog
assertz(p(1)).
retract(p(1)).
p(X).  % fail（幽霊節なし）
```

---

## 10. 非対応・将来検討事項（明示）

* retractall/1 の意味論
* abolish/1 の導入
* unknown flag
* ISO / SWI 完全互換

---

## 最終結論

本仕様は **pyprolog の縮小版 Prolog として十分な一貫性と安定性を持つ**。

* dynamic 宣言は構文・意味論ともに安定
* existence_error は typo 検出に有効
* ベンチマークと動的更新に悪影響なし
* 実装コストは最小

この仕様を **最終仕様（Phase確定）** とする。

```

---
