from prolog.core.types import Term, Variable, Atom, Number, PrologType, ListTerm
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.errors import PrologError, CutException # Assuming CutException might be relevant for some builtins
from typing import TYPE_CHECKING, Iterator, List, Any

if TYPE_CHECKING:
    from prolog.runtime.interpreter import Runtime


class BuiltinPredicate:
    def __init__(self, *args):
        self.args = args

    def execute(self, runtime: "Runtime", bindings: BindingEnvironment) -> Iterator[BindingEnvironment]:
        raise NotImplementedError


class VarPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Variable):
            yield env

class AtomPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Atom):
            yield env

class NumberPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Number):
            yield env


class FunctorPredicate(BuiltinPredicate):
    def __init__(self, term_arg: PrologType, functor_arg: PrologType, arity_arg: PrologType):
        super().__init__(term_arg, functor_arg, arity_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        term, d_functor, d_arity = self.args[0], self.args[1], self.args[2]

        term_val = runtime.logic_interpreter.dereference(term, env)
        functor_val = runtime.logic_interpreter.dereference(d_functor, env)
        arity_val = runtime.logic_interpreter.dereference(d_arity, env)

        if not isinstance(term, Variable) or (isinstance(term, Variable) and not env.is_unbound(term.name)): # Analysis
            actual_functor: PrologType
            actual_arity: Number

            if isinstance(term_val, Term):
                actual_functor = term_val.functor
                actual_arity = Number(len(term_val.args))
            elif isinstance(term_val, Atom):
                actual_functor = term_val
                actual_arity = Number(0)
            elif isinstance(term_val, Number):
                actual_functor = term_val
                actual_arity = Number(0)
            else:
                return

            unified_functor, env1 = runtime.logic_interpreter.unify(functor_val, actual_functor, env)
            if not unified_functor: return

            unified_arity, env2 = runtime.logic_interpreter.unify(arity_val, actual_arity, env1)
            if not unified_arity: return

            yield env2
            return

        elif isinstance(term, Variable) and env.is_unbound(term.name): # Synthesis
            if not isinstance(functor_val, (Atom, Number)): return
            if not isinstance(arity_val, Number) or not arity_val.value.is_integer() or arity_val.value < 0: return
            if isinstance(functor_val, Number) and arity_val.value != 0: return

            constructed_term: PrologType
            arity_int = int(arity_val.value)

            if arity_int == 0:
                constructed_term = functor_val
            else:
                if not isinstance(functor_val, Atom): return
                args = [Variable(f"_GFA{runtime.logic_interpreter._unique_var_counter + i}") for i in range(arity_int)]
                runtime.logic_interpreter._unique_var_counter += arity_int
                constructed_term = Term(functor_val, args)

            unified_term, final_env = runtime.logic_interpreter.unify(term, constructed_term, env)
            if unified_term:
                yield final_env
            return
        return


class ArgPredicate(BuiltinPredicate):
    def __init__(self, index_arg: PrologType, term_arg: PrologType, value_arg: PrologType):
        super().__init__(index_arg, term_arg, value_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        index_val = runtime.logic_interpreter.dereference(self.args[0], env)
        term_val = runtime.logic_interpreter.dereference(self.args[1], env)

        if not isinstance(index_val, Number) or not index_val.value.is_integer() or index_val.value <= 0: return
        if not isinstance(term_val, Term): return

        idx = int(index_val.value)
        if idx > len(term_val.args): return

        target_arg = term_val.args[idx - 1]
        unified, final_env = runtime.logic_interpreter.unify(self.args[2], target_arg, env)
        if unified:
            yield final_env


class UnivPredicate(BuiltinPredicate): # =../2
    def __init__(self, term_arg: PrologType, list_arg: PrologType):
        super().__init__(term_arg, list_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # Determine mode based on which argument is a variable vs instantiated
        term_is_var_unbound = isinstance(self.args[0], Variable) and env.is_unbound(self.args[0].name)
        list_is_var_unbound = isinstance(self.args[1], Variable) and env.is_unbound(self.args[1].name)

        term_val = runtime.logic_interpreter.dereference(self.args[0], env)
        list_val = runtime.logic_interpreter.dereference(self.args[1], env)

        if not term_is_var_unbound : # Analysis: Term -> List
            result_list_content: List[PrologType] = []
            if isinstance(term_val, Term):
                result_list_content.append(term_val.functor)
                result_list_content.extend(term_val.args)
            elif isinstance(term_val, (Atom, Number)):
                result_list_content.append(term_val)
            else: return

            prolog_list: PrologType = Atom("[]")
            for i in range(len(result_list_content) - 1, -1, -1):
                prolog_list = Term(Atom("."), [result_list_content[i], prolog_list])

            unified, final_env = runtime.logic_interpreter.unify(self.args[1], prolog_list, env)
            if unified: yield final_env
            return

        elif term_is_var_unbound and not list_is_var_unbound: # Synthesis: List -> Term
            if not isinstance(list_val, Term) and not (isinstance(list_val, Atom) and list_val.name == "[]"):
                 return # List must be a proper list or empty list atom

            py_list: List[PrologType] = []
            current_cell = list_val
            while isinstance(current_cell, Term) and current_cell.functor.name == "." and len(current_cell.args) == 2:
                py_list.append(runtime.logic_interpreter.dereference(current_cell.args[0], env)) # Deref elements during deconstruction
                current_cell = runtime.logic_interpreter.dereference(current_cell.args[1], env)

            if not (isinstance(current_cell, Atom) and current_cell.name == "[]"): return
            if not py_list: return

            functor_from_list = py_list[0]
            args_from_list = py_list[1:]

            if not isinstance(functor_from_list, (Atom, Number)): return
            if isinstance(functor_from_list, Number) and args_from_list: return
            if isinstance(functor_from_list, Atom) and functor_from_list.name == "[]" and args_from_list: return

            MAX_ARITY = 255
            if len(args_from_list) > MAX_ARITY: return

            constructed_term: PrologType
            if not args_from_list:
                constructed_term = functor_from_list
            else:
                if not isinstance(functor_from_list, Atom): return
                constructed_term = Term(functor_from_list, args_from_list)

            unified, final_env = runtime.logic_interpreter.unify(self.args[0], constructed_term, env)
            if unified: yield final_env
            return
        # Other cases like both vars, or both instantiated (check mode)
        elif term_is_var_unbound and list_is_var_unbound: # Both vars: Error
            return
        # If both are instantiated, it becomes a check. This is implicitly handled if neither of the above blocks execute.
        # However, the logic for analysis (Term->List) will perform the check if list_val is also instantiated.
        return


class DynamicAssertAPredicate(BuiltinPredicate):
    def __init__(self, clause_arg: PrologType):
        super().__init__(clause_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        clause_val = runtime.logic_interpreter.dereference(self.args[0], env)
        if isinstance(clause_val, Variable): return
        if not isinstance(clause_val, (Term, Atom)):return

        clause_val_as_term = Term(clause_val, []) if isinstance(clause_val, Atom) else clause_val

        # No skolemization here, vars are shared.
        if clause_val_as_term.functor.name == ":-" and len(clause_val_as_term.args) == 2:
            head = clause_val_as_term.args[0]
            body = clause_val_as_term.args[1]
            if not isinstance(head, (Term,Atom)): return # Basic head validation
            if isinstance(head, Atom): head = Term(head,[])

            runtime.rules.insert(0, Rule(head, body))
        else:
            runtime.rules.insert(0, Fact(clause_val_as_term))

        runtime.logic_interpreter.rules = runtime.rules
        yield env


class DynamicAssertZPredicate(BuiltinPredicate):
    def __init__(self, clause_arg: PrologType):
        super().__init__(clause_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        clause_val = runtime.logic_interpreter.dereference(self.args[0], env)
        if isinstance(clause_val, Variable): return
        if not isinstance(clause_val, (Term, Atom)): return

        clause_val_as_term = Term(clause_val, []) if isinstance(clause_val, Atom) else clause_val

        if clause_val_as_term.functor.name == ":-" and len(clause_val_as_term.args) == 2:
            head = clause_val_as_term.args[0]
            body = clause_val_as_term.args[1]
            if not isinstance(head, (Term,Atom)): return
            if isinstance(head, Atom): head = Term(head,[])
            runtime.rules.append(Rule(head, body))
        else:
            runtime.rules.append(Fact(clause_val_as_term))

        runtime.logic_interpreter.rules = runtime.rules
        yield env

class MemberPredicate(BuiltinPredicate):
    def __init__(self, element_arg: PrologType, list_arg: PrologType):
        super().__init__(element_arg, list_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        current_list = runtime.logic_interpreter.dereference(self.args[1], env)
        element_to_match = self.args[0] # This will be unified, use original arg

        while isinstance(current_list, Term) and \
              isinstance(current_list.functor, Atom) and \
              current_list.functor.name == '.' and \
              len(current_list.args) == 2:

            head = current_list.args[0]
            tail = current_list.args[1]

            unified, next_env = runtime.logic_interpreter.unify(element_to_match, head, env)
            if unified:
                yield next_env
            current_list = runtime.logic_interpreter.dereference(tail, env)
        return

class AppendPredicate(BuiltinPredicate):
    def __init__(self, list1_arg: PrologType, list2_arg: PrologType, list3_arg: PrologType):
        super().__init__(list1_arg, list2_arg, list3_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # --- Choice Point 1: append([], L2, L2). ---
        env_clause1 = env.copy()
        unified_l1_empty, env_clause1_after_l1 = runtime.logic_interpreter.unify(
            self.args[0], Atom("[]"), env_clause1
        )
        if unified_l1_empty:
            # L1 is []. Unify L2 and L3.
            unified_l2_l3, final_env_clause1 = runtime.logic_interpreter.unify(
                self.args[1], self.args[2], env_clause1_after_l1
            )
            if unified_l2_l3:
                yield final_env_clause1

        # --- Choice Point 2: append([H|T1], L2, [H|T3]) :- append(T1, L2, T3). ---
        env_clause2 = env.copy()

        # Create fresh variables for the components of List1 and List3 for this specific choice point
        # Use unique names to avoid clashes with variables from outer scopes in the environment.
        counter = runtime.logic_interpreter._unique_var_counter
        h1_var = Variable(f"_HAppend_{counter}")
        t1_var = Variable(f"_T1Append_{counter+1}")
        # For list3_pattern, H must be the *same* variable instance as in list1_pattern
        t3_var = Variable(f"_T3Append_{counter+2}")
        runtime.logic_interpreter._unique_var_counter += 3

        list1_pattern = Term(Atom("."), [h1_var, t1_var])

        unified_l1_cons, env_clause2_after_l1 = runtime.logic_interpreter.unify(
            self.args[0], list1_pattern, env_clause2
        )

        if unified_l1_cons:
            # L1 successfully unified with [h1_var | t1_var].
            # h1_var and t1_var are now (potentially) bound in env_clause2_after_l1.

            # List3 must match [h1_var | t3_var].
            # The h1_var in this pattern is the same Variable instance as in list1_pattern.
            # Unification will use its binding from env_clause2_after_l1.
            list3_pattern = Term(Atom("."), [h1_var, t3_var]) # uses the same h1_var Variable object

            unified_l3_cons, env_clause2_after_l3 = runtime.logic_interpreter.unify(
                self.args[2], list3_pattern, env_clause2_after_l1
            )

            if unified_l3_cons:
                # Recursively call append(t1_var, List2_original, t3_var)
                # using env_clause2_after_l3.
                # The original self.args[1] is List2.
                # t1_var and t3_var are passed (their bound values if bound, or the Variable objects themselves)
                recursive_predicate = AppendPredicate(t1_var, self.args[1], t3_var)
                yield from recursive_predicate.execute(runtime, env_clause2_after_l3)
        return # End of AppendPredicate
