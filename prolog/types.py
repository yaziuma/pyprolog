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
        # Convert self to list, substitute elements, then build new Dot from list
        substituted_elements = [elem.substitute(bindings) for elem in list(self)]
        result = Dot.from_list(substituted_elements)
        logger.debug(f"Dot.substitute returning: {result}")
        return result

    def query(self, runtime):
        yield from runtime.execute(self)

    def __iter__(self):
        self._current_element = self
        return self

    def __next__(self):
        if self._current_element is None:
            raise StopIteration
        element = self._current_element.head
        self._current_element = self._current_element.tail
        return element

    def __str__(self):
        if self.head and isinstance(self.head, Term) and str(self.head) == "[]" and self.tail is None:
            return "[]"
        # For non-empty lists or lists not matching the empty list pattern, convert to Python list and then to string.
        # This relies on __iter__ and __next__ correctly yielding elements.
        elements = []
        current = self
        while current is not None and hasattr(current, 'head') and hasattr(current, 'tail'):
            if isinstance(current.head, Term) and current.head.pred == "[]" and current.tail is None : # End of list marker
                 if not elements: # This was an empty list from the start, e.g. Dot(Term("[]"), None)
                    return "[]"
                 break
            elements.append(str(current.head))
            if not isinstance(current.tail, Dot): # Tail is a variable or other term
                elements.append("|")
                elements.append(str(current.tail))
                break
            current = current.tail
            if current is not None and not hasattr(current, 'head'): # Should not happen with proper Dot lists
                elements.append("|") # Indicate improper list end if tail is not Dot or None
                elements.append(str(current))
                break
        
        if not elements: # Should be caught by the first check if it's a canonical empty list
            if self.head and isinstance(self.head, Term) and self.head.pred == "[]" and self.tail is None:
                 return "[]"
            # Fallback for unusual Dot structures that don't iterate well or aren't canonical lists
            if self.head is not None and self.tail is not None:
                return f"[{self.head}|{self.tail}]" # Generic representation for non-list-like Dot
            elif self.head is not None:
                return f"[{self.head}|.]" # Indicate incomplete list if tail is missing
            else:
                return "[?]" # Unknown Dot structure

        # Construct string representation
        # If the loop ended with '|' then the last element is the tail variable/term
        s = "["
        for i, el_str in enumerate(elements):
            if el_str == "|":
                s = s.rstrip(", ") + " | "
            elif i > 0 and elements[i-1] != "|":
                s += ", " + el_str
            else: # First element or element after |
                s += el_str
        s += "]"
        return s

    def __repr__(self):
        return str(self)


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

        # This logic seems complex and might need careful review for correctness with new Dot.from_list
        try:
            # Attempt to get the length of self.head, assuming it's a list-like Dot
            if isinstance(self.head, Dot):
                len_self_head = len(list(self.head))
            elif isinstance(self.head, Variable) or isinstance(self.head, Term):
                # If H in [H|T] is a single Variable or Term, its "length" for prefix matching is 1.
                # This part of Bar.match is tricky. The original code implied self.head is a list.
                # If Bar is strictly for [PrefixList | TailVar], then self.head must be a Dot.
                # If Bar can be [ElementVar | TailVar], then this logic needs to be simpler:
                #   head_match = self.head.match(other.head)
                #   tail_match = self.tail.match(other.tail)
                # For now, stick to the idea that if self.head is not a Dot, this complex prefix match fails.
                logger.warning(f"Bar.match: self.head ({self.head}, type {type(self.head)}) is not a Dot. " +
                               "This match logic expects self.head to be a list prefix (Dot). " +
                               "Treating as non-match for this complex prefix logic.")
                return None
            else: # Should not happen if parser constructs Bar correctly
                logger.error(f"Bar.match: self.head ({self.head}, type {type(self.head)}) has unexpected type for prefix matching.")
                return None
        except TypeError:
            # This might happen if self.head is a Dot but its elements are not iterable,
            # or if list(self.head) fails for another reason.
            logger.error(f"Bar.match: TypeError when trying to determine length of self.head ({self.head}). Cannot determine prefix length.")
            return None

        other_elements = list(other)
        if len(other_elements) < len_self_head: # Not enough elements in other to match the prefix
            logger.debug("Bar.match (other list too short) returning: None")
            return None

        other_left_elements = other_elements[:len_self_head]
        other_right_elements = other_elements[len_self_head:]

        # other_head should be a Dot representing the prefix from 'other'
        # other_tail should be a Dot representing the rest of 'other'
        # However, Dot.from_list expects a list of terms, not already Dot objects.
        # If other_left_elements are already terms, this is fine.
        other_head_dot = Dot.from_list(other_left_elements)
        other_tail_dot = Dot.from_list(other_right_elements)

        head_match = self.head.match(other_head_dot)
        tail_match = self.tail.match(other_tail_dot)

        if head_match is not None and tail_match is not None:
            merged = merge_bindings(head_match, tail_match) # Use merge_bindings
            logger.debug(f"Bar.match (success) returning: {merged}")
            return merged # Return merged bindings

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
        output += ', '.join(map(str, self.head))
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
                if match_result is None: # If any arg fails to match, the whole term fails
                    logger.debug(f"Term.match (arg mismatch: {arg1} vs {arg2}) returning: None")
                    return None
                m.append(match_result)
            
            try:
                final_bindings = reduce(merge_bindings, [{}] + m)
                logger.debug(f"Term.match (success) returning: {final_bindings}")
                return final_bindings
            except TypeError: # merge_bindings might fail if a None was missed (shouldn't happen with check above)
                logger.error(f"Term.match error during merge_bindings with matches: {m}")
                return None


        # If other is not a Term, delegate (e.g., if other is a Variable)
        # This can lead to infinite recursion if not handled carefully (e.g. Var.match(Term) -> Term.match(Var))
        # Variable.match does not delegate back to Term.match if other is Term.
        if hasattr(other, 'match'):
            res_other_match = other.match(self)
            logger.debug(f"Term.match (delegating to other.match) returning: {res_other_match}")
            return res_other_match
        
        logger.debug("Term.match (other has no match method) returning: None")
        return None # No match if other is not Term and has no match method

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
        super().__init__(TRUE)

    def substitute(self, bindings):
        return self

    def query(self, runtime):
        yield self


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
