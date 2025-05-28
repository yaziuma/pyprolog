# PyPrologプロジェクト修正詳細設計書：専用バインディング環境アプローチ

## 1. 概要

### 1.1 目的
PyPrologプロジェクトにおける変数同士の単一化処理を根本的に改善するため、専用のバインディング環境システムを実装する。これにより、`match(X, Y) :- X = Y.` ルールのテストを通すだけでなく、Prologエンジン全体の堅牢性と拡張性を高める。

### 1.2 背景
テストケース `test_unification_in_rule_body` の失敗は、現在の実装が変数間の相互参照と統一的なバインディング管理に対応していないことを示している。一時的なハックではなく、Prologの標準的な実装に近い方式での解決が求められる。

### 1.3 現状の問題点
- 変数バインディングがオブジェクト間で断片的に管理されている
- 変数同士の統合（単一化）に体系的な処理が欠けている
- 単一化の結果がクエリ全体で一貫して伝播されない
- バックトラック時の状態管理機能が不十分

## 2. 修正設計：専用バインディング環境アプローチ

### 2.1 修正アプローチの概要
専用の `BindingEnvironment` クラスを導入し、すべての変数バインディングをこのクラスで一元管理する。Union-Find（素集合データ構造）アルゴリズムを活用し、効率的な変数の統合と検索を実現する。

### 2.2 対象ファイル
- **新規作成:** `prolog/binding_environment.py`
- **主要修正:** `prolog/interpreter.py`
- **インターフェース変更:** `prolog/types.py`, `prolog/merge_bindings.py`

## 3. 詳細な修正内容

### 3.1 新規ファイル: `binding_environment.py`

```python
from prolog.core_types import Variable
from prolog.logger import logger

class BindingEnvironment:
    """変数バインディングを一元管理する環境

    Union-Findアルゴリズムを使用して、変数同士の統合と効率的な検索を提供します。
    バックトラックのためのチェックポイント機能も含まれています。
    """
    
    def __init__(self):
        # 変数から代表元変数へのマッピング
        self.parent = {}
        # 変数から具体的な値へのマッピング
        self.value = {}
        # バックトラック用のトレイル（変更された変数のスタック）
        self.trail = []
        # トレイルのチェックポイント（バックトラック位置）
        self.trail_marks = []
        
    def find(self, var):
        """変数の代表元を検索する（パス圧縮アルゴリズム）

        Args:
            var: 検索する変数

        Returns:
            変数の代表元（自身が代表元の場合は自身）
        """
        if not isinstance(var, Variable):
            return var
            
        # 未登録の変数は自身が代表元
        if var not in self.parent:
            self.parent[var] = var
            return var
            
        # パス圧縮：検索中に通過したノードの親を直接ルートに設定
        if self.parent[var] != var:
            self.parent[var] = self.find(self.parent[var])
        return self.parent[var]
        
    def unify(self, var1, var2):
        """二つの変数を単一化する

        Args:
            var1: 単一化する変数1
            var2: 単一化する変数2

        Returns:
            bool: 単一化に成功したかどうか
        """
        # 変数以外のオブジェクトの場合は直接比較
        if not isinstance(var1, Variable) and not isinstance(var2, Variable):
            return var1 == var2
            
        # 代表元を見つける
        root1 = self.find(var1)
        root2 = self.find(var2)
        
        # すでに同じ代表元なら成功
        if root1 == root2:
            return True
            
        # 両方が変数の場合は統合
        if isinstance(root1, Variable) and isinstance(root2, Variable):
            self._record_trail(root1)  # バックトラック用に記録
            self.parent[root1] = root2
            return True
            
        # 一方が変数、一方が値の場合
        if isinstance(root1, Variable):
            self._record_trail(root1)  # バックトラック用に記録
            self.value[root1] = root2
            return True
            
        if isinstance(root2, Variable):
            self._record_trail(root2)  # バックトラック用に記録
            self.value[root2] = root1
            return True
            
        # 両方が値の場合は等しいかどうかで判定
        return root1 == root2
        
    def get_value(self, var):
        """変数の値を取得する

        Args:
            var: 値を取得する変数

        Returns:
            変数の値（バインディングがなければ変数自身）
        """
        if not isinstance(var, Variable):
            return var
            
        root = self.find(var)
        return self.value.get(root, root)
        
    def _record_trail(self, var):
        """バックトラック用に変数をトレイルに記録する

        Args:
            var: 記録する変数
        """
        self.trail.append(var)
        
    def mark_trail(self):
        """現在のトレイル位置をマークする（バックトラック用）

        Returns:
            int: チェックポイントの位置
        """
        mark = len(self.trail)
        self.trail_marks.append(mark)
        return mark
        
    def backtrack_to_mark(self):
        """最後のマークまでバックトラックする
        
        Returns:
            bool: バックトラックが可能だったかどうか
        """
        if not self.trail_marks:
            return False
            
        mark = self.trail_marks.pop()
        return self.backtrack(mark)
        
    def backtrack(self, position):
        """指定位置までバックトラックする

        Args:
            position: バックトラック先の位置

        Returns:
            bool: バックトラックが可能だったかどうか
        """
        if position < 0 or position > len(self.trail):
            return False
            
        # トレイルの末尾から処理
        while len(self.trail) > position:
            var = self.trail.pop()
            if var in self.value:
                del self.value[var]
            if var in self.parent:
                self.parent[var] = var  # 自身を親に戻す
                
        return True
        
    def copy(self):
        """バインディング環境のコピーを作成する

        Returns:
            BindingEnvironment: コピーされた環境
        """
        new_env = BindingEnvironment()
        new_env.parent = self.parent.copy()
        new_env.value = self.value.copy()
        # トレイルはコピーしない（新しい履歴から始める）
        return new_env
        
    def __str__(self):
        bindings = {}
        for var in self.parent:
            value = self.get_value(var)
            if value != var:  # 自身以外にバインドされている場合のみ
                bindings[str(var)] = str(value)
        return str(bindings)
```

