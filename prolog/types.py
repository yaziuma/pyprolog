from functools import reduce
from .math_interpreter import MathInterpreter
from .logic_interpreter import LogicInterpreter
from .expression import Visitor, PrimaryExpression, BinaryExpression
from .merge_bindings import merge_bindings
from prolog.logger import logger

logger.debug("types.py loaded")

class Variable:
    def __init__(self, name):
        # logger.debug(f"Variable initialized: {name}") # Can be very verbose
        self.name = name

    def match(self, other):
        logger.debug(f"Variable.match({self}) called with other: {other}")
        bindings = dict()
        if self != other:
            bindings[self] = other
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
                logger.debug(f"Variable.substitute: {self} is bound to itself. Returning self.")
                return self
            result = value.substitute(bindings)
            logger.debug(f"Variable.substitute returning (from value): {result}")
            return result
        logger.debug(f"Variable.substitute returning (self): {self}")
        return self

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)

class Dot:
    def __init__(self, head, tail=None):
        # logger.debug(f"Dot initialized with head: {head}, tail: {tail}") # Can be very verbose
        self._name = '.'
        self.head = head
        self.tail = tail
        self._current_element = self

    @classmethod
    def from_list(cls, lst):
        logger.debug(f"Dot.from_list called with: {lst}")
        # 空リストの特殊ケース
        if not lst:
            # 空リストは Term("[]") を head に持ち、tail は None
            empty_term = Term("[]")
            result = cls(empty_term, None)
            logger.debug(f"Dot.from_list returning (empty list): {result}")
            return result
        
        # 非空リストの処理
        current_tail = cls(Term("[]"), None)  # 空リストで終了
        for element in reversed(lst):
            current_tail = cls(element, current_tail)
        logger.debug(f"Dot.from_list returning (non-empty list): {current_tail}")
        return current_tail

    @staticmethod
    def concat(dot1, dot2):
        return Dot.from_list(list(dot1) + list(dot2))

    def _match_lsts(self, lst1, lst2):
        m = list(map((lambda arg1, arg2: arg1.match(arg2)), lst1, lst2))

        return reduce(merge_bindings, [{}] + m)

    def match(self, other):
        logger.debug(f"Dot.match({self}) called with other: {other}")
        if isinstance(other, Bar):
            res_bar_match = other.match(self)
            logger.debug(f"Dot.match (delegating to Bar.match) returning: {res_bar_match}")
            return res_bar_match

        if not isinstance(other, Dot):
            logger.debug("Dot.match (other is not Dot) returning: {}")
            return {} # Should be None for no match, or {} for no bindings? Original was {}

        l1 = list(self)
        l2 = list(other)
        if len(l1) == len(l2):
            res_match_lsts = self._match_lsts(l1, l2)
            logger.debug(f"Dot.match (lengths equal) returning: {res_match_lsts}")
            return res_match_lsts
        logger.debug("Dot.match (lengths differ) returning: None")
        return None

    def substitute(self, bindings):
        logger.debug(f"Dot.substitute({self}) called with bindings: {bindings}")
        
        # 空リストの特殊ケース処理
        if isinstance(self.head, Term) and self.head.pred == "[]" and self.tail is None:
            # 空リストはそのまま返す - 置換の必要なし
            logger.debug(f"Dot.substitute: empty list detected, returning unchanged")
            return self
        
        # 値が代入されている場合の処理
        value = bindings.get(self, None)
        if value is not None:
            result = value.substitute(bindings)
            logger.debug(f"Dot.substitute: bound value found, returning: {result}")
            return result
        
        # 非空リストの通常の処理
        substituted_head = self.head.substitute(bindings)
        substituted_tail = None if self.tail is None else self.tail.substitute(bindings)
        
        result = Dot(substituted_head, substituted_tail)
        logger.debug(f"Dot.substitute: returning with substituted head/tail: {result}")
        return result

    def query(self, runtime):
        yield from runtime.execute(self)

    def __iter__(self):
        self._current_element = self
        return self

    def __next__(self):
        if self._current_element is None or \
           (isinstance(self._current_element.head, Term) and \
            self._current_element.head.pred == "[]" and \
            self._current_element.tail is None):
            raise StopIteration
        element = self._current_element.head
        self._current_element = self._current_element.tail
        return element

    def __str__(self):
        if self.head and isinstance(self.head, Term) and str(self.head) == "[]" and self.tail is None:
            return "[]"
        elements = []
        current = self
        # The iteration logic here must align with __iter__/__next__
        # If list(self) is now correct (e.g. list(Dot(Term("[]"),None)) == []), then this can be simplified.
        py_list = list(self) # Relies on __iter__ and __next__ being correct
        if not py_list: # Handles truly empty list
            # This case should be hit if self is Dot(Term("[]"), None) and list(self) is []
            # However, if self.head is Term("[]") and self.tail is None, the first check already returns "[]"
            # This part might be redundant if the first check and list(self) are consistent.
            # Let's assume the first check `if self.head ... return "[]"` is for the canonical empty list object.
             pass # Covered by the first check or if py_list is used.

        # If the list has a non-Dot tail (e.g. [a,b|T])
        # list(self) would only give [a,b]. We need to find the tail if it's not the empty list marker.
        
        # Revised __str__ using a manual walk like before, as list(self) might not capture an open tail.
        elements_str = []
        current_node = self
        while current_node is not None and hasattr(current_node, 'head') and hasattr(current_node, 'tail'):
            if isinstance(current_node.head, Term) and current_node.head.pred == "[]" and current_node.tail is None:
                # This is the empty list marker, signifies end of proper list part
                if not elements_str: # Original list was empty
                    return "[]"
                break 
            elements_str.append(str(current_node.head))
            if not isinstance(current_node.tail, Dot): # Tail is a variable or other non-Dot term
                elements_str.append("|")
                elements_str.append(str(current_node.tail))
                break
            current_node = current_node.tail
            # If current_node becomes non-Dot (e.g. variable tail) but wasn't caught by `isinstance(current_node.tail, Dot)`
            # this means the list was improper. The `hasattr` checks should mostly cover this.
            if current_node is not None and not (hasattr(current_node, 'head') and hasattr(current_node, 'tail')):
                 # This case implies an improper list structure where tail is not None, not Dot,
                 # and not caught by the `isinstance(current_node.tail, Dot)` check.
                 # This should ideally not happen if lists are constructed correctly.
                 # For robustness, append it as a tail.
                 elements_str.append("|")
                 elements_str.append(str(current_node))
                 break
        
        if not elements_str:
             # This can happen if self was Dot(Term("[]"), None) and the loop didn't run.
             if isinstance(self.head, Term) and self.head.pred == "[]" and self.tail is None:
                 return "[]"
             # Or if it's some other non-list-like Dot structure
             if self.head is not None and self.tail is not None:
                 return f"[{str(self.head)}|{str(self.tail)}]"
             elif self.head is not None:
                 return f"[{str(self.head)}|.]" # Should not happen with proper lists
             else:
                 return "[?]"


        s = "["
        for i, el_str_val in enumerate(elements_str):
            if el_str_val == "|":
                s = s.rstrip(", ") + " | "
            elif i > 0 and elements_str[i-1] != "|":
                s += ", " + el_str_val
            else: # First element or element after |
                s += el_str_val
        s += "]"
        return s

    def __repr__(self):
        return str(self)

