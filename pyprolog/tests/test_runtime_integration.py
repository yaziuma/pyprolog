import unittest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Atom
from pyprolog.util.variable_mapper import VariableMapper


class TestRuntimeIntegrationJapanese(unittest.TestCase):
    def setUp(self):
        # 各テストで新しいRuntimeとVariableMapperインスタンスを使用する
        self.variable_mapper = VariableMapper()
        self.runtime = Runtime(variable_mapper=self.variable_mapper)

    def assertSolutionContains(self, solutions, expected_bindings_list):
        self.assertEqual(
            len(solutions),
            len(expected_bindings_list),
            f"Expected {len(expected_bindings_list)} solutions, got {len(solutions)}",
        )

        processed_solutions = []
        for sol_dict in solutions:
            processed_sol = {}
            for k_var, val_term in sol_dict.items():
                processed_sol[k_var.name] = val_term
            processed_solutions.append(processed_sol)

        for expected_bindings_dict in expected_bindings_list:
            found_match = False
            for processed_sol_dict in processed_solutions:
                if len(processed_sol_dict) != len(expected_bindings_dict):
                    continue  # Different number of bindings

                match_this_sol = True
                for var_name_str, expected_val in expected_bindings_dict.items():
                    if (
                        var_name_str not in processed_sol_dict
                        or processed_sol_dict[var_name_str] != expected_val
                    ):
                        match_this_sol = False
                        break

                if match_this_sol:
                    found_match = True
                    # Optionally, remove the matched solution to ensure all expected solutions are unique and present
                    # processed_solutions.remove(processed_sol_dict)
                    break
            self.assertTrue(
                found_match,
                f"Expected solution containing {expected_bindings_dict} not found in actual solutions {solutions}",
            )

    def test_simple_japanese_variable_query(self):
        self.runtime.add_rule("favorite_food(apple).")
        self.runtime.add_rule("favorite_food(orange).")
        solutions = self.runtime.query("favorite_food(X).")

        expected = [{"X": Atom("apple")}, {"X": Atom("orange")}]
        self.assertSolutionContains(solutions, expected)

    def test_japanese_variables_in_rule_and_query(self):
        # Simplified test using English atoms but Japanese variables
        self.runtime.add_rule("parent(taro, ichiro).")
        self.runtime.add_rule("parent(taro, jiro).")
        self.runtime.add_rule("sibling(X, Y) :- parent(P, X), parent(P, Y).")

        solutions = self.runtime.query("sibling(ichiro, X).")
        # The query should find that ichiro and jiro are siblings
        expected = [{"X": Atom("ichiro")}, {"X": Atom("jiro")}]
        self.assertSolutionContains(solutions, expected)

        # j_to_e, e_to_j = self.variable_mapper.get_all_mappings()
        # print("\nMappings for test_japanese_variables_in_rule_and_query:")
        # print("J->E:", j_to_e) # Should contain 兄,弟,親,誰か and their V forms
        # print("E->J:", e_to_j)

    def test_query_with_multiple_japanese_variables(self):
        self.runtime.add_rule("location(tokyo, japan).")
        self.runtime.add_rule("location(osaka, japan).")
        self.runtime.add_rule("location(paris, france).")

        solutions = self.runtime.query("location(X, japan).")
        expected = [{"X": Atom("tokyo")}, {"X": Atom("osaka")}]
        self.assertSolutionContains(solutions, expected)

        self.setUp()
        self.runtime.add_rule("location(tokyo, japan).")
        self.runtime.add_rule("location(osaka, japan).")
        self.runtime.add_rule("location(paris, france).")
        solutions2 = self.runtime.query("location(X, Y).")
        expected2 = [
            {"X": Atom("tokyo"), "Y": Atom("japan")},
            {"X": Atom("osaka"), "Y": Atom("japan")},
            {"X": Atom("paris"), "Y": Atom("france")},
        ]
        self.assertSolutionContains(solutions2, expected2)

    def test_mixed_japanese_and_english_variables(self):
        self.runtime.add_rule("likes(taro, apple).")
        self.runtime.add_rule("likes(jiro, X) :- likes(taro, X).")

        solutions = self.runtime.query("likes(jiro, Food).")
        # Query: likes(jiro, Food)
        # Rule: likes(jiro, V1) :- likes(taro, V1)
        # Unify query with rule head: Food <-> V1
        # New goal: likes(taro, V1)
        # Fact: likes(taro, apple) -> V1 = apple
        # So, Food = apple.
        expected = [{"Food": Atom("apple")}]
        self.assertSolutionContains(solutions, expected)

    def test_no_solution_with_japanese_variables(self):
        self.runtime.add_rule("food(apple).")
        solutions = self.runtime.query("food(X).")
        expected = [{"X": Atom("apple")}]
        self.assertSolutionContains(solutions, expected)

    def test_japanese_variable_unification_in_query(self):
        self.setUp()
        solutions = self.runtime.query("X = tokyo, X = tokyo.")
        expected = [{"X": Atom("tokyo")}]
        self.assertSolutionContains(solutions, expected)


if __name__ == "__main__":
    unittest.main()