### 3.2 `interpreter.py` の修正

#### 3.2.1 `Runtime` クラスの修正

```python
class Runtime:
    def __init__(self, rules):
        # logger.debug(f"Runtime initialized with rules (count: {len(rules)}): {rules[:3]}{'...' if len(rules) > 3 else ''}")
        self.rules = rules
        self.stream = io.StringIO()
        self.stream_pos = 0
        self.binding_env = BindingEnvironment()  # 新しいバインディング環境を追加
```

#### 3.2.2 `query` メソッドの修正

```python
def query(self, query_str):
    from prolog.scanner import Scanner
    from prolog.parser import Parser
    # logger.debug(f"Runtime.query called with: '{query_str}'") # Entry point for query
    
    # 新しいクエリごとにバインディング環境をリセット
    self.binding_env = BindingEnvironment()
    
    tokens = Scanner(query_str).tokenize()
    # logger.debug(f"Runtime.query: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")

    if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
        # logger.debug("Runtime.query: no relevant tokens, returning (no solutions).")
        return

    parsed_query = Parser(tokens).parse_query()
    # logger.debug(f"Runtime.query: parsed_query: {parsed_query}, type: {type(parsed_query)}")

    query_vars = []
    
    def find_variables(term, found_vars_list): # Pass list to append to
        if isinstance(term, Variable):
            if term.name != '_' and term not in found_vars_list:
                 found_vars_list.append(term)
        elif isinstance(term, Term): 
            for arg_item in term.args: # Renamed arg to arg_item to avoid conflict
                find_variables(arg_item, found_vars_list)
        elif isinstance(term, Rule): 
            if hasattr(term, 'head') and term.head is not None:
                find_variables(term.head, found_vars_list)
            if hasattr(term, 'body') and term.body is not None:
                find_variables(term.body, found_vars_list)
    
    temp_query_vars = []
    find_variables(parsed_query, temp_query_vars)
    query_vars = temp_query_vars # Assign after full traversal

    # logger.debug(f"Runtime.query: Found variables in query: {[var.name for var in query_vars if var is not None]}")
    
    solution_count = 0
    for solution_item in self.execute(parsed_query): 
        # logger.debug(f"Runtime.query: solution_item from execute: {solution_item}, type: {type(solution_item)}") # Key log for query results
        
        if isinstance(solution_item, FALSE) or solution_item is None:
            # logger.debug("Runtime.query: solution_item is FALSE or None, skipping.")
            continue
        if isinstance(solution_item, CUT):
            logger.warning("Runtime.query: CUT signal reached top-level query. This should ideally be handled internally.") # Keep warning
            break

        # 結果から変数バインディングを抽出
        current_bindings = {}
        if query_vars:
            for var in query_vars:
                value = self.binding_env.get_value(var)
                if value != var:  # バインディングがある場合
                    current_bindings[var] = value
            
            if current_bindings or not query_vars: 
                solution_count += 1
                yield current_bindings
        elif isinstance(solution_item, TRUE): 
            # Ground query (no variables) success
            solution_count += 1
            yield {} 
    
    logger.info(f"Runtime.query for '{query_str}' finished. Total solutions yielded: {solution_count}") # Keep info for summary
```

#### 3.2.3 `execute` メソッドの修正

