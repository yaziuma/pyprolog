from prolog.core.types import Term, Variable, TRUE_TERM


class Number(Term):
    """数値を表すTerm"""
    def __init__(self, value):
        super().__init__(value)  # pred に数値を格納
        self.value = value
    
    def match(self, other, bindings=None):
        if bindings is None:
            bindings = {}
        
        if isinstance(other, Variable):
            return other.match(self, bindings)
        
        if isinstance(other, Number):
            return bindings if self.value == other.value else None
        
        return None
    
    def substitute(self, bindings):
        return self
    
    def __str__(self):
        return str(self.value)
    
    # 算術演算メソッド
    def add(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value)
        raise TypeError(f"Cannot add Number and {type(other)}")
    
    def substract(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value)
        raise TypeError(f"Cannot subtract Number and {type(other)}")
    
    def multiply(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value)
        raise TypeError(f"Cannot multiply Number and {type(other)}")
    
    def divide(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                raise ZeroDivisionError("Division by zero")
            return Number(self.value / other.value)
        raise TypeError(f"Cannot divide Number and {type(other)}")
    
    # 比較演算メソッド
    def equal(self, other):
        if isinstance(other, Number):
            return self.value == other.value
        return False
    
    def not_equal(self, other):
        return not self.equal(other)
    
    def less(self, other):
        if isinstance(other, Number):
            return self.value < other.value
        raise TypeError(f"Cannot compare Number and {type(other)}")
    
    def equal_less(self, other):
        if isinstance(other, Number):
            return self.value <= other.value
        raise TypeError(f"Cannot compare Number and {type(other)}")
    
    def greater(self, other):
        if isinstance(other, Number):
            return self.value > other.value
        raise TypeError(f"Cannot compare Number and {type(other)}")
    
    def greater_equal(self, other):
        if isinstance(other, Number):
            return self.value >= other.value
        raise TypeError(f"Cannot compare Number and {type(other)}")


class Arithmetic(Variable):
    """算術式を含む変数"""
    def __init__(self, name, expression):
        super().__init__(name)
        self.expression = expression
    
    def evaluate(self, interpreter):
        """MathInterpreterを使って式を評価"""
        return interpreter._evaluate_expr(self.expression)


class Logic(Term):
    """論理式を表すTerm"""
    def __init__(self, expression):
        super().__init__('logic', expression)
        self.expression = expression
    
    def evaluate(self, interpreter):
        """LogicInterpreterを使って式を評価"""
        return interpreter._evaluate_expr(self.expression)


class Dot(Term):
    """リスト構造 [H|T] の実装"""
    def __init__(self, head, tail):
        super().__init__('.', head, tail)
        self.head = head
        self.tail = tail
    
    @classmethod
    def from_list(cls, items):
        """Pythonリストから Dot 構造を作成"""
        if not items:
            return Term('[]')  # 空リスト
        
        result = Term('[]')
        for item in reversed(items):
            result = cls(item, result)
        return result
    
    def to_list(self):
        """Dot構造をPythonリストに変換"""
        result = []
        current = self
        while isinstance(current, Dot):
            result.append(current.head)
            current = current.tail
        if str(current) != '[]':
            # 非正規リスト [1,2|X] の場合
            result.append('|')
            result.append(current)
        return result
    
    def __str__(self):
        items = self.to_list()
        if items and items[-2:] == ['|', items[-1]]:
            # 非正規リスト
            return '[' + ', '.join(str(i) for i in items[:-2]) + '|' + str(items[-1]) + ']'
        else:
            # 正規リスト
            return '[' + ', '.join(str(i) for i in items) + ']'


class Bar(Term):
    """リストの明示的な tail 記法 [H|T]"""
    def __init__(self, head_list, tail):
        # head_list は Dot 構造、tail は Variable または Term
        super().__init__('|', head_list, tail)
        self.head_list = head_list
        self.tail = tail
    
    def __str__(self):
        # head_list を展開してリスト要素を取得
        if isinstance(self.head_list, Dot):
            items = self.head_list.to_list()
            if items and str(items[-1]) == '[]':
                items = items[:-1]  # 末尾の [] を除去
            return '[' + ', '.join(str(i) for i in items) + '|' + str(self.tail) + ']'
        else:
            return f'[{self.head_list}|{self.tail}]'


# 定数
TRUE = TRUE_TERM
FALSE = lambda: Term('false')  # FALSE は関数として定義されている可能性


# TermFunction の追加実装（runtime/interpreter.py で必要）
class TermFunction(Term):
    """Python関数を呼び出し可能なTerm"""
    def __init__(self, predicate_name, *args, python_callable=None):
        super().__init__(predicate_name, *args)
        self.python_callable = python_callable
        self._executed = False
    
    def _execute_func(self):
        """Python関数を実行してargs を更新"""
        if self.python_callable and not self._executed:
            # 引数を Python オブジェクトに変換
            py_args = []
            for arg in self.args:
                if isinstance(arg, Number):
                    py_args.append(arg.value)
                elif isinstance(arg, Term) and str(arg.pred) in ['true', 'false']:
                    py_args.append(str(arg.pred) == 'true')
                else:
                    py_args.append(str(arg))
            
            # 関数を実行
            result = self.python_callable(*py_args)
            
            # 結果を Prolog の Term に変換
            if isinstance(result, bool):
                self.args = [Term('true') if result else Term('false')]
            elif isinstance(result, (int, float)):
                self.args = [Number(result)]
            else:
                self.args = [Term(str(result))]
            
            self._executed = True
    
    def match(self, other, bindings=None):
        # 実行前に関数を呼び出す
        self._execute_func()
        return super().match(other, bindings)