# prolog/core/types.py
from prolog.util.logger import logger


class Variable:
    def __init__(self, name):
        self.name = name
        self.bindings = None

    def match(self, other, bindings=None):
        if bindings is None:
            bindings = {}

        if self == other:
            return bindings

        if self.name == "_":
            return bindings
        if isinstance(other, Variable) and other.name == "_":
            return bindings

        if self in bindings:
            bound_value = bindings[self]
            if hasattr(bound_value, "match"):
                return bound_value.match(other, bindings)
            return bindings if bound_value == other else None

        if isinstance(other, Variable) and other in bindings:
            bound_value_other = bindings[other]
            return self.match(bound_value_other, bindings)

        new_bindings = bindings.copy()
        new_bindings[self] = other
        return new_bindings

    def substitute(self, bindings):
        if self in bindings:
            value = bindings[self]
            if value == self:
                return self
            if hasattr(value, "substitute"):
                return value.substitute(bindings)
            return value
        return self

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return NotImplemented
        return self.name == other.name


class Term:
    def __init__(self, pred, *args):
        self.pred = pred
        self.args = list(args)

    def match(self, other, bindings=None):
        if bindings is None:
            bindings = {}

        if isinstance(other, Variable):
            return other.match(self, bindings)

        if isinstance(other, Term):
            if self.pred != other.pred or len(self.args) != len(other.args):
                return None

            current_bindings = bindings.copy()
            for arg1, arg2 in zip(self.args, other.args):
                if hasattr(arg1, "match"):
                    match_result = arg1.match(arg2, current_bindings)
                    if match_result is None:
                        return None
                    current_bindings.update(match_result)
                elif arg1 != arg2:
                    return None
            return current_bindings

        return None

    def substitute(self, bindings):
        substituted_args = []
        for arg in self.args:
            if hasattr(arg, "substitute"):
                substituted_args.append(arg.substitute(bindings))
            else:
                substituted_args.append(arg)
        return Term(self.pred, *substituted_args)

    def __str__(self):
        if not self.args:
            return str(self.pred)
        args_str = ", ".join(map(str, self.args))
        return f"{self.pred}({args_str})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        try:
            return hash((self.pred, tuple(self.args)))
        except TypeError:
            logger.warning(f"Term '{self}' is not hashable due to its arguments.")
            raise TypeError(f"Unhashable type in Term arguments: {self.args}")

    def __eq__(self, other):
        if not isinstance(other, Term):
            return NotImplemented
        return self.pred == other.pred and self.args == other.args


class Rule:
    def __init__(self, head, body):
        self.head = head
        self.body = body

    def __str__(self):
        if hasattr(self.body, "pred") and self.body.pred == "true":
            return f"{self.head}."
        return f"{self.head} :- {self.body}."

    def __repr__(self):
        return str(self)

    def substitute(self, bindings):
        new_head = (
            self.head.substitute(bindings)
            if hasattr(self.head, "substitute")
            else self.head
        )
        new_body = (
            self.body.substitute(bindings)
            if hasattr(self.body, "substitute")
            else self.body
        )
        return Rule(new_head, new_body)


class Conjunction(Term):
    def __init__(self, goals):
        super().__init__(",", *goals)

    def substitute(self, bindings):
        substituted_goals = [
            g.substitute(bindings) if hasattr(g, "substitute") else g for g in self.args
        ]
        return Conjunction(substituted_goals)

    def __str__(self):
        return "(" + ", ".join(map(str, self.args)) + ")"


# Token互換属性を持つミックスイン
class TokenCompatible:
    """Tokenクラスとの互換性を提供するミックスイン"""

    def __init__(self, lexeme_value):
        self.lexeme = lexeme_value
        self.literal = None
        self.token_type = None
        self.line = -1


# シングルトンクラスの修正版
class _SingletonTerm(Term):
    _instances = {}  # クラスごとのインスタンスを保存

    def __new__(cls, pred_name):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonTerm, cls).__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]

    def __init__(self, pred_name):
        if not getattr(self, "_initialized", False):
            super().__init__(pred_name)
            self._initialized = True

    def substitute(self, bindings):
        return self


class TRUEClass(_SingletonTerm, TokenCompatible):
    def __new__(cls):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonTerm, cls).__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]

    def __init__(self):
        if not getattr(self, "_initialized", False):
            super(_SingletonTerm, self).__init__("true")
            TokenCompatible.__init__(self, "true")
            self._initialized = True


class FALSEClass(_SingletonTerm, TokenCompatible):
    def __new__(cls):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonTerm, cls).__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]

    def __init__(self):
        if not getattr(self, "_initialized", False):
            super(_SingletonTerm, self).__init__("false")
            TokenCompatible.__init__(self, "false")
            self._initialized = True


class CUTClass(_SingletonTerm, TokenCompatible):
    def __new__(cls):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonTerm, cls).__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]

    def __init__(self):
        if not getattr(self, "_initialized", False):
            super(_SingletonTerm, self).__init__("!")
            TokenCompatible.__init__(self, "!")
            self._initialized = True


class Fail(Term, TokenCompatible):
    def __init__(self):
        super().__init__("fail")
        TokenCompatible.__init__(self, "fail")


class Cut(Term, TokenCompatible):
    def __init__(self):
        super().__init__("!")
        TokenCompatible.__init__(self, "!")


# シングルトンインスタンスを作成
TRUE_TERM = TRUEClass()
FALSE_TERM = FALSEClass()
CUT_SIGNAL = CUTClass()
FAIL_TERM = Fail()

# List-related constants and helpers
EMPTY_LIST_ATOM = Term("[]")

def is_list(term):
    """Checks if a term is a Prolog list (either empty or a dot pair)."""
    return is_empty_list(term) or (isinstance(term, Term) and term.pred == '.' and len(term.args) == 2)

def is_empty_list(term):
    """Checks if a term is the empty list atom '[]'."""
    return isinstance(term, Term) and term.pred == '[]' and not term.args

def get_list_head(term):
    """Gets the head of a list. Assumes term is a non-empty list."""
    if not is_list(term) or is_empty_list(term):
        raise TypeError("Term is not a non-empty list.")
    return term.args[0]

def get_list_tail(term):
    """Gets the tail of a list. Assumes term is a non-empty list."""
    if not is_list(term) or is_empty_list(term):
        raise TypeError("Term is not a non-empty list.")
    return term.args[1]

# 後方互換性のための関数形式（廃止予定）
def TRUE():
    return TRUE_TERM


def FALSE():
    return FALSE_TERM
