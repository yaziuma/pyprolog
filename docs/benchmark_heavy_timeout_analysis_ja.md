# heavy ベンチマーク 3 件のタイムアウト要因考察（日本語）

## 対象
以下 3 テスト（ユーザー報告では `timeout 180`）:

- `tests/benchmark/test_benchmarks.py::test_nrev_heavy`
- `tests/benchmark/test_benchmarks.py::test_primes_heavy`
- `tests/benchmark/test_benchmarks.py::test_recursion_depth_heavy`

いずれも `_run_benchmark(...)` で `assert len(result) >= 1` を満たす必要がある構造。失敗時は「解が 0 件」の扱いになります。  
(テスト定義と共通実行ロジックは同一) 。

## 先に結論（要点）
1. **根本原因は 3 件ともほぼ共通で、`_execute_body_direct` 側の再帰深度問題が残っていること**です。  
   現在の実装は conjunction を iterative 化していますが、`_execute_body_direct` 自体は「HYBRID（再帰を残す）」で、`_execute_single_goal` との往復で深い再帰パスが残ります。
2. その結果、負荷が上がる入力サイズ（`nrev(300)`, `primes(10000)`, `benchmark(1000)`）で **RecursionError が内部で発生**し、テストからは `result == []`（= `len(result)==0`）として見えるケースが起きます。
3. ユーザー環境で `timeout 180` と表示されたのは、
   - 実行中に標準出力に進捗が出ず待ち続ける
   - もしくは低速環境で計算が長引いたあと失敗する
   などにより、タイムアウトラッパー側で打ち切られた可能性が高いです。

---

## 事実ベース（コード上の観測）

### 1) heavy テストの入力サイズが大きい
- `nrev_heavy` は `benchmark(300).` を実行します。  
- `primes_heavy` は `benchmark(10000).` を実行します。  
- `recursion_depth_heavy` は iterative runtime で `benchmark(1000).` を実行します。  

### 2) 3 テストは共通で `_run_benchmark` を通る
`_run_benchmark` は query 実行結果を `result = benchmark(lambda: run_query(...))` で受け、`assert len(result) >= 1` を要求します。  
つまり内部例外や探索失敗で解が返らないと、最終的に同じ失敗形になります。

### 3) 実行エンジン側は「部分 iterative」
`logic_interpreter.py` の `_execute_body_direct` は docstring 上も「HYBRID」で、
- conjunction flatten + iterative 実行は導入済み
- ただし body 実行自体は再帰経路が残る
という設計です。  
実際、`_execute_conjunction_iterative` から再び `_execute_body_direct` を呼び、そこから `_execute_single_goal` へ降りるため、深い再帰パスが発生し得ます。

---

## テスト別の考察

## A. `test_nrev_heavy`（`benchmark(300)`）
- `nrev/2` は `append/3` を伴うナイーブ反転で、計算量が大きく（実質 O(n^2)）、かつ再帰のネストも深くなります。
- 実測でも `benchmark(300)` で RecursionError が発生し、解が返らない挙動を確認しました。
- そのため、環境によっては「RecursionError で即失敗」または「遅延後タイムアウト」のどちらにも見えます。

## B. `test_primes_heavy`（`benchmark(10000)`）
- `sieve/filter/range` が深い再帰連鎖を作り、`Limit=10000` は再帰回数・探索状態ともに重い設定です。
- 実測では中規模以上で RecursionError が発生し得るため、heavy は結果 0 件（assert 失敗）に到達しやすいです。
- こちらも環境次第で、失敗までに時間がかかる場合は `timeout 180` 側で先に落ちます。

## C. `test_recursion_depth_heavy`（iterative runtime + `benchmark(1000)`）
- テスト意図は「iterative 実行で深い再帰に耐える」ですが、現実装は `_execute_body_direct` が完全 iterative 化されていないため、`N=1000` で再帰経路が残ります。
- そのため heavy で解が返らず（0 件）、環境によってはタイムアウトに見える・あるいは即失敗になります。

---

## なぜ「タイムアウト」と「解0件失敗」が混在して見えるか

同じ根本問題（深い再帰 + 高負荷）でも、
- CPU 制限
- スレッドスケジューリング
- ログ出力バッファリング
- タイムアウトラッパーの閾値

で表面症状が変わるためです。  
早く RecursionError に到達する環境では `assert len(result) >= 1` 失敗、
到達前に 180 秒を超える環境では timeout として観測されます。

---

## 改善の方向性（提案）

1. **Phase 2 として `_execute_body_direct` の完全 iterative 化**を優先。  
   これが 3 件共通の本命対策です。
2. `nrev/primes` については、性能観点で heavy 入力値の妥当性見直し（CI/ローカル向けプロファイル分離）も有効。
3. ベンチの失敗理由を明確化するため、`_run_benchmark` に
   - 例外種別の明示ログ
   - 実行時間計測
   を追加すると、timeout と論理失敗の切り分けが容易になります。

---

## 参考（対象コード）
- heavy テスト定義と `_run_benchmark`。
- `nrev.pl` / `primes.pl` / `recursion_depth.pl` の負荷条件。
- `_execute_body_direct` と `_execute_conjunction_iterative` の実装（再帰経路が残る点）。
