# 実装タスク分解（dynamic 宣言・述語存在・動的更新）

本ドキュメントは、`docs/dynamic_directive/pyprolog_縮小版仕様.md` の確定仕様に従い、
Parser / Runtime(interpreter) / LogicInterpreter / Builtins の4ブロックで
実装タスクと差分点、影響範囲、テスト方針を整理したもの。

---

## 1. 実装タスク分解

### 1.1 Parser

**変更対象ファイル**
- `pyprolog/parser/parser.py`

**変更対象関数**
- `Parser._parse_rule()`
- （必要なら）`Parser.parse()` の返却構造

**追加するデータ構造・責務**
- directive 収集用のコンテナ（例：`self._directives: list[Term]` または `self._dynamic_predicates: set[tuple[str, int]]`）
  - `:- dynamic p/1.` だけを受理し、AST（Rule/Fact）には混在させない。
  - p/1 は既存パーサが `Term(Atom("/"), [Atom("p"), Number(1)])` として作る前提。

**最小差分の擬似コード**
```
def _parse_rule():
    if _match(COLONMINUS):
        # directive branch
        if _match(ATOM) and previous.lexeme == "dynamic":
            indicator = _parse_term()  # expects Term("/", [Atom, Number])
            # validate indicator (functor "/" and arity 2, etc.)
            # store (name, arity) to directives
            return None  # do not emit Rule/Fact
        else:
            error("unsupported directive")
            return None
    # existing rule/fact parsing path
```

**互換性リスク**
- `:-` を rule head の一部として扱っていた既存パースパスに影響し、
  `H :- B` の通常ルール解析が壊れる可能性。
- `parse()` 返却型の変更（directive 情報の追加）により、
  呼び出し側（Runtime）が破壊される可能性。

**防止するテスト**
- 既存テスト群の再実行（regression）
- guardrail（後述）に加えて、`H :- B` が従来通り読み取れることの回帰テスト

---

### 1.2 Runtime (interpreter)

**変更対象ファイル**
- `pyprolog/runtime/interpreter.py`

**変更対象関数**
- `Runtime.__init__()`（LogicInterpreter 初期化との連携）
- `Runtime.add_rule()`
- `Runtime.consult()`
- `Runtime.query()`（directive を含むクエリ解析時の扱い）

**追加するデータ構造・責務**
- Parser から取得した directive 情報を LogicInterpreter に伝播する責務。
- 例：`Parser.parse()` が `(rules, directives)` を返すなら、
  `Runtime` がその directive を解釈し `logic_interpreter.predicate_registry` を更新。

**最小差分の擬似コード**
```
parsed_rules, directives = Parser(...).parse()
for (name, arity) in directives:
    logic_interpreter.register_predicate(name, arity, source="dynamic")
for rule in parsed_rules:
    logic_interpreter.add_rule(rule, position="last")
    # add_rule 内で registry へ追加する設計ならここでは不要
```

**互換性リスク**
- `Parser.parse()` の戻り値が変わることで `query()` / `consult()` の
  既存処理が壊れる。
- `add_rule()` / `consult()` が directive を「unknown item」として
  取り扱う可能性。

**防止するテスト**
- `consult()` 経由で directive が解釈されることの回帰テスト
- 既存の `query()` ユースケースが維持されることの回帰テスト

---

### 1.3 LogicInterpreter

**変更対象ファイル**
- `pyprolog/runtime/logic_interpreter.py`

**変更対象関数**
- `LogicInterpreter.__init__()`（registry 初期化）
- `LogicInterpreter.add_rule()`（asserta/assertz 時に registry を add）
- `LogicInterpreter.solve_goal()`（existence 判定の差し替え）
- （必要なら）新規メソッド `register_predicate()` / `ensure_predicate_registered()`

**追加するデータ構造・責務**
- `predicate_registry: set[tuple[str, int]]`
  - `:- dynamic p/1.` を add
  - `asserta/assertz` を add
  - `retract/retractall` では削除しない
  - `abolish` は今回非対応

