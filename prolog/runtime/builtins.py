from abc import ABC, abstractmethod
from prolog.core.merge_bindings import merge_bindings
from prolog.core.types import TRUE_TERM as TRUE # Added import for TRUE


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

    def query(self, runtime, bindings={}):
        self.substitute(bindings).display(runtime.stream_write)
        yield bindings


class Fail:
    def __init__(self):
        self.name = 'fail'

    def match(self, other):
        return None

    def substitute(self, bindings):
        return self

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)

    def query(self, runtime):
        # 螟ｱ謨玲凾縺ｫ縺ｯ菴輔ｂ邨先棡繧定ｿ斐＆縺ｪ縺・ｼ郁ｧ｣縺後ぞ繝ｭ・・
        # logger.debug(f"Fail.query called") # logger is not defined here
        if False:  # 縺薙・譚｡莉ｶ縺ｯ蟶ｸ縺ｫfalse
            yield  # 縺薙・陦後・螳溯｡後＆繧後↑縺・ｼ医ず繧ｧ繝阪Ξ繝ｼ繧ｿ縺ｫ縺吶ｋ縺溘ａ縺ｮ譁・ｳ慕噪縺ｪ隕∫ｴ・・
        # 菴輔ｂyield縺帙★縺ｫ蜊ｳ譎ゅΜ繧ｿ繝ｼ繝ｳ = 螟ｱ謨励ｒ諢丞袖縺吶ｋ


class Cut:
    def __init__(self):
        # The parser creates this for '!' token.
        # The name 'cut' might be for internal representation or if it were callable by name.
        # For '!', the predicate name is effectively '!'.
        self.name = '!' # Changed from 'cut' to '!' to match typical Prolog representation

    def match(self, other):
        # A cut should generally match if the other thing is also a cut.
        # However, its primary role is procedural, not unification in the typical sense.
        # Returning {} (empty bindings, meaning success with no new bindings) is common.
        if isinstance(other, Cut):
            return {}
        return None # Fails to match anything else

    def substitute(self, bindings):
        # Cut is a procedural construct, its identity doesn't change with bindings.
        return self

    def query(self, runtime, bindings=None):
        # When a Cut is encountered in a query, it succeeds once and then
        # prunes choice points. The "succeeds once" part means it yields TRUE.
        # The pruning is handled by the interpreter when it sees the CUT signal.
        if bindings is None:
            bindings = {}
        yield TRUE() # Cut itself evaluates to true.

    def __str__(self):
        return self.name # Should be '!'

    def __repr__(self):
        return str(self)


class Write(BuiltinsBase):
    def __init__(self, *args):
        self.pred = 'write'
        self.args = list(args)

    def match(self, other):
        return {}

    def substitute(self, bindings):
        result = Write(*map((lambda arg: arg.substitute(bindings)), self.args))
        return result

    def display(self, stream_writer):
        for arg in self.args:
            stream_writer(str(arg))

    def __str__(self):
        if len(self.args) == 0:
            return f'{self.pred}'
        args = ', '.join(map(str, self.args))
        return f'{self.pred}({args})'

    def __repr__(self):
        return str(self)


class Nl(BuiltinsBase):
    def __init__(self):
        self.pred = 'nl'

    def match(self, other):
        return {}

    def substitute(self, bindings):
        return Nl()

    def display(self, stream_writer):
        stream_writer('\n')

    def __str__(self):
        return 'nl'

    def __repr__(self):
        return str(self)


class Tab(BuiltinsBase):
    def __init__(self):
        self.pred = 'tab'

    def match(self, other):
        return {}

    def substitute(self, bindings):
        return Tab()

    def display(self, stream_writer):
        stream_writer('\t')

    def __str__(self):
        return self.pred

    def __repr__(self):
        return str(self)


class DatabaseOp(ABC):
    def match(self, other):
        bindings = dict()
        if self != other:
            bindings[self] = other
        return bindings

    @abstractmethod
    def substitute(self, bindings):
        pass

    @abstractmethod
    def execute(self, remove_rule):
        pass

    def query(self, runtime, bindings={}):
        param_bound = list(self.arg.query(runtime))
        if param_bound:
            param_bound = param_bound[0]
            unified = merge_bindings(self.match(param_bound), bindings)
            self.substitute(unified).execute(runtime)
        else:
            self.substitute(bindings).execute(runtime)
        yield bindings


class Retract(DatabaseOp):
    def __init__(self, arg):
        self.pred = 'retract'
        self.arg = arg

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None:
            return Retract(value.substitute(bindings))
        return Retract(self.arg.substitute(bindings))

    def execute(self, runtime):
        runtime.remove_rule(self.arg)

    def __str__(self):
        return f'{self.pred}({self.arg})'

    def __repr__(self):
        return str(self)


class AssertA(DatabaseOp):
    def __init__(self, arg):
        self.pred = 'asserta'
        self.arg = arg

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None:
            return AssertA(value.substitute(bindings))
        return AssertA(self.arg.substitute(bindings))

    def execute(self, runtime):
        runtime.insert_rule_left(self.arg)

    def __str__(self):
        return f'{self.pred}({self.arg})'

    def __repr__(self):
        return str(self)


class AssertZ(DatabaseOp):
    def __init__(self, arg):
        self.pred = 'assertz'
        self.arg = arg

    def substitute(self, bindings):
        value = bindings.get(self, None)
        if value is not None:
            return AssertZ(value.substitute(bindings))
        return AssertZ(self.arg.substitute(bindings))

    def execute(self, runtime):
        runtime.insert_rule_right(self.arg)

    def __str__(self):
        return f'{self.pred}({self.arg})'

    def __repr__(self):
        return str(self)
