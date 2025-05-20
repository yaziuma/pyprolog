from prolog.logger import logger

class Variable:
    def __init__(self, name):
        # logger.debug(f"Variable initialized: {name}") # Can be very verbose
        self.name = name

    def match(self, other):
        logger.debug(f"Variable.match({self}) called with other: {other}")
        bindings = dict()
        if self != other:
            bindings[self] = other
            
            # 両変数の場合は双方向に束縛を追加
            if isinstance(other, Variable):
                bindings[other] = self
                
        logger.debug(f"Variable.match returning: {bindings}")
        return bindings

    def substitute(self, bindings, visited=None):
        """
        バインディングに従って変数を置換する。
        循環参照を検出して無限再帰を防ぐ。
        
        Args:
            bindings: 変数の置換マップ
            visited: 既に訪問した変数の集合（循環検出用）
        
        Returns:
            置換された値、または自分自身
        """
        logger.debug(f"Variable.substitute({self}) called with bindings: {bindings}")
        
        # 防御的チェック
        if bindings is None:
            logger.warning(f"Variable.substitute: bindings is None for {self}")
            return self
        
        # 循環検出用の初期化
        if visited is None:
            visited = set()
        
        # 循環検出: この変数が既に訪問済みなら、それ以上置換せず自身を返す
        if self in visited:
            logger.debug(f"Variable.substitute: Circular reference detected for {self}, returning self")
            return self
            
        # 変数を訪問済みとしてマーク
        visited.add(self)
        
        # バインディングがあれば置換を試みる
        value = bindings.get(self, None)
        if value is not None:
            # 自己参照の場合は自身を返す
            if value == self:
                logger.debug(f"Variable.substitute: Self-reference detected for {self}, returning self")
                return self
                
            # 値が変数の場合、再帰的に置換する（循環検出付き）
            if isinstance(value, Variable):
                result = value.substitute(bindings, visited)
                logger.debug(f"Variable.substitute returning (from recursive value): {result}")
                return result
            else:
                # 値が変数でない場合、その値自体に置換メソッドがあれば呼び出す
                if hasattr(value, 'substitute'):
                    result = value.substitute(bindings)
                    logger.debug(f"Variable.substitute returning (from value.substitute): {result}")
                    return result
                else:
                    logger.debug(f"Variable.substitute returning (from value directly): {value}")
                    return value
        
        # バインディングがない場合は自身を返す
        logger.debug(f"Variable.substitute returning (self): {self}")
        return self

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name
        return False
