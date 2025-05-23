from prolog.logger import logger


class Variable:
    def __init__(self, name):
        # logger.debug(f"Variable initialized with name: {name}") # Can be very verbose
        self.name = name
        self.bindings = None  # For compatibility with some older logic, may not be used by BindingEnvironment

    def match(
        self, other, bindings=None
    ):  # bindings param for compatibility, not used by new unify
        # logger.debug(f"Variable.match({self}) called with other: {other}")
        # In the new system, unification is handled by BindingEnvironment.
        # This match might be used for specific cases or can be simplified.
        # For now, standard variable matching:
        if bindings is None:
            bindings = {}

        if self == other:  # Matching identical variable instance
            # logger.debug(f"Variable.match: self == other, returning bindings: {bindings}")
            return bindings

        if self.name == "_":  # Anonymous variable matches anything
            # logger.debug(f"Variable.match: anonymous var, returning bindings: {bindings}")
            return bindings
        if (
            isinstance(other, Variable) and other.name == "_"
        ):  # Matching against anonymous var
            # logger.debug(f"Variable.match: other is anonymous var, returning bindings: {bindings}")
            return bindings

        # If self is already bound in the provided bindings (legacy path)
        if self in bindings:
            bound_value = bindings[self]
            # logger.debug(f"Variable.match: self ({self.name}) is bound to {bound_value} in provided bindings.")
            if hasattr(bound_value, "match"):
                return bound_value.match(other, bindings)
            return bindings if bound_value == other else None

        # If other is already bound in the provided bindings (legacy path)
        if isinstance(other, Variable) and other in bindings:
            bound_value_other = bindings[other]
            # logger.debug(f"Variable.match: other ({other.name}) is bound to {bound_value_other} in provided bindings.")
            # Recursive match: self against the value of other
            return self.match(bound_value_other, bindings)

        # Default: bind self to other
        new_bindings = bindings.copy()
        new_bindings[self] = other
        # logger.debug(f"Variable.match: binding {self.name} to {other}, returning new_bindings: {new_bindings}")
        return new_bindings

    def substitute(self, bindings):
        # logger.debug(f"Variable.substitute({self}) called with bindings: {bindings}")
        # BindingEnvironment.get_value should be the primary way to get a var's value.
        # This substitute is for applying a given set of bindings (e.g., from a match).

        # Check if the variable itself is in the bindings dictionary
        if self in bindings:
            value = bindings[self]
            # logger.debug(f"Variable.substitute: {self.name} found in bindings, value: {value}. Recursively substituting.")
            # If the value is another variable, or a term, it might need further substitution.
            # Avoid infinite recursion if X is bound to X.
            if value == self:
                return self
            # If value is a term or variable that can be substituted:
            if hasattr(value, "substitute"):
                # Pass the same bindings dict for recursive substitution.
                # This allows chains like X=Y, Y=Z, Z=a to resolve X to a.
                return value.substitute(bindings)
            return value  # Value is a constant or something not substitutable further by this call

        # logger.debug(f"Variable.substitute: {self.name} not in bindings, returning self.")
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
        # logger.debug(f"Term initialized with pred: {pred}, args: {args}")
        self.pred = pred
        self.args = list(args)
        # self.bindings = None # This was in types.py Term, not typically part of core Term structure

    def match(self, other, bindings=None):  # bindings param for compatibility
        # logger.debug(f"Term.match({self}) called with other: {other}")
        # Unification is primarily handled by BindingEnvironment.
        # This match is for specific cases or can be simplified.
        if bindings is None:
            bindings = {}

        if isinstance(other, Variable):
            # logger.debug(f"Term.match: other is Variable {other.name}. Delegating to other.match(self).")
            return other.match(self, bindings)  # Variable handles matching a Term

        if isinstance(other, Term):
            if self.pred != other.pred or len(self.args) != len(other.args):
                # logger.debug("Term.match: pred/arity mismatch, returning None.")
                return None

            current_bindings = bindings.copy()
            for arg1, arg2 in zip(self.args, other.args):
                if hasattr(arg1, "match"):
                    match_result = arg1.match(arg2, current_bindings)
                    if match_result is None:
                        # logger.debug(f"Term.match: arg mismatch ({arg1} vs {arg2}), returning None.")
                        return None
                    current_bindings.update(match_result)  # Accumulate bindings
                elif arg1 != arg2:  # If arg1 is not matchable (e.g. Python constant)
                    # logger.debug(f"Term.match: non-matchable arg mismatch ({arg1} vs {arg2}), returning None.")
                    return None
            # logger.debug(f"Term.match: success, returning bindings: {current_bindings}")
            return current_bindings

        # logger.debug("Term.match: other is not Variable or Term, returning None.")
        return None

    def substitute(self, bindings):
        # logger.debug(f"Term.substitute({self}) called with bindings: {bindings}")
        # Substitute arguments
        substituted_args = []
        for arg in self.args:
            if hasattr(arg, "substitute"):
                substituted_args.append(arg.substitute(bindings))
            else:
                substituted_args.append(
                    arg
                )  # Arg is not substitutable (e.g. Python constant)

        # Return new Term with substituted arguments
        # logger.debug(f"Term.substitute: returning new Term({self.pred}, {substituted_args})")
        return Term(self.pred, *substituted_args)

    def __str__(self):
        if not self.args:  # Handles atoms like 'true', 'fail'
            return str(self.pred)
        args_str = ", ".join(map(str, self.args))
        return f"{self.pred}({args_str})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        # Make Term hashable if its predicate and args are.
        # Args are a list, so convert to tuple for hashing.
        try:
            return hash((self.pred, tuple(self.args)))
        except TypeError:
            # If args are not hashable (e.g., contain lists or unhashable custom objects),
            # then this Term instance is not hashable.
            # This can be an issue if Terms are used as dict keys directly without care.
            # For BindingEnvironment, Variables are keys, and their hash is based on name.
            logger.warning(f"Term '{self}' is not hashable due to its arguments.")
            raise TypeError(f"Unhashable type in Term arguments: {self.args}")

    def __eq__(self, other):
        if not isinstance(other, Term):
            return NotImplemented
        return self.pred == other.pred and self.args == other.args


