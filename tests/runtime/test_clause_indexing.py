from pyprolog import Runtime
from pyprolog.core.types import Atom, Number, Variable


class TestClauseIndexing:
    def test_cut_order_preserved_with_arg0_indexing(self):
        runtime = Runtime()
        runtime.add_rule("p(a, 1).")
        runtime.add_rule("p(a, 2) :- !.")
        runtime.add_rule("p(a, 3).")
        runtime.add_rule("p(b, 4).")

        results = runtime.query("p(a, X).")
        values = [list(result.values())[0] for result in results]

        assert values == [Number(1), Number(2)]

    def test_fallback_for_variable_arg0(self):
        runtime = Runtime()
        runtime.add_rule("p(a, 1).")
        runtime.add_rule("p(b, 2).")
        runtime.add_rule("p(c, 3).")

        results = runtime.query("p(X, Y).")
        values = [(res[Variable("X")], res[Variable("Y")]) for res in results]

        assert values == [
            (Atom("a"), Number(1)),
            (Atom("b"), Number(2)),
            (Atom("c"), Number(3)),
        ]

    def test_secondary_index_preserves_consult_order(self):
        runtime = Runtime()
        runtime.add_rule("p(a, 1).")
        runtime.add_rule("p(a, 2).")
        runtime.add_rule("p(a, 3).")

        results = runtime.query("p(a, X).")
        values = [list(result.values())[0] for result in results]

        assert values == [Number(1), Number(2), Number(3)]

    def test_secondary_index_miss_falls_back_to_primary(self):
        runtime = Runtime()
        runtime.add_rule("p(b, 1).")

        results = runtime.query("p(a, X).")

        assert list(results) == []
