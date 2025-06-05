import pytest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Term, Variable, Atom


class TestListOperations:
    @pytest.fixture(autouse=True)
    def setup_runtime(self):
        self.runtime = Runtime()
        # No user-defined rules needed for member/2 as it's a built-in
        # self.runtime.rules.clear() # Not strictly necessary if only built-ins are tested
        # if hasattr(self.runtime, 'logic_interpreter') and self.runtime.logic_interpreter:
        #     self.runtime.logic_interpreter.rules.clear()

    def assertQuerySolutions(self, query_string, expected_solutions_list, msg=None):
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(
            f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})",
            flush=True,
        )

        processed_solutions = []
        for sol_dict in solutions:
            processed_sol = {}
            for var_key, value in sol_dict.items():
                if isinstance(var_key, Variable):
                    processed_sol[var_key.name] = value
                else:
                    processed_sol[str(var_key)] = value
            processed_solutions.append(frozenset(processed_sol.items()))

        processed_expected_solutions = []
        for expected_sol_dict in expected_solutions_list:
            processed_expected_sol = {}
            for var_name_str, expected_value in expected_sol_dict.items():
                processed_expected_sol[var_name_str] = expected_value
            processed_expected_solutions.append(
                frozenset(processed_expected_sol.items())
            )

        assert len(processed_solutions) == len(processed_expected_solutions), (
            msg
            or f"Query '{query_string}' expected {len(processed_expected_solutions)} solutions, got {len(processed_solutions)}. Solutions: {solutions}"
        )

        for expected_fs in processed_expected_solutions:
            assert expected_fs in processed_solutions, (
                msg
                or f"Query '{query_string}': Expected solution {dict(expected_fs)} not found in actual solutions {solutions}."
            )

        for actual_fs in processed_solutions:
            assert actual_fs in processed_expected_solutions, (
                msg
                or f"Query '{query_string}': Actual solution {dict(actual_fs)} was not expected. Expected: {expected_solutions_list}."
            )

    def assertQueryTrue(self, query_string, expected_bindings_list=None, msg=None):
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(
            f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})",
            flush=True,
        )

        if expected_bindings_list is None:
            assert len(solutions) >= 1, (
                msg
                or f"Query '{query_string}' should succeed but failed (no solutions)."
            )
        elif not expected_bindings_list:
            assert len(solutions) >= 1, (
                msg
                or f"Query '{query_string}' should succeed but failed (no solutions)."
            )
        else:
            assert len(solutions) >= 1, (
                msg
                or f"Query '{query_string}' expected at least one solution, got {len(solutions)}."
            )
            first_solution_bindings = solutions[0]
            expected_first_solution_bindings = expected_bindings_list[0]

            processed_first_solution = {}
            for var_key, value in first_solution_bindings.items():
                if isinstance(var_key, Variable):
                    processed_first_solution[var_key.name] = value
                else:
                    processed_first_solution[str(var_key)] = value

            for (
                var_name_str,
                expected_value,
            ) in expected_first_solution_bindings.items():
                actual_value = processed_first_solution.get(var_name_str)
                assert actual_value == expected_value, (
                    msg
                    or f"Query '{query_string}', first solution: Var '{var_name_str}' expected <{expected_value}>, got <{actual_value}>."
                )

    def assertQueryFalse(self, query_string, msg=None):
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(
            f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})",
            flush=True,
        )
        assert len(solutions) == 0, (
            msg
            or f"Query '{query_string}' should fail but succeeded with {len(solutions)} solution(s)."
        )

    # --- Test Cases for member/2 ---

    def test_member_inspection_mode(self):
        """Test member/2 in inspection mode (element is ground)."""
        self.assertQueryTrue("member(a, [a,b,c])", [{}])
        self.assertQueryTrue("member(b, [a,b,c])", [{}])
        self.assertQueryTrue("member(c, [a,b,c])", [{}])
        self.assertQueryFalse("member(x, [a,b,c])")
        self.assertQueryFalse("member(a, [])")  # Empty list
        self.assertQueryTrue("member(a, [x,a,y])", [{}])
        self.assertQueryTrue("member([1], [[1],[2]])", [{}])  # Element is a list
        self.assertQueryFalse("member([3], [[1],[2]])")

    def test_member_generation_mode(self):
        """Test member/2 in generation mode (element is a variable)."""
        self.assertQuerySolutions(
            "member(X, [a,b,c])", [{"X": Atom("a")}, {"X": Atom("b")}, {"X": Atom("c")}]
        )
        self.assertQuerySolutions("member(X, [a])", [{"X": Atom("a")}])
        self.assertQuerySolutions(
            "member(X, [a,a,b])",
            [  # Check for duplicate elements
                {"X": Atom("a")},  # First 'a'
                {"X": Atom("a")},  # Second 'a'
                {"X": Atom("b")},
            ],
        )
        self.assertQueryFalse("member(X, [])")

    def test_member_list_argument_types(self):
        """Test member/2 with various types for the list argument."""
        # Case 4: Second argument is an unbound variable
        # Standard Prolog would raise an instantiation error.
        # Current MemberPredicate might fail quietly or loop if not careful.
        # Based on implementation, it dereferences List, if it's Var, loop condition fails.
        self.assertQueryFalse("member(a, L)")
        self.assertQueryFalse("member(X, L)")

        # Case 5: Second argument is a non-list atom or number
        self.assertQueryFalse("member(a, not_a_list)")
        self.assertQueryFalse("member(a, 123)")

        # Case 6: Second argument is a partial list with non-list tail
        # member(a, [a,b|c]) should find 'a'.
        self.assertQueryTrue("member(a, [a,b|c])", [{}])
        # member(b, [a,b|c]) should find 'b'.
        self.assertQueryTrue("member(b, [a,b|c])", [{}])
        # member(c, [a,b|c]) should fail as 'c' is not an element reached by walking .(_,_)
        self.assertQueryFalse("member(c, [a,b|c])")
        # member(X, [a,b|c]) should yield X=a, then X=b
        self.assertQuerySolutions(
            "member(X, [a,b|c])", [{"X": Atom("a")}, {"X": Atom("b")}]
        )
        # member(X, [a|b])
        self.assertQuerySolutions("member(X, [a|b])", [{"X": Atom("a")}])

    def test_member_element_and_list_vars(self):
        """Test member/2 where elements and list items are variables."""
        # Case 7: Element and list items are variables
        # member(X, [Y,Z]), Y=a, Z=b -> X=a; X=b
        self.runtime.add_rule("item(a).")  # Define some atoms to bind Y, Z to
        self.runtime.add_rule("item(b).")
        # This test is tricky because we need to set up Y and Z.
        # A direct query "member(X, [Y,Z]), Y=a, Z=b." involves conjunction.
        # For now, let's test with concrete values that were variables.
        self.assertQuerySolutions(
            "member(X, [a,b])", [{"X": Atom("a")}, {"X": Atom("b")}]
        )  # Same as generation

        # member(a, [X,b]), X=a. -> This requires X to be bound by unify within member.
        # This is more about how unification works with the yielded results.
        # If X is unified with 'a' by member, then member(a, [a,b]) is true.
        solutions = self.runtime.query(
            "member(a, [X,b])"
        )  # X will be 'a' for the first solution
        # Expected: X=a (solution 1), X=b (no, because 'a' != 'b')
        # Actually, member(a, [X,b])
        # 1. unify(a, X) -> X=a. env={X:a}. yield env. member(a,[a,b]) -> solution {X:a}
        # 2. unify(a, b) -> fails.
        self.assertQuerySolutions("member(a, [X,b])", [{"X": Atom("a")}])

        # member(a, [X,Y]), X=a, Y=b -> X=a (from first element)
        # This is more complex: member(a, [X,Y])
        # 1. unify(a,X) -> X=a. yield env1={X:a, Y:Y}.
        # 2. unify(a,Y) -> Y=a. yield env2={X:X, Y:a}.
        # The assertQuerySolutions needs to handle these distinct solutions.
        self.assertQuerySolutions(
            "member(a, [X,Y])",
            [
                {"X": Atom("a"), "Y": Variable("Y")},
                {"X": Variable("X"), "Y": Atom("a")},
            ],
        )

        # Test with list elements being variables that get bound
        # member(Val, [Val1, Val2]), Val1 = foo, Val2 = bar.
        # This is essentially member(Val, [foo,bar]).
        self.assertQuerySolutions(
            "member(Val, [foo,bar])", [{"Val": Atom("foo")}, {"Val": Atom("bar")}]
        )

    def test_member_complex_elements(self):
        """Test member/2 with complex terms as elements."""
        self.assertQueryTrue("member(f(1), [a, f(1), b])", [{}])
        self.assertQueryFalse("member(f(2), [a, f(1), b])")

        # Generation with complex terms
        # member(X, [f(a), g(b)]) -> X=f(a); X=g(b)
        self.assertQuerySolutions(
            "member(X, [f(a), g(b)])",
            [{"X": Term(Atom("f"), [Atom("a")])}, {"X": Term(Atom("g"), [Atom("b")])}],
        )

        # Unification with complex terms containing variables
        # member(f(A), [f(x), g(y)]) -> A=x (solution 1)
        # member(f(A), [g(y), f(x)]) -> A=x (solution 1, but after checking g(y))
        solutions = self.runtime.query("member(f(A), [f(x), g(y)])")
        assert len(solutions) == 1
        assert solutions[0].get(Variable("A")) == Atom("x")

        solutions2 = self.runtime.query("member(f(A), [g(y), f(x)])")
        assert len(solutions2) == 1
        assert solutions2[0].get(Variable("A")) == Atom("x")

        # member(Term, [item(Val)]), Term = item(foo).
        # This is effectively member(item(foo), [item(Val)])
        # 1. unify(item(foo), item(Val)) -> Val=foo. Yield env with Val=foo.
        self.assertQuerySolutions(
            "member(item(foo), [item(Val)])", [{"Val": Atom("foo")}]
        )

    # --- Test Cases for append/3 ---
    def test_append_predicate(self):
        # Helper to create list terms for expected results
        def make_list(*elements):
            res = Atom("[]")
            for el in reversed(elements):
                # Assume elements are already PrologType objects (Atom, Number, Variable, Term)
                res = Term(Atom("."), [el, res])
            return res

        # 1. Concatenation mode: append(L1, L2, L3_var)
        self.assertQueryTrue(
            "append([a,b], [c,d], L3)",
            [{"L3": make_list(Atom("a"), Atom("b"), Atom("c"), Atom("d"))}],
        )
        self.assertQueryTrue(
            "append([], [a,b], L3)", [{"L3": make_list(Atom("a"), Atom("b"))}]
        )
        self.assertQueryTrue(
            "append([a,b], [], L3)", [{"L3": make_list(Atom("a"), Atom("b"))}]
        )
        self.assertQueryTrue("append([], [], L3)", [{"L3": Atom("[]")}])

        # 2. Inspection mode: append(L1, L2, L3_ground)
        self.assertQueryTrue("append([a,b], [c,d], [a,b,c,d])", [{}])
        self.assertQueryFalse("append([a,b], [c,d], [a,b,c,e])")
        self.assertQueryFalse("append([a,b], [c,d], [a,b,d,c])")  # Order matters
        self.assertQueryTrue("append([], [a], [a])", [{}])
        self.assertQueryTrue("append([a], [], [a])", [{}])
        self.assertQueryTrue("append([], [], [])", [{}])
        self.assertQueryFalse("append([a], [b], [a])")

        # 3. Splitting mode: append(L1_var, L2_var, L3_ground) - expecting all solutions
        # append(L1, L2, [a,b,c])
        # L1=[], L2=[a,b,c]
        # L1=[a], L2=[b,c]
        # L1=[a,b], L2=[c]
        # L1=[a,b,c], L2=[]
        self.assertQuerySolutions(
            "append(L1, L2, [a,b,c])",
            [
                {"L1": Atom("[]"), "L2": make_list(Atom("a"), Atom("b"), Atom("c"))},
                {"L1": make_list(Atom("a")), "L2": make_list(Atom("b"), Atom("c"))},
                {"L1": make_list(Atom("a"), Atom("b")), "L2": make_list(Atom("c"))},
                {"L1": make_list(Atom("a"), Atom("b"), Atom("c")), "L2": Atom("[]")},
            ],
        )

        self.assertQuerySolutions(
            "append(L1, L2, [a])",
            [
                {"L1": Atom("[]"), "L2": make_list(Atom("a"))},
                {"L1": make_list(Atom("a")), "L2": Atom("[]")},
            ],
        )

        self.assertQuerySolutions(
            "append(L1, L2, [])", [{"L1": Atom("[]"), "L2": Atom("[]")}]
        )

        # 4. Other modes (mixed variables and ground terms)
        self.assertQueryTrue(
            "append([a,X], [c,Y], [a,b,c,d])", [{"X": Atom("b"), "Y": Atom("d")}]
        )
        self.assertQueryTrue(
            "append(L1, [c,d], [a,b,c,d])", [{"L1": make_list(Atom("a"), Atom("b"))}]
        )
        self.assertQueryTrue(
            "append([a,b], L2, [a,b,c,d])", [{"L2": make_list(Atom("c"), Atom("d"))}]
        )
        self.assertQueryFalse(
            "append(L1, [c,e], [a,b,c,d])"
        )  # L1 would need to "fix" the mismatch

        # append(X, [b,c], [a,b,c]) -> X = [a]
        self.assertQueryTrue("append(X, [b,c], [a,b,c])", [{"X": make_list(Atom("a"))}])
        # append([a,b], Y, [a,b,c]) -> Y = [c]
        self.assertQueryTrue("append([a,b], Y, [a,b,c])", [{"Y": make_list(Atom("c"))}])

        # 5. Type errors and improper lists (current behavior)
        # Current AppendPredicate is basic, might not raise Prolog-specific errors but should fail (no solutions).
        self.assertQueryFalse("append(a, [b], L3)")  # L1 not a list
        # Standard Prolog: append([a], b, L) gives L = [a|b].
        self.assertQueryTrue(
            "append([a], b, L3)", [{"L3": Term(Atom("."), [Atom("a"), Atom("b")])}]
        )  # L2 not a list but L1 is proper

        # L3 is not a list, but L1 or L2 are variables.
        # append(L1,L2,not_a_list)
        # Clause 1: L1=[], unify(L2, not_a_list). If L2 is var, L2=not_a_list. This might succeed.
        # Expected: Should fail if standard list types are enforced.
        # Current implementation: if L1=[], L2 unifies with not_a_list.
        # If L2 is a variable, it will bind L2 to 'not_a_list'.
        # This tests if the implementation correctly handles non-list results for L3.
        # The predicate should ideally fail if L3 cannot form a list structure from L1 and L2.
        # For append([], L2, non_list_atom), if L2 is var, L2=non_list_atom.
        # This is one solution.
        self.assertQuerySolutions(
            "append(L1, L2, not_a_list)",
            [
                {"L1": Atom("[]"), "L2": Atom("not_a_list")}
                # Potentially other solutions if L1 is not empty, but they would be complex.
                # Let's restrict to a simpler case where it's more predictable.
            ],
        )
        # If L3 must be a list, then append(L1,L2,not_a_list) should always fail.
        # For now, the above tests the current flexible unification.
        # A stricter append would require a type check on L3 in some modes.

        # Improper lists for L1 or L2
        # append([a|b], [c], L3)
        # Clause 1: L1 != [].
        # Clause 2: L1 is .(a,b). H1=a, T1=b.
        #   L3 unifies with [a|T3_rec]. env_after_l3_unify has L3 = [a|T3_rec]
        #   recursive call: append(b, [c], T3_rec). This should fail as 'b' is not a list.
        self.assertQueryFalse("append([a|b], [c], L3)")

        # append([a], [c|d], L3)
        # Clause 1: L1 != [].
        # Clause 2: L1 is .(a,[]). H1=a, T1=[].
        #   L3 unifies with [a|T3_rec].
        #   recursive call: append([], [c|d], T3_rec).
        #     Clause 1 (recursive): L1_rec is []. L2_rec is [c|d]. T3_rec unifies with [c|d].
        #     So, L3 = [a | [c|d]], which is [a,c|d].
        self.assertQueryTrue(
            "append([a], [c|d], L3)",
            [
                {
                    "L3": Term(
                        Atom("."), [Atom("a"), Term(Atom("."), [Atom("c"), Atom("d")])]
                    )
                }
            ],
        )
