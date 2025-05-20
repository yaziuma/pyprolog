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

    def substitute(self, bindings):
        logger.debug(f"Variable.substitute({self}) called with bindings: {bindings}")
        # Defensive Null check for bindings
        if bindings is None:
            logger.warning(f"Variable.substitute: bindings is None for {self}")
            return self
        
        value = bindings.get(self, None)
        if value is not None:
            # Prevent infinite recursion if a variable is bound to itself
            if value == self:
                logger.debug(f"Variable.substitute: Self-reference detected for {self}, returning self")
                return self
            
            # 変数チェーンを再帰的に解決
            result = value.substitute(bindings)
            logger.debug(f"Variable.substitute returning (from value): {result}")
            return result
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