class Rule:  # Basic Rule structure
    def __init__(self, head, body):
        if not isinstance(head, Term):
            # logger.error(f"Rule head must be a Term, got {type(head)}")
            # For simplicity, allow non-Term heads if they are special like TRUE, etc.
            # Or enforce Term for structured heads.
            pass
        if not (
            isinstance(body, Term)
            or isinstance(body, Conjunction)
            or body is TRUE()
            or body is FALSE()
            or isinstance(body, Variable)
        ):  # body can be complex
            # logger.error(f"Rule body must be a Term, Conjunction, TRUE, FALSE or Variable, got {type(body)}")
            pass
        self.head = head
        self.body = body

    def __str__(self):
        if isinstance(self.body, TRUE):
            return f"{self.head}."
        return f"{self.head} :- {self.body}."

    def __repr__(self):
        return str(self)

    # Substitute for Rule might be needed if rules are manipulated with bindings
    def substitute(self, bindings):
        # logger.debug(f"Rule.substitute({self}) called with bindings: {bindings}")
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


class Conjunction(Term):  # Conjunction is a special kind of Term
    def __init__(self, goals):  # goals is a list of terms/conj/etc.
        super().__init__(
            ",", *goals
        )  # Use ',' as predicate for conjunction, args are the goals

    def substitute(self, bindings):
        # logger.debug(f"Conjunction.substitute({self}) called with bindings: {bindings}")
        substituted_goals = [
            g.substitute(bindings) if hasattr(g, "substitute") else g for g in self.args
        ]
        return Conjunction(substituted_goals)

    def __str__(self):
        return "(" + ", ".join(map(str, self.args)) + ")"


# Singleton TRUE, FALSE, CUT, Fail objects
class _SingletonTerm(Term):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(_SingletonTerm, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def substitute(self, bindings):  # Singleton terms are not affected by substitution
        return self


class TRUE(_SingletonTerm):
    def __init__(self):
        super().__init__("true")  # Atom 'true'


class FALSE(_SingletonTerm):
    def __init__(self):
        super().__init__("false")  # Atom 'false'


class CUT(_SingletonTerm):  # This is the CUT *signal*
    def __init__(self):
        super().__init__("!")  # Representation for the signal


class Fail(Term):  # Fail is a term that always fails, like 'fail/0'
    def __init__(self):
        super().__init__("fail")


# Instantiate singletons for use
# Using specific names for instances to avoid Pylance confusion with class names
TRUE_TERM = TRUE()
FALSE_TERM = FALSE()
CUT_SIGNAL = CUT()
FAIL_TERM = Fail()