# Corrected __next__ for Dot class, to be placed inside the class definition
# This is a conceptual note; the actual code is part of the Dot class above.
# def __next__(self):
#     if self._current_element is None or \
#        (isinstance(self._current_element.head, Term) and \
#         self._current_element.head.pred == "[]" and \
#         self._current_element.tail is None):
#         raise StopIteration
#     element = self._current_element.head
#     self._current_element = self._current_element.tail
#     return element
# The __next__ method inside the Dot class needs to be updated to this logic.
# The current __next__ in the Dot class (as of the last successful write) is:
#    def __next__(self):
#        if self._current_element is None:
#            raise StopIteration
#        element = self._current_element.head
#        self._current_element = self._current_element.tail
#        return element
# This needs to be replaced with the version that correctly stops for Term("[]")

class Bar:
    def __init__(self, head, tail):
        # logger.debug(f"Bar initialized with head: {head}, tail: {tail}") # Can be very verbose
        self.head = head
        self.tail = tail

    def match(self, other):
        logger.debug(f"Bar.match({self}) called with other: {other}")
        if not isinstance(other, Dot):
            logger.debug("Bar.match (other is not Dot) returning: None")
            return None

        try:
            if isinstance(self.head, Dot):
                len_self_head = 0
                # Correctly get length of a Dot list by iterating it
                for _ in self.head: # Relies on Dot being iterable
                    len_self_head += 1
            elif isinstance(self.head, Variable) or isinstance(self.head, Term):
                logger.warning(f"Bar.match: self.head ({self.head}, type {type(self.head)}) is not a Dot. " +
                               "This match logic expects self.head to be a list prefix (Dot). " +
                               "Treating as non-match for this complex prefix logic.")
                return None
            else: 
                logger.error(f"Bar.match: self.head ({self.head}, type {type(self.head)}) has unexpected type for prefix matching.")
                return None
        except TypeError as e: # This will catch if self.head (if Dot) is not iterable
            logger.error(f"Bar.match: TypeError when trying to determine length of self.head ({self.head}). Error: {e}. Cannot determine prefix length.")
            return None

        other_elements = []
        try:
            other_elements = list(other) # Relies on other (Dot) being iterable
        except TypeError as e:
            logger.error(f"Bar.match: TypeError when trying to convert 'other' to list. Error: {e}")
            return None

        if len(other_elements) < len_self_head: 
            logger.debug("Bar.match (other list too short) returning: None")
            return None

        other_left_elements = other_elements[:len_self_head]
        other_right_elements = other_elements[len_self_head:]

        other_head_dot = Dot.from_list(other_left_elements)
        other_tail_dot = Dot.from_list(other_right_elements)

        head_match = self.head.match(other_head_dot)
        tail_match = self.tail.match(other_tail_dot)

        if head_match is not None and tail_match is not None:
            merged = merge_bindings(head_match, tail_match) 
            logger.debug(f"Bar.match (success) returning: {merged}")
            return merged 

        logger.debug("Bar.match (failed) returning: None")
        return None

    def substitute(self, bindings):
        logger.debug(f"Bar.substitute({self}) called with bindings: {bindings}")
        new_head = self.head.substitute(bindings)
        new_tail = self.tail.substitute(bindings)
        result = Bar(new_head, new_tail)
        logger.debug(f"Bar.substitute returning: {result}")
        return result

    def query(self, runtime):
        yield from runtime.execute(self)

    def __str__(self):
        output = '['
        if isinstance(self.head, Dot):
            head_str = str(self.head) 
            if head_str == "[]":
                output += head_str 
            elif head_str.startswith('[') and head_str.endswith(']'):
                output += head_str[1:-1] 
            else:
                logger.warning(f"Bar.__str__: Unexpected str(self.head) format for Dot: {head_str}")
                output += head_str
        else:
            output += str(self.head)

        if self.tail:
            output += f' | {self.tail}'
        output += ']'
        return output

    def __repr__(self):
        return str(self)

