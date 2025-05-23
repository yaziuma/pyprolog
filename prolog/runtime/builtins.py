from abc import ABC, abstractmethod
from prolog.core.merge_bindings import merge_bindings
from prolog.core.types import Term, TRUE_TERM, FALSE_TERM


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
    def execute(self, runtime):
        pass

    def query(self, runtime, bindings=None):
        if bindings is None:
            bindings = {}

        if hasattr(self.arg, "query"):
            param_bound = list(self.arg.query(runtime))
            if param_bound:
                param_bound_term = param_bound[0]
                match_result_bindings = self.match(param_bound_term)
                unified = merge_bindings(match_result_bindings, bindings)
                substituted = self.substitute(unified)
                if substituted is not None and hasattr(substituted, "execute"):
                    substituted.execute(runtime)
            else:
                substituted = self.substitute(bindings)
                if substituted is not None and hasattr(substituted, "execute"):
                    substituted.execute(runtime)
        else:
            substituted = self.substitute(bindings)
            if substituted is not None and hasattr(substituted, "execute"):
                substituted.execute(runtime)

        yield bindings


class Retract(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)
        self.pred = "retract"

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None and hasattr(value, "substitute"):
            if hasattr(value, "args") and value.args:
                return Retract(value.args[0].substitute(bindings))
            elif isinstance(value, DatabaseOp):
                return Retract(value.arg.substitute(bindings))
            else:
                return Retract(value)

        if hasattr(self.arg, "substitute"):
            substituted_arg = self.arg.substitute(bindings)
            if substituted_arg is not None:
                return Retract(substituted_arg)
            return None
        return Retract(self.arg)

    def execute(self, runtime):
        if hasattr(runtime, "remove_rule"):
            runtime.remove_rule(self.arg)

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class AssertA(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)
        self.pred = "asserta"

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
        super().__init__(arg)
        self.pred = "assertz"

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


# BuiltinCutとBuiltinFailクラスを追加
class Cut(Term):
    """カット演算子のBuiltin実装"""
    def __init__(self):
        super().__init__("!")
        self.pred = "!"

    def substitute(self, bindings):
        return self

    def __str__(self):
        return "!"

    def __repr__(self):
        return "Cut()"


class Fail(Term):
    """Fail演算子のBuiltin実装"""
    def __init__(self):
        super().__init__("fail")
        self.pred = "fail"

    def substitute(self, bindings):
        return self

    def __str__(self):
        return "fail"

    def __repr__(self):
        return "Fail()"


# エイリアス（後方互換性のため）
BuiltinCut = Cut
BuiltinFail = Fail