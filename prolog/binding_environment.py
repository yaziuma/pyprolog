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
        # スコープID用のカウンター
        self._next_scope_id = 0
        
    def get_next_scope_id(self):
        """一意のスコープIDを生成して返す"""
        scope_id = self._next_scope_id
        self._next_scope_id += 1
        return scope_id

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