**最小差分の擬似コード**
```
class LogicInterpreter:
    def __init__(...):
        self.predicate_registry = set()
        # existing _build_index()

    def register_predicate(name, arity):
        self.predicate_registry.add((name, arity))

    def add_rule(entry, position="last"):
        ... existing add ...
        if head is Term/Atom:
            register_predicate(pred_name, pred_arity)

    def solve_goal(goal, env):
        if functor in ("true", "fail"):
            existing logic
        key = (name, arity)
        if key not in predicate_registry:
            raise existence_error
        if key in registry and key not in rules_by_pred:
            fail  # clause 0
        else:
            normal search
```

**互換性リスク**
- 既存の existence 判定が `rules_by_pred` 依存なので、
  registry 導入により未知/既知の境界が変わる可能性。
- rule index 更新の順序と registry 更新が同期していない場合、
  一時的に存在判定がぶれる可能性。

**防止するテスト**
- guardrail テスト（未定義 → existence_error、dynamic + retract → fail）
- registry 追加/削除の境界条件（rule 0件/1件/複数件）

---

### 1.4 Builtins

**変更対象ファイル**
- `pyprolog/runtime/builtins.py`
- `pyprolog/runtime/interpreter.py`（builtins 呼び出し部分）

**変更対象関数**
- `DynamicAssertAPredicate.execute()`
- `DynamicAssertZPredicate.execute()`
- `DynamicRetractPredicate.execute()`（registry に影響しない）

**追加するデータ構造・責務**
- asserta/assertz で新規 predicate の場合に registry を add
  - `logic_interpreter.register_predicate()` へ委譲
- retract では registry を消さない（削除しない）

**最小差分の擬似コード**
```
class DynamicAssertZPredicate:
    def execute(...):
        # after building clause to add
        runtime.logic_interpreter.add_rule(entry, position="last")
        runtime.logic_interpreter.register_predicate(name, arity)
        yield env
```

**互換性リスク**
- assert 系 predicate の挙動が変わり、既存テストの期待値が変わる可能性。
- retract の削除順序（現行 LIFO）を維持しつつ、幽霊節が残る可能性。

**防止するテスト**
- retract 系の guardrail（削除後に幽霊節が残らない）
- asserta/assertz で未登録 predicate が existence_error にならない回帰

---

## 2. 実装順序

1. **Parser の directive 受理**
   - 完了条件：
     - `:- dynamic p/1.` を parse してもエラーにならない
     - Rule/Fact の AST に directive が混ざらない
2. **LogicInterpreter の registry 導入**
   - 完了条件：
     - `predicate_registry` が初期化され、`register_predicate()` が動作
     - `solve_goal()` で existence 判定順が仕様通りに切り替わる
3. **Runtime で directive を伝播**
   - 完了条件：
     - `consult()` / `add_rule()` / `query()` から directive を取り扱える
     - directive が registry に反映される
4. **Builtins で dynamic 更新**
   - 完了条件：
     - `asserta/assertz` が registry を add
     - `retract/retractall` は registry を削除しない
5. **Guardrail テスト追加**
   - 完了条件：
     - 全 guardrail が green
     - 既存 pytest が green

---

## 3. テスト（guardrails）

**GR-1: 未定義述語は existence_error**
```
q(X).  % existence_error(procedure, q/1)
```

**GR-2: dynamic 宣言 + assertz + retract → fail**
```
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).  % fail
```

**GR-3: retract 後に幽霊節が残らない**
```
assertz(p(1)).
retract(p(1)).
p(X).  % fail
```

テスト位置案：
- `tests/` に新規ファイル（例：`tests/test_dynamic_directive_guardrails.py`）
- 既存の runtime/logic_interpreter テストがあれば同ファイルに追記

---

## 4. リスクと回避策

| リスク | 内容 | 回避策 |
| --- | --- | --- |
| Parser の directive 分岐が rule を壊す | `:-` の先読みで通常ルール解析が破壊される | 既存 rule parsing の回帰テストを追加 |
| registry と rule index の不整合 | rule の追加/削除と registry 更新がズレる | add_rule 内で registry 更新を一元化 |
| retract の幽霊節 | index が消えても rules が残る/その逆 | `_remove_from_index` と `remove_rule` の一致テスト |
| query/consult の挙動変化 | parse 返却構造変更により既存 API が壊れる | API 入出力の回帰テスト |

