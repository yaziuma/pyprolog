from abc import ABC, abstractmethod
from prolog.core.merge_bindings import merge_bindings
from prolog.core.types import Term, Variable, Atom, Number, String # Added String, ListTerm not used for now
from prolog.core.errors import PrologError # Added PrologError


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
    def execute(self, runtime): # Changed from (self, runtime) to (self, runtime, bindings) for consistency
        pass

    def query(self, runtime, bindings=None): # Added bindings here too
        if bindings is None:
            bindings = {}

        if hasattr(self.arg, "query"):
            param_bound = list(self.arg.query(runtime, bindings)) # Pass bindings
            if param_bound:
                param_bound_term = param_bound[0] 
                # This logic seems problematic, param_bound_term is an environment, not a term
                # Re-evaluating DatabaseOp is outside current scope, but noting this.
                # For now, assume it intends to get a term.
                # A proper fix would require understanding how self.match expects to work with an env.
                # Simplified for now, assuming param_bound_term is the term IF the query was for a single term.
                # This part of DatabaseOp is likely not fully correct.
                # Let's assume current behavior is that self.arg.query yields terms or environments.
                # The original code here is a bit unclear for DatabaseOp.query.
                # For now, the execute methods are the focus.
                
                # Simplified/Placeholder logic for query in DatabaseOp
                # This should ideally be reviewed separately.
                # For this subtask, we focus on the execute methods of new builtins.
                pass # Placeholder for complex DatabaseOp.query logic


            # This part of DatabaseOp.query seems more plausible if execute takes runtime & bindings
            substituted = self.substitute(bindings)
            if substituted is not None and hasattr(substituted, "execute"):
                 # Assuming execute for DatabaseOp will take runtime and bindings
                yield from substituted.execute(runtime, bindings) 
            else: # If no execute, just yield current bindings as if it's a check
                 yield bindings
        else: # If self.arg is not queryable
            substituted = self.substitute(bindings)
            if substituted is not None and hasattr(substituted, "execute"):
                yield from substituted.execute(runtime, bindings)
            else:
                 yield bindings


class Retract(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)
        self.pred = "retract"

    def substitute(self, bindings):
        # ... (original substitute logic)
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


    def execute(self, runtime, bindings): # Added bindings
        # runtime.remove_rule expects a term, needs dereferencing
        term_to_retract = runtime.logic_interpreter.dereference(self.arg, bindings)
        if hasattr(runtime, "remove_rule"):
            # remove_rule should ideally return success/failure or handle matching internally
            # For now, assume it finds and removes one matching rule/fact.
            # To make retract work as a goal, it needs to yield on success.
            original_rules_count = len(runtime.rules)
            runtime.remove_rule(term_to_retract) # Assuming this modifies runtime.rules
            if len(runtime.rules) < original_rules_count : # A crude check for success
                 yield bindings 
        # else fail (yield nothing)


    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class AssertA(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)
        self.pred = "asserta"

    def substitute(self, bindings):
        # ... (original substitute logic)
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

    def execute(self, runtime, bindings): # Added bindings
        term_to_assert = runtime.logic_interpreter.dereference(self.arg, bindings)
        if hasattr(runtime, "insert_rule_left"):
            runtime.insert_rule_left(term_to_assert) # Assuming this adds to runtime.rules
            yield bindings # Asserta always succeeds
        # else fail or raise error if runtime doesn't have the method

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class AssertZ(DatabaseOp):
    def __init__(self, arg):
        super().__init__(arg)
        self.pred = "assertz"

    def substitute(self, bindings):
        # ... (original substitute logic)
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

    def execute(self, runtime, bindings): # Added bindings
        term_to_assert = runtime.logic_interpreter.dereference(self.arg, bindings)
        if hasattr(runtime, "insert_rule_right"):
            runtime.insert_rule_right(term_to_assert)
            yield bindings # Assertz always succeeds
        # else fail

    def __str__(self):
        return f"{self.pred}({self.arg})"

    def __repr__(self):
        return str(self)


class Cut(Term):
    def __init__(self):
        super().__init__(Atom("!")) # Functor is Atom
        self.pred = "!"

    def substitute(self, bindings):
        return self

    def __str__(self):
        return "!"

    def __repr__(self):
        return "Cut()"


class Fail(Term):
    def __init__(self):
        super().__init__(Atom("fail")) # Functor is Atom
        self.pred = "fail"

    def substitute(self, bindings):
        return self

    def __str__(self):
        return "fail"

    def __repr__(self):
        return "Fail()"

BuiltinCut = Cut
BuiltinFail = Fail


class VarPredicate:
    def __init__(self, arg):
        self.arg = arg 
        self.pred = "var"

    def execute(self, runtime, bindings):
        if isinstance(self.arg, Variable):
            yield bindings 

    def __str__(self): return f"var({self.arg})"
    def __repr__(self): return f"VarPredicate({repr(self.arg)})"