class Term:
    def __init__(self, pred, *args):
        # logger.debug(f"Term initialized with pred: {pred}, args: {args}") # Can be very verbose
        self.pred = pred
        self.args = list(args)

    def match(self, other):
        logger.debug(f"Term.match({self}) called with other: {other}")
        if isinstance(other, Term):
            if self.pred != other.pred or len(self.args) != len(other.args):
                logger.debug("Term.match (pred/arity mismatch) returning: None")
                return None

            m = []
            for arg1, arg2 in zip(self.args, other.args):
                match_result = arg1.match(arg2)
                if match_result is None: 
                    logger.debug(f"Term.match (arg mismatch: {arg1} vs {arg2}) returning: None")
                    return None
                m.append(match_result)
            
            try:
                final_bindings = reduce(merge_bindings, [{}] + m)
                logger.debug(f"Term.match (success) returning: {final_bindings}")
                return final_bindings
            except TypeError: 
                logger.error(f"Term.match error during merge_bindings with matches: {m}")
                return None

        if hasattr(other, 'match'):
            res_other_match = other.match(self)
            logger.debug(f"Term.match (delegating to other.match) returning: {res_other_match}")
            return res_other_match
        
        logger.debug("Term.match (other has no match method) returning: None")
        return None

    def substitute(self, bindings):
        logger.debug(f"Term.substitute({self}) called with bindings: {bindings}")
        substituted_args = [arg.substitute(bindings) for arg in self.args]
        result = Term(self.pred, *substituted_args)
        logger.debug(f"Term.substitute returning: {result}")
        return result

    def query(self, runtime):
        yield from runtime.execute(self)

    def __str__(self):
        if len(self.args) == 0:
            return f'{self.pred}'
        args = ', '.join(map(str, self.args))
        return f'{self.pred}({args})'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, Term):
            return NotImplemented
        return self.pred == other.pred and self.args == other.args

