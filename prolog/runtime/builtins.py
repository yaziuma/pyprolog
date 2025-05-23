from abc import ABC, abstractmethod
from prolog.core.merge_bindings import merge_bindings
# Unused imports: Cut as CoreCut, Fail as CoreFail


class BuiltinsBase(ABC):
    @abstractmethod
    def match(self, other):
        pass

    @abstractmethod
    def substitute(self, bindings):
        pass

    @abstractmethod
    def display(self, stream_writer):
        pass

    def query(self, runtime, bindings=None):
        if bindings is None:
            bindings = {}
        substituted = self.substitute(bindings)
        if substituted is not None and hasattr(substituted, "display"):
            substituted.display(runtime.stream_write)
        yield bindings


class Write(BuiltinsBase):
    def __init__(self, *args):
        self.pred = "write"
        self.args = list(args)

    def match(self, other):
        return {}

    def substitute(self, bindings):
        def substitute_arg(arg):
            if hasattr(arg, "substitute"):
                return arg.substitute(bindings)
            return arg

        result = Write(*map(substitute_arg, self.args))
        return result

    def display(self, stream_writer):
        for arg in self.args:
            stream_writer(str(arg))

    def __str__(self):
        if len(self.args) == 0:
            return f"{self.pred}"
        args = ", ".join(map(str, self.args))
        return f"{self.pred}({args})"

    def __repr__(self):
        return str(self)


class Nl(BuiltinsBase):
    def __init__(self):
        self.pred = "nl"

    def match(self, other):
        return {}

    def substitute(self, bindings):
        return Nl()

    def display(self, stream_writer):
        stream_writer("\n")

    def __str__(self):
        return "nl"

    def __repr__(self):
        return str(self)


class Tab(BuiltinsBase):
    def __init__(self):
        self.pred = "tab"

    def match(self, other):
        return {}

    def substitute(self, bindings):
        return Tab()

    def display(self, stream_writer):
        stream_writer("\t")

    def __str__(self):
        return self.pred

    def __repr__(self):
        return str(self)


class DatabaseOp(ABC):
    def __init__(self, arg):
        self.arg = arg

    def match(self, other):
        bindings = dict()
        if self != other:
            bindings[self] = other
        return bindings

    @abstractmethod
    def substitute(self, bindings):
        pass

    @abstractmethod
    def execute(self, runtime):  # Changed parameter name from remove_rule to runtime
        pass

    def query(self, runtime, bindings=None):
        if bindings is None:
            bindings = {}

        if hasattr(self.arg, "query"):
            param_bound = list(
                self.arg.query(runtime)
            )  # As per user's initial prompt, no bindings passed to self.arg.query
            if param_bound:  # if arg.query succeeded and yielded results
                param_bound_term = param_bound[0]  # Take the first result (a Term)

                # The self.match(param_bound_term) part:
                # self is DatabaseOp instance, e.g. Retract(X)
                # param_bound_term is a Term, e.g. my_fact(a)
                # DatabaseOp.match(self, other) is:
                #   bindings_map = dict()
                #   if self != other: bindings_map[self] = other
                #   return bindings_map
                # So, match_result_bindings = {Retract(X): my_fact(a)} if they differ.
                match_result_bindings = self.match(param_bound_term)

                unified = merge_bindings(match_result_bindings, bindings)
                # unified now might contain {Retract(X): my_fact(a), ... existing bindings ...}

                substituted = self.substitute(unified)
                # For Retract(X).substitute(unified):
                #   value = unified.get(Retract(X), None) -> my_fact(a)
                #   if value (my_fact(a)) is not None and hasattr(value, 'substitute'):
                #     if hasattr(my_fact(a), 'args') and my_fact(a).args: -> e.g. arg is 'a'
                #       return Retract(my_fact(a).args[0].substitute(unified)) -> Retract('a'.substitute(unified)) -> Retract('a')
                #     elif isinstance(my_fact(a), DatabaseOp): ...
                #     else: return Retract(my_fact(a)) -> Retract(my_fact(a))
                # This logic seems to be what the user intended for DatabaseOp argument resolution.

                if substituted is not None and hasattr(substituted, "execute"):
                    substituted.execute(runtime)
            else:  # self.arg.query failed or yielded no results
                substituted = self.substitute(bindings)
                if substituted is not None and hasattr(substituted, "execute"):
                    substituted.execute(runtime)
        else:  # self.arg is not queryable (e.g., a simple term like `foo(a)` or a variable)
            substituted = self.substitute(bindings)
            if substituted is not None and hasattr(substituted, "execute"):
                substituted.execute(runtime)

        yield bindings


class Retract(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)  # Call parent __init__
        self.pred = "retract"
        # self.arg = arg # Already done by super

    def substitute(self, bindings):
        # This substitution logic is from the user's initial prompt
        value = bindings.get(self, None)  # Check if the DatabaseOp itself is bound
        if value is not None and hasattr(
            value, "substitute"
        ):  # If `retract(X)` is bound to `retract(foo(a))`
            # `value` would be the `retract(foo(a))` term.
            # We need to return a new `Retract` instance with the argument from `value`.
            if hasattr(value, "args") and value.args:
                return Retract(
                    value.args[0].substitute(bindings)
                )  # Substitute the arg of the bound value
            elif isinstance(
                value, DatabaseOp
            ):  # If bound to another DatabaseOp instance
                return Retract(value.arg.substitute(bindings))  # Substitute its arg
            else:  # If bound to a simple term, use it as the argument
                return Retract(value)  # Or value.substitute(bindings) if it's a term?

        # If the DatabaseOp itself is not bound, substitute its argument
        if hasattr(self.arg, "substitute"):
            substituted_arg = self.arg.substitute(bindings)
            if substituted_arg is not None:
                return Retract(substituted_arg)
            return None  # If arg substitution fails
        return Retract(
            self.arg
        )  # Arg is not substitutable (e.g. a Python string/number)

    def execute(self, runtime):
        if hasattr(runtime, "remove_rule"):  # Check if runtime can remove_rule
            runtime.remove_rule(self.arg)

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class AssertA(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)  # Call parent __init__
        self.pred = "asserta"
        # self.arg = arg

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None and hasattr(value, "substitute"):
            if hasattr(value, "args") and value.args:
                return AssertA(value.args[0].substitute(bindings))
            elif isinstance(value, DatabaseOp):
                return AssertA(value.arg.substitute(bindings))
            else:
                return AssertA(value)

        if hasattr(self.arg, "substitute"):
            substituted_arg = self.arg.substitute(bindings)
            if substituted_arg is not None:
                return AssertA(substituted_arg)
            return None
        return AssertA(self.arg)

    def execute(self, runtime):
        if hasattr(runtime, "insert_rule_left"):
            runtime.insert_rule_left(self.arg)

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class AssertZ(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)  # Call parent __init__
        self.pred = "assertz"
        # self.arg = arg

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None and hasattr(value, "substitute"):
            if hasattr(value, "args") and value.args:
                return AssertZ(value.args[0].substitute(bindings))
            elif isinstance(value, DatabaseOp):
                return AssertZ(value.arg.substitute(bindings))
            else:
                return AssertZ(value)

        if hasattr(self.arg, "substitute"):
            substituted_arg = self.arg.substitute(bindings)
            if substituted_arg is not None:
                return AssertZ(substituted_arg)
            return None
        return AssertZ(self.arg)

    def execute(self, runtime):
        if hasattr(runtime, "insert_rule_right"):
            runtime.insert_rule_right(self.arg)

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)