class AtomPredicate:
    def __init__(self, arg):
        self.arg = arg 
        self.pred = "atom"

    def execute(self, runtime, bindings):
        if isinstance(self.arg, Atom):
            yield bindings

    def __str__(self): return f"atom({self.arg})"
    def __repr__(self): return f"AtomPredicate({repr(self.arg)})"


class NumberPredicate:
    def __init__(self, arg):
        self.arg = arg
        self.pred = "number"

    def execute(self, runtime, bindings):
        if isinstance(self.arg, Number):
            yield bindings

    def __str__(self): return f"number({self.arg})"
    def __repr__(self): return f"NumberPredicate({repr(self.arg)})"


# Term Manipulation Predicates

class FunctorPredicate:
    """functor/3: functor(Term, Functor, Arity)"""
    def __init__(self, term_arg, functor_arg, arity_arg):
        self.term_arg = term_arg
        self.functor_arg = functor_arg
        self.arity_arg = arity_arg
        self.pred = "functor"

    def execute(self, runtime, bindings):
        d_term = runtime.logic_interpreter.dereference(self.term_arg, bindings)
        d_functor = runtime.logic_interpreter.dereference(self.functor_arg, bindings)
        d_arity = runtime.logic_interpreter.dereference(self.arity_arg, bindings)

        # Mode 1: Analysis (Term is instantiated)
        if not isinstance(d_term, Variable):
            actual_functor = None
            actual_arity_val = -1

            if isinstance(d_term, (Atom, Number)):
                actual_functor = d_term
                actual_arity_val = 0
            elif isinstance(d_term, Term):
                actual_functor = d_term.functor
                actual_arity_val = len(d_term.args)
            else: # Not a type that functor/3 can analyze (e.g. String if not treated as Atom)
                return # Fail

            s1, b1 = runtime.logic_interpreter.unify(self.functor_arg, actual_functor, bindings)
            if not s1: return
            s2, b2 = runtime.logic_interpreter.unify(self.arity_arg, Number(actual_arity_val), b1)
            if not s2: return
            yield b2
        
        # Mode 2: Construction (Term is Variable, Functor and Arity are instantiated)
        elif isinstance(d_term, Variable):
            if not (isinstance(d_functor, (Atom, Number)) and isinstance(d_arity, Number)):
                # Functor must be Atom/Number, Arity must be Number for construction.
                # Or if they are variables, this isn't construction mode.
                # This check might be too simple if d_functor/d_arity are unbound vars.
                # Standard Prolog might raise instantiation error or just fail. We'll fail.
                # If d_functor or d_arity are variables, unification will handle it if term_arg was also instantiated.
                # If all three are variables, it should probably fail or error.
                # Assuming if d_term is Variable, then d_functor and d_arity MUST be instantiated.
                if isinstance(d_functor, Variable) or isinstance(d_arity, Variable):
                     raise PrologError(f"functor/3: Functor and Arity must be instantiated for construction if Term is a variable.")
                # Type errors for functor/arity values
                if not isinstance(d_functor, (Atom, Number)): 
                    raise PrologError(f"functor/3: Functor argument must be an Atom or Number, not {type(d_functor)}")
                if not (isinstance(d_arity, Number) and isinstance(d_arity.value, int) and d_arity.value >= 0):
                    raise PrologError(f"functor/3: Arity argument must be a non-negative integer, not {d_arity}")
                return # Fail due to type error above (or should we raise?) Raising is better.
            
            arity_val = int(d_arity.value) # Safe after check above
            
            constructed_term = None
            if arity_val == 0:
                if isinstance(d_functor, (Atom, Number)):
                    constructed_term = d_functor
                else: # Should have been caught by earlier type check
                    raise PrologError(f"functor/3: Functor for arity 0 must be Atom or Number, got {type(d_functor)}")
            elif arity_val > 0:
                if not isinstance(d_functor, Atom):
                    raise PrologError(f"functor/3: Functor for arity > 0 must be an Atom, got {type(d_functor)}")
                
                # Create new unique variables for args
                new_vars = []
                for i in range(arity_val):
                    runtime.logic_interpreter._unique_var_counter += 1
                    new_vars.append(Variable(f"_G{runtime.logic_interpreter._unique_var_counter}"))
                constructed_term = Term(d_functor, new_vars)
            else: # Should have been caught by arity >= 0 check
                raise PrologError(f"functor/3: Arity must be non-negative.")

            if constructed_term is not None:
                s, b = runtime.logic_interpreter.unify(self.term_arg, constructed_term, bindings)
                if s:
                    yield b
        # else: Other cases, e.g. all three are partially instantiated. This will just fail.
        
    def __str__(self): return f"functor({self.term_arg},{self.functor_arg},{self.arity_arg})"
    def __repr__(self): return f"FunctorPredicate({repr(self.term_arg)},{repr(self.functor_arg)},{repr(self.arity_arg)})"