```python
def execute(self, query_obj):
    # logger.debug(f"Runtime.execute called with query_obj: {query_obj}") # Entry point for execute

    if isinstance(query_obj, TRUE):
        # logger.debug("Runtime.execute: query_obj is TRUE, yielding TRUE")
        yield TRUE()
        return
    
    if isinstance(query_obj, Fail): 
        # logger.debug("Runtime.execute: query_obj is Fail, yielding nothing (failure)")
        return  
        
    if isinstance(query_obj, Rule):
        # ルールを評価
        # バックトラック用にマークを設定
        mark = self.binding_env.mark_trail()
        
        for body_result in query_obj.body.query(self): 
            if isinstance(body_result, FALSE):
                continue
            if isinstance(body_result, CUT): 
                yield CUT()
                return
                
            # ルールのヘッドを現在の環境で評価して返す
            yield query_obj.head
            
            # バックトラックのためバインディングを元に戻す
            self.binding_env.backtrack(mark)
            
    elif isinstance(query_obj, Term):
        if query_obj.pred == '=':
            # '=' 演算子の特別処理
            if len(query_obj.args) == 2:
                lhs, rhs = query_obj.args
                if self.binding_env.unify(lhs, rhs):
                    yield TRUE()
                return
                
        # 通常の述語呼び出し
        for rule in self.rules:
            if rule.head.pred == query_obj.pred and len(rule.head.args) == len(query_obj.args):
                # ヘッドとクエリの引数の単一化を試みる
                
                # バックトラック用にマークを設定
                mark = self.binding_env.mark_trail()
                
                # ヘッドの引数をクエリの引数と単一化
                unification_success = True
                for rule_arg, query_arg in zip(rule.head.args, query_obj.args):
                    if not self.binding_env.unify(rule_arg, query_arg):
                        unification_success = False
                        break
                
                if unification_success:
                    # ボディを評価
                    for body_result in self.execute(rule.body):
                        if isinstance(body_result, FALSE):
                            continue
                        if isinstance(body_result, CUT):
                            yield CUT()
                            # CUTが見つかった場合は現在のマークまで戻る（それ以降はバックトラックしない）
                            break
                            
                        # 成功を通知
                        yield TRUE()
                
                # バックトラックのためバインディングを元に戻す（CUTの場合を除く）
                if not isinstance(body_result, CUT):
                    self.binding_env.backtrack(mark)
                    
    elif isinstance(query_obj, Conjunction):
        # 結合ゴールの処理
        self._execute_conjunction(query_obj)
        
    # logger.debug(f"Runtime.execute for query_obj: {query_obj} finished.")

def _execute_conjunction(self, conjunction):
    """結合ゴールを実行する
    
    Args:
        conjunction: 実行する結合ゴール
    
    Yields:
        結合ゴールの評価結果
    """
    def execute_goals(index):
        if index >= len(conjunction.args):
            yield TRUE()
            return
            
        goal = conjunction.args[index]
        
        # バックトラック用にマークを設定
        mark = self.binding_env.mark_trail()
        
        # カット演算子の特別処理
        if isinstance(goal, CUT):
            yield from execute_goals(index + 1)
            yield CUT()
            return
            
        for result in self.execute(goal):
            if isinstance(result, FALSE):
                continue
                
            if isinstance(result, CUT):
                yield from execute_goals(index + 1)
                yield CUT()
                return
                
            # 次のゴールを評価
            yield from execute_goals(index + 1)
                
            # バックトラックのためバインディングを元に戻す
            self.binding_env.backtrack(mark)
            
    yield from execute_goals(0)
```

### 3.3 `types.py` の修正

#### 3.3.1 `Term` クラスの `substitute` メソッド修正

```python
def substitute(self, binding_env_or_dict):
    """現在のバインディング環境またはバインディング辞書に基づいて項を置換する
    
    Args:
        binding_env_or_dict: BindingEnvironmentインスタンスまたはバインディング辞書
        
    Returns:
        置換後のTerm
    """
    # 後方互換性のため両方のタイプをサポート
    if hasattr(binding_env_or_dict, 'get_value'):
        # BindingEnvironmentインスタンス
        binding_env = binding_env_or_dict
        substituted_args = []
        for arg in self.args:
            if hasattr(arg, 'substitute'):
                substituted_args.append(arg.substitute(binding_env))
            else:
                substituted_args.append(binding_env.get_value(arg))
        return Term(self.pred, *substituted_args)
    else:
        # 辞書タイプ（従来の実装との互換性）
        bindings = binding_env_or_dict
        substituted_args = [arg.substitute(bindings) for arg in self.args]
        return Term(self.pred, *substituted_args)
```

#### 3.3.2 `Variable` クラスの `substitute` メソッド修正

