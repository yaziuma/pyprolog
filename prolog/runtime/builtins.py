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


class FindallPredicate(BuiltinPredicate):
    def __init__(self, template_arg: PrologType, goal_arg: PrologType, list_arg: PrologType):
        super().__init__(template_arg, goal_arg, list_arg)

    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        template = self.args[0]
        goal_to_prove = runtime.logic_interpreter.dereference(self.args[1], env) # Dereference goal in current env
        result_list_arg = self.args[2]

        # 2.a: Check if Goal is a callable term
        if isinstance(goal_to_prove, Variable): # Uninstantiated variable
            raise PrologError(f"instantiation_error: Goal in findall/3 cannot be an unbound variable. Got: {goal_to_prove}")

        # Standard Prolog: `[]` is not callable. Other atoms are callable (arity 0). Terms are callable.
        if isinstance(goal_to_prove, Atom) and goal_to_prove.name == "[]":
            raise PrologError(f"type_error(callable, {goal_to_prove}): Goal '[]' in findall/3 is not a callable term.")
        elif not isinstance(goal_to_prove, (Atom, Term)): # Numbers, strings (if distinct type) etc.
            raise PrologError(f"type_error(callable, {goal_to_prove}): Goal in findall/3 must be a callable term.")
        # At this point, goal_to_prove is an Atom (not '[]') or a Term.

        collected_templates: List[PrologType] = []

        # Create a pristine environment for proving the goal, independent of findall's own environment,
        # but able to see rules.
        # However, variables in `goal_to_prove` should be interpreted relative to `env` initially if they are shared.
        # The standard findall behavior is that `goal_to_prove` is called as if it's a normal goal.
        # Variables in `goal_to_prove` that are bound *outside* findall are part of the goal.
        # Variables *local* to `goal_to_prove` and `template` are the ones that vary per solution.

        # It's crucial that variables in `template` that are *not* part of `goal_to_prove`
        # (i.e., "free" variables in the template) are preserved as variables in each instantiated template.
        # The `instantiate_term_for_findall` helper needs to handle this correctly.
        # It should copy `template` and then apply only the bindings relevant to variables *within* that copied template
        # that were bound by the `goal_to_prove`'s solution.

        try:
            # Iterate over all solutions for the goal
            # Each solution from runtime.execute will be a BindingEnvironment
            # We need to use the original `env` because `goal_to_prove` might contain variables
            # bound in `env` that are part of the query.
            for solution_env in runtime.execute(goal_to_prove, env):
                # For each solution, instantiate the template.
                # This requires a careful instantiation that:
                # 1. Takes a *copy* of the original template.
                # 2. Applies bindings from `solution_env` to this copy.
                # 3. Variables in the template that were not bound by the goal remain as (copied) variables.
                # This is often done by "refreshing" or "skolemizing" variables from the template
                # that are *not* bound by the goal's solution, to ensure they are unique across results if needed,
                # or more simply, just applying the bindings from solution_env to a fresh copy of template.
                # A common approach: substitute known bindings from solution_env into a copy of template.

                # The logic_interpreter.instantiate_term should handle this:
                # It should take the template, and an environment (solution_env),
                # and return a new term with variables from template substituted if they are in solution_env.
                # Variables in template not in solution_env should remain as they are (or copies).
                instantiated_template = runtime.logic_interpreter.instantiate_term(template, solution_env)
                collected_templates.append(instantiated_template)

        except CutException:
            # findall/3 is transparent to cuts *within* Goal.
            # If a cut is encountered inside Goal, it prunes choices for Goal, but findall continues.
            # If a cut is trying to escape Goal (which it shouldn't if prove handles it),
            # that would be an issue for the interpreter design.
            # For now, assume prove handles cuts internally and findall just collects all results it's given.
            # If CutException propagates here, it might be an error or specific design choice.
            # Standard behavior: cut inside findall/3 does not affect choice points outside findall/3.
            # It *does* affect the solutions generated for Goal.
            pass # Let collected_templates be what we have so far if cut happened.
        except PrologError as e:
            # 2.e: If proving Goal raises an exception, findall/3 should re-throw that exception.
            raise e # Re-throw other Prolog errors.

        # 2.c & 2.d: Convert collected_templates to a Prolog list
        prolog_solutions_list: PrologType = Atom("[]")
        for item in reversed(collected_templates):
            prolog_solutions_list = Term(Atom("."), [item, prolog_solutions_list])

        # Unify the resulting Prolog list with the List argument
        unified, final_env = runtime.logic_interpreter.unify(result_list_arg, prolog_solutions_list, env)
        if unified:
            yield final_env
        # If unification fails, findall/3 fails (no solutions yielded).
        return