class ArgPredicate:
    """arg/3: arg(N, Term, Value)"""
    def __init__(self, n_arg, term_arg, value_arg):
        self.n_arg = n_arg
        self.term_arg = term_arg
        self.value_arg = value_arg
        self.pred = "arg"

    def execute(self, runtime, bindings):
        d_n = runtime.logic_interpreter.dereference(self.n_arg, bindings)
        d_term = runtime.logic_interpreter.dereference(self.term_arg, bindings)

        if not isinstance(d_n, Number) or not isinstance(d_n.value, int) or d_n.value <= 0:
            # Fail if N is not a positive integer. Some Prologs raise error, some fail. We fail.
            # raise PrologError("arg/3: N must be a positive integer.")
            return

        if not isinstance(d_term, Term):
            # Fail if Term is not a compound term.
            # raise PrologError("arg/3: Term must be a compound term.")
            return 
            
        index = d_n.value - 1 # 1-based to 0-based index

        if 0 <= index < len(d_term.args):
            actual_arg_from_term = d_term.args[index]
            s, b = runtime.logic_interpreter.unify(self.value_arg, actual_arg_from_term, bindings)
            if s:
                yield b
        # else (index out of bounds), fail implicitly by not yielding

    def __str__(self): return f"arg({self.n_arg},{self.term_arg},{self.value_arg})"
    def __repr__(self): return f"ArgPredicate({repr(self.n_arg)},{repr(self.term_arg)},{repr(self.value_arg)})"


class UnivPredicate:
    """=../2 (univ): Term =.. List"""
    def __init__(self, term_arg, list_arg):
        self.term_arg = term_arg
        self.list_arg = list_arg
        self.pred = "=.."

    @staticmethod
    def _python_list_to_prolog_list(elements):
        if not elements:
            return Atom("[]")
        current_list = Atom("[]")
        for element in reversed(elements):
            current_list = Term(Atom("."), [element, current_list])
        return current_list

    @staticmethod
    def _prolog_list_to_python_list(prolog_list_term, runtime, bindings):
        elements = []
        current = runtime.logic_interpreter.dereference(prolog_list_term, bindings)
        while isinstance(current, Term) and current.functor.name == "." and len(current.args) == 2:
            elements.append(current.args[0])
            current = runtime.logic_interpreter.dereference(current.args[1], bindings)
        
        if not (isinstance(current, Atom) and current.name == "[]"):
            # Improper list or non-list tail
            raise PrologError("=../2: List argument is not a proper list.")
        return elements

    def execute(self, runtime, bindings):
        d_term = runtime.logic_interpreter.dereference(self.term_arg, bindings)
        d_list = runtime.logic_interpreter.dereference(self.list_arg, bindings)

        # Mode 1: Analysis (Term is instantiated, List is variable or to be unified)
        if not isinstance(d_term, Variable):
            prolog_representation_list = None
            if isinstance(d_term, (Atom, Number)): # Atomic term
                prolog_representation_list = UnivPredicate._python_list_to_prolog_list([d_term])
            elif isinstance(d_term, Term): # Compound term
                py_list = [d_term.functor] + d_term.args
                prolog_representation_list = UnivPredicate._python_list_to_prolog_list(py_list)
            else: # Should not happen for valid Prolog terms if not Variable
                raise PrologError(f"=../2: Cannot analyze term of type {type(d_term)}")

            if prolog_representation_list:
                s, b = runtime.logic_interpreter.unify(self.list_arg, prolog_representation_list, bindings)
                if s:
                    yield b
        
        # Mode 2: Construction (List is instantiated, Term is variable or to be unified)
        elif not isinstance(d_list, Variable): # List is instantiated
            try:
                py_list = UnivPredicate._prolog_list_to_python_list(d_list, runtime, bindings)
            except PrologError: # Improper list from helper
                return # Fail

            if not py_list: # Empty list is invalid for construction
                # raise PrologError("=../2: List cannot be empty for construction.")
                return # Fail

            functor_element = py_list[0]
            # Functor element must be dereferenced further in case it's a variable from the list itself
            functor_element = runtime.logic_interpreter.dereference(functor_element, bindings)


            constructed_term = None
            if len(py_list) == 1: # e.g., Term =.. [my_atom] or Term =.. [123]
                if isinstance(functor_element, (Atom, Number)):
                    constructed_term = functor_element
                else: # Functor for arity 0 must be atomic
                    # raise PrologError("=../2: Head of single-element list for construction must be an atom or number.")
                    return # Fail
            else: # e.g., Term =.. [f, a, b]
                if not isinstance(functor_element, Atom):
                    # raise PrologError("=../2: Head of multi-element list for construction must be an atom.")
                    return # Fail
                args = py_list[1:]
                constructed_term = Term(functor_element, args)
            
            if constructed_term is not None:
                s, b = runtime.logic_interpreter.unify(self.term_arg, constructed_term, bindings)
                if s:
                    yield b
        # else: Both are variables, or insufficient instantiation. Standard Prolog might error or fail.
        # Here, we implicitly fail if neither mode matches.
        # Consider instantiation errors for specific cases like Term=Var, List=Var.

    def __str__(self): return f"{self.term_arg} =.. {self.list_arg}"
    def __repr__(self): return f"UnivPredicate({repr(self.term_arg)},{repr(self.list_arg)})"
