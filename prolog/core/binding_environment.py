from prolog.core.types import Variable


class BindingEnvironment:
    """変数バインディングを管理する環境

    Union-Findアルゴリズムを使用して、変数同士の統合と効率的な検索を提供します。
    バックトラックのためのチェックポイント機能も含まれています。
    """

    def __init__(self):
        # 変数から代表允E��数へのマッピング
        self.parent = {}
        # 変数から具体的な値へのマッピング
        self.value = {}
        # バックトラチE��用のトレイル�E�変更された変数のスタチE���E�E
        self.trail = []
        # トレイルのチェチE��ポイント（バチE��トラチE��位置�E�E
        self.trail_marks = []
        # スコープID用のカウンター
        self._next_scope_id = 0

    def get_next_scope_id(self):
        """一意�EスコープIDを生成して返す"""
        scope_id = self._next_scope_id
        self._next_scope_id += 1
        return scope_id

    def find(self, var):
        """変数の代表允E��検索する�E�パス圧縮アルゴリズム�E�E

        Args:
            var: 検索する変数

        Returns:
            変数の代表允E���E身が代表允E�E場合�E自身�E�E
        """
        if not isinstance(var, Variable):
            return var

        # 未登録の変数は自身が代表允E
        if var not in self.parent:
            self.parent[var] = var
            return var

        # パス圧縮�E�検索中に通過したノ�Eド�E親を直接ルートに設宁E
        if self.parent[var] != var:
            self.parent[var] = self.find(self.parent[var])
        return self.parent[var]

    def unify(self, var1, var2):
        """二つの変数を単一化すめE

        Args:
            var1: 単一化する変数1
            var2: 単一化する変数2

        Returns:
            bool: 単一化に成功したかどぁE��
        """
        # 変数以外�Eオブジェクト�E場合�E直接比輁E
        if not isinstance(var1, Variable) and not isinstance(var2, Variable):
            return var1 == var2

        # 代表允E��見つける
        root1 = self.find(var1)
        root2 = self.find(var2)

        # すでに同じ代表允E��ら�E劁E
        if root1 == root2:
            return True

        # 両方が変数の場合�E統吁E
        if isinstance(root1, Variable) and isinstance(root2, Variable):
            self._record_trail(root1)  # バックトラチE��用に記録
            self.parent[root1] = root2
            return True

        # 一方が変数、一方が値の場吁E
        if isinstance(root1, Variable):
            self._record_trail(root1)  # バックトラチE��用に記録
            self.value[root1] = root2
            return True

        if isinstance(root2, Variable):
            self._record_trail(root2)  # バックトラチE��用に記録
            self.value[root2] = root1
            return True

        # 両方が値の場合�E等しぁE��どぁE��で判宁E
        return root1 == root2

    def get_value(self, var):
        """変数の値を取得すめE

        Args:
            var: 値を取得する変数

        Returns:
            変数の値�E�バインチE��ングがなければ変数自身�E�E
        """
        if not isinstance(var, Variable):
            return var

        root = self.find(var)
        return self.value.get(root, root)

    def _record_trail(self, var):
        """バックトラチE��用に変数をトレイルに記録する

        Args:
            var: 記録する変数
        """
        self.trail.append(var)

    def mark_trail(self):
        """現在のトレイル位置を�Eークする�E�バチE��トラチE��用�E�E

        Returns:
            int: チェチE��ポイント�E位置
        """
        mark = len(self.trail)
        self.trail_marks.append(mark)
        return mark

    def backtrack_to_mark(self):
        """最後�Eマ�EクまでバックトラチE��する

        Returns:
            bool: バックトラチE��が可能だったかどぁE��
        """
        if not self.trail_marks:
            return False

        mark = self.trail_marks.pop()
        return self.backtrack(mark)

    def backtrack(self, position):
        """持E��位置までバックトラチE��する

        Args:
            position: バックトラチE��先�E位置

        Returns:
            bool: バックトラチE��が可能だったかどぁE��
        """
        if position < 0 or position > len(self.trail):
            return False

        # トレイルの末尾から処琁E
        while len(self.trail) > position:
            var = self.trail.pop()
            if var in self.value:
                del self.value[var]
            if var in self.parent:
                self.parent[var] = var  # 自身を親に戻ぁE

        return True

    def copy(self):
        """バインチE��ング環墁E�Eコピ�Eを作�Eする

        Returns:
            BindingEnvironment: コピ�Eされた環墁E
        """
        new_env = BindingEnvironment()
        new_env.parent = self.parent.copy()
        new_env.value = self.value.copy()
        # トレイルはコピ�EしなぁE��新しい履歴から始める！E
        return new_env

    def __str__(self):
        bindings = {}
        for var in self.parent:
            value = self.get_value(var)
            if value != var:  # 自身以外にバインドされてぁE��場合�Eみ
                bindings[str(var)] = str(value)
        return str(bindings)