```python
def substitute(self, binding_env_or_dict, visited=None):
    """バインディング環境または辞書に基づいて変数を置換する
    
    Args:
        binding_env_or_dict: BindingEnvironmentインスタンスまたはバインディング辞書
        visited: 訪問済み変数の集合（循環検出用、辞書モードのみ）
        
    Returns:
        置換後の値または自分自身
    """
    # 後方互換性のため両方のタイプをサポート
    if hasattr(binding_env_or_dict, 'get_value'):
        # BindingEnvironmentインスタンス
        binding_env = binding_env_or_dict
        value = binding_env.get_value(self)
        if value == self:
            return self
        if hasattr(value, 'substitute'):
            return value.substitute(binding_env)
        return value
    else:
        # 辞書タイプ（従来の実装との互換性）
        # 既存のコードは変更なし
        bindings = binding_env_or_dict
        if bindings is None:
            return self
        
        if visited is None:
            visited = set()
            
        if self in visited:
            return self
            
        visited.add(self)
        
        value = bindings.get(self, None)
        if value is not None:
            if value == self:
                return self
                
            if isinstance(value, Variable):
                result = value.substitute(bindings, visited)
                return result
            else:
                if hasattr(value, 'substitute'):
                    result = value.substitute(bindings)
                    return result
                else:
                    return value
        
        return self
```

## 4. 実装における重要なポイント

### 4.1 Union-Findアルゴリズム
- 変数の同値関係を効率的に管理するための素集合データ構造
- パス圧縮により、検索操作（find）の償却計算量がほぼO(1)になる
- 変数同士の参照関係をグラフとして扱い、統合操作で効率的に管理

### 4.2 バックトラック機能
- トレイルで変更された変数を記録し、必要に応じて元の状態に戻せるようにする
- マーキングシステムで複数階層のバックトラックを可能にする
- カット演算子（!）との連携で、バックトラックの範囲を制御

### 4.3 変数バインディングのスコープ
- バインディングは単一のクエリ実行中でのみ有効
- 新しいクエリごとにバインディング環境をリセットする
- 変数のバインディングはクエリの全体で一貫して維持される

## 5. 修正による影響範囲

### 5.1 正の影響
- 変数同士の単一化が正しく機能するようになる
- 堅牢なバインディング管理により、複雑なクエリも正確に処理可能になる
- バックトラック機能の改善により、複雑な検索空間の探索が可能に
- より標準的なPrologの実装に近づく
- 将来的な拡張性が高まる

### 5.2 潜在的な課題
- 既存コードとの互換性維持が必要（substitute メソッド等）
- パフォーマンス最適化の余地がある（特にUnion-Findのランク最適化）
- メモリ使用量が増加する可能性がある

## 6. 移行戦略

### 6.1 段階的導入
1. `BindingEnvironment` クラスを実装する
2. `Runtime` クラスにバインディング環境を統合する
3. 単一のテストケース（`test_unification_in_rule_body`）で検証する
4. `substitute` メソッドに後方互換性を追加する
5. 残りの処理を新しいバインディング環境に移行する
6. すべてのテストが通ることを確認する

### 6.2 既存コードとの並存
- 一時的に両方のバインディング方式をサポートする
- 段階的にコード全体を移行する
- 移行完了後、古いメカニズムを廃止する

## 7. テスト計画

### 7.1 ユニットテスト
- `BindingEnvironment` クラスの基本機能のテスト
- 変数同士の単一化や複雑なバインディングパターンのテスト
- バックトラック機能とカット演算子の連携テスト

### 7.2 回帰テスト
- 既存のテストケースが引き続き通ることを確認
- 特に `test_unification_in_rule_body` テストに注目

### 7.3 性能テスト
- 大規模なクエリでのパフォーマンス測定
- メモリ使用量の監視

## 8. 実装計画

### 8.1 優先順位
1. `BindingEnvironment` クラスの実装
2. `Runtime` クラスの修正
3. `types.py` の修正
4. テスト実行と調整

### 8.2 タイムライン
- 基本実装：2日
- 既存コードとの統合：2日
- テストと調整：1日
- ドキュメント作成：1日
- 合計：6日間

## 9. まとめ

専用バインディング環境の導入は、単に特定のテストケースを通すためのハックではなく、Prologエンジン全体の品質と拡張性を高めるための戦略的な修正です。Union-Findアルゴリズムを用いた効率的な変数管理と、適切なバックトラック機能の実装により、標準的なPrologの実装に近い挙動を実現します。

この修正は単なるバグ修正を超え、プロジェクト全体のアーキテクチャを改善するリファクタリングです。変数同士の単一化問題を解決すると同時に、将来的な機能拡張への道を開きます。