class TermFunction(Term):
    def __init__(self, func, predicate, *args):
        super().__init__(predicate, *args)
        self._func = func

    def _execute_func(self):
        result = next(self._func())
        if isinstance(result, tuple):
            self.args = [*result]
        else:
            self.args = [result]

    def match(self, other):
        if isinstance(other, Term):
            if self.pred != other.pred or len(self.args) != len(other.args):
                return None

            self._execute_func()
            m = list(
                map(
                    (lambda arg1, arg2: arg1.match(arg2)), self.args, other.args
                )
            )

            return reduce(merge_bindings, [{}] + m)

        return other.match(self)

class Logic:
    def __init__(self, expression):
        self._expression = expression

    def match(self, other):
        bindings = dict()
        if self != other:
            bindings[self] = self.evaluate()
        return bindings

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None:
            return value.substitute(bindings)

        expression_binder = ExpressionBinder(bindings)
        expression = self._expression.accept(expression_binder)
        return Logic(expression)

    def evaluate(self):
        return self._expression.accept(logic_interpreter)

    def query(self, runtime):
        yield self.evaluate()

    def __str__(self):
        return f'{self._expression}'

    def __repr__(self):
        return str(self)

class Arithmetic(Variable):
    def __init__(self, name, expression):
        super().__init__(name)
        self._expression = expression

    @property
    def args(self):
        return [self]

    @property
    def var(self):
        return self

    def _bind_name(self, bindings):
        for k, v in bindings.items():
            if isinstance(k, Variable) and k.name == self.name:
                if isinstance(v, Variable):
                    return v.name
        return self.name

    def match(self, other):
        bindings = dict()
        if self != other:
            bindings[self] = self.evaluate()
        return bindings

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None:
            return value.substitute(bindings)

        expression_binder = ExpressionBinder(bindings)
        name = self._bind_name(bindings)
        expression = self._expression.accept(expression_binder)
        return Arithmetic(name, expression)

    def evaluate(self):
        val = self._expression.accept(math_interpreter)
        return val

    def query(self, runtime):
        yield self

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return str(self)

class Number(Term):
    def __init__(self, pred):
        super().__init__(pred)

    def multiply(self, number):
        return Number(self.pred * number.pred)

    def divide(self, number):
        return Number(self.pred / number.pred)

    def add(self, number):
        return Number(self.pred + number.pred)

    def substract(self, number):
        return Number(self.pred - number.pred)

    def equal(self, number):
        if self.pred == number.pred:
            return TRUE()
        return FALSE()

    def not_equal(self, number):
        if self.pred != number.pred:
            return TRUE()
        return FALSE()

    def equal_less(self, number):
        if self.pred <= number.pred:
            return TRUE()
        return FALSE()

    def less(self, number):
        if self.pred < number.pred:
            return TRUE()
        return FALSE()

    def greater_equal(self, number):
        if self.pred >= number.pred:
            return TRUE()
        return FALSE()

    def greater(self, number):
        if self.pred > number.pred:
            return TRUE()
        return FALSE()

class TRUE(Term):
    def __init__(self):
        # トークンのlexemeに合わせて"true"を述語名として使用
        super().__init__("true")

    def substitute(self, bindings):
        return self

    def query(self, runtime):
        # TRUEは常に空のバインディングで成功する
        logger.debug("TRUE.query called, yielding empty bindings {}")
        yield {}

class FALSE(Term):
    def __init__(self):
        super().__init__(FALSE)

    def substitute(self, bindings):
        return {}

    def query(self, runtime):
        yield self

class CUT(Term):
    def __init__(self):
        super().__init__(CUT)

    def substitute(self, bindings):
        return {}

    def query(self, runtime):
        yield self

class ExpressionBinder(Visitor):
    """Binds variables.

    This class given dictionary of variable bindings walks expression tree
    and substitutes each variable for the value found in bindings dictionary.
    This returns identical expression tree as the input but with variables
    replaced with values.
    """

    def __init__(self, bindings):
        self._bindings = bindings

    def _bind_expr(self, expr):
        return expr.accept(self)

    def visit_binary(self, expr):
        left = self._bind_expr(expr.left)
        right = self._bind_expr(expr.right)

        return BinaryExpression(left, expr.operand, right)

    def visit_primary(self, expr):
        exp = expr.exp
        if isinstance(exp, Variable):
            for k, v in self._bindings.items():
                if k.name == exp.name:
                    return PrimaryExpression(v)

        return expr

math_interpreter = MathInterpreter()
logic_interpreter = LogicInterpreter()
