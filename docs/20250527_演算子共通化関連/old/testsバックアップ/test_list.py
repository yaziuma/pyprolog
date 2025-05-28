from prolog.core.types import Term, Variable, FALSE_TERM, Rule
from prolog.runtime.interpreter import Runtime
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner

from prolog.core.types import (
    EMPTY_LIST_ATOM,
    is_list,
    is_empty_list,
    get_list_head,
    get_list_tail,
)


# Helper function to convert Python list to Prolog list Term
def py_list_to_prolog_list(elements):
    if not elements:
        return EMPTY_LIST_ATOM
    current_list_term = EMPTY_LIST_ATOM
    for element in reversed(elements):
        current_list_term = Term(".", [element, current_list_term])
    return current_list_term


# Helper function to convert Prolog list Term to Python list
def prolog_list_to_py_list(term):
    py_list = []
    current = term
    while is_list(current) and not is_empty_list(current):
        py_list.append(get_list_head(current))
        current = get_list_tail(current)
    if not is_empty_list(current):  # Improper list
        # For now, we might not perfectly handle string representation of improper lists
        # or decide how to represent them in the Python list.
        # This function primarily aims for proper lists for now.
        # raise ValueError("Cannot convert improper Prolog list to Python list directly for iteration.")
        pass  # Or append the tail as is, depending on desired behavior
    return py_list


# Helper function to get a string representation similar to Prolog for lists
def prolog_list_str(term):
    if is_empty_list(term):
        return "[]"

    elements = []
    current = term
    while is_list(current) and not is_empty_list(current):
        elements.append(str(get_list_head(current)))
        current = get_list_tail(current)

    if is_empty_list(current):  # Proper list
        return f"[{', '.join(elements)}]"
    else:  # Improper list
        return f"[{', '.join(elements)} | {str(current)}]"


def test_dot_print():
    # Test case for [A, B]
    list_ab = py_list_to_prolog_list([Term("A"), Term("B")])
    # The string representation depends on Term.__str__ and how it handles '.' functor.
    # We'll use our helper for a consistent Prolog-like list string.
    assert prolog_list_str(list_ab) == "[A, B]"

    # Test case for [A]
    list_a = py_list_to_prolog_list([Term("A")])
    assert prolog_list_str(list_a) == "[A]"

    # Test case for []
    empty_list_term = py_list_to_prolog_list([])
    assert prolog_list_str(empty_list_term) == "[]"

    # Test case for [A | B]
    list_a_bar_b = Term(".", Term("A"), Term("B"))  # Represents [A|B]
    assert prolog_list_str(list_a_bar_b) == "[A | B]"


def test_dot_iterator():
    # Represents [A, B, C] -> .(A, .(B, .(C, [])))
    prolog_list_abc = py_list_to_prolog_list([Term("A"), Term("B"), Term("C")])

    # Convert back to Python list using the new helper
    py_list_from_prolog = prolog_list_to_py_list(prolog_list_abc)
    assert py_list_from_prolog == [Term("A"), Term("B"), Term("C")]

    # Test with an empty list
    empty_prolog_list = py_list_to_prolog_list([])
    assert prolog_list_to_py_list(empty_prolog_list) == []

    # Test with an improper list [A | B] - iteration behavior might be tricky
    # For now, prolog_list_to_py_list might only return [Term('A')] if not handling improper tails for iteration
    # Or it could raise an error, or append Term('B').
    # Let's assume for now it extracts up to the non-list tail.
    improper_list = Term(".", Term("A"), Term("B"))
    # Depending on prolog_list_to_py_list implementation for improper lists:
    # Option 1: Only proper part -> [Term('A')]
    # Option 2: Include tail -> [Term('A'), Term('B')] (if tail is considered an element)
    # Option 3: Raise error
    # Current prolog_list_to_py_list will give [Term('A')] because Term('B') is not a list.
    assert prolog_list_to_py_list(improper_list) == [
        Term("A")
    ]  # Adjust if behavior is different


def test_list_with_simple_terms():
    a1_1 = Term("a1")
    a1_2 = Term("a2")

    a2_1 = Term("a1")
    a2_2 = Term("a2")

    l1 = py_list_to_prolog_list([a1_1, a1_2])  # .(a1, .(a2, []))
    l2 = py_list_to_prolog_list([a2_1, a2_2])  # .(a1, .(a2, []))

    m = l1.match(l2)
    assert m is not None and m == {}


def test_list_with_vars_and_terms():
    v_x = Variable("X")  # Renamed for clarity
    v_y = Variable("Y")  # Renamed for clarity

    t_a1 = Term("a1")  # Renamed for clarity
    t_a2 = Term("a2")  # Renamed for clarity

    l1 = py_list_to_prolog_list([v_x, v_y])  # .(X, .(Y, []))
    l2 = py_list_to_prolog_list([t_a1, t_a2])  # .(a1, .(a2, []))

    m = l1.match(l2)
    assert m is not None
    assert m.get(v_x) == t_a1
    assert m.get(v_y) == t_a2
    # For string comparison, ensure consistent formatting or compare objects
    # assert(str(m) == "{X: a1, Y: a2}") # This can be brittle

    sub = l1.substitute(m)  # Should become .(a1, .(a2, []))

    py_list_from_sub = prolog_list_to_py_list(sub)
    assert py_list_from_sub == [t_a1, t_a2]


def test_list_with_subset_vars():
    v_x = Variable("X")
    t_a2 = Term("a2")

    t_a1 = Term("a1")
    # t_a2 is already defined

    l1 = py_list_to_prolog_list([v_x, t_a2])  # .(X, .(a2, []))
    l2 = py_list_to_prolog_list([t_a1, t_a2])  # .(a1, .(a2, []))

    m = l1.match(l2)
    assert m is not None
    assert m.get(v_x) == t_a1
    # assert(str(m) == "{X: a1}")

    sub = l1.substitute(m)  # .(a1, .(a2, []))
    py_list_from_sub = prolog_list_to_py_list(sub)
    assert py_list_from_sub == [t_a1, t_a2]


def test_list_with_bar_variable_tail():
    t_a1 = Term("a1")
    t_a2 = Term("a2")
    var_x = Variable("X")

    # l1 = [a1, a2 | X] -> .(a1, .(a2, X))
    l1 = Term(".", t_a1, Term(".", t_a2, var_x))

    t_a3 = Term("a3")
    # l2 = [a1, a2, a3] -> .(a1, .(a2, .(a3, [])))
    l2 = py_list_to_prolog_list([t_a1, t_a2, t_a3])

    m = l1.match(l2)

    expected_x_binding = py_list_to_prolog_list(
        [t_a3]
    )  # X should be bound to [a3] -> .(a3, [])
    assert m is not None
    assert m.get(var_x) == expected_x_binding

    sub = l1.substitute(m)  # .(a1, .(a2, .(a3, [])))
    assert prolog_list_to_py_list(sub) == [t_a1, t_a2, t_a3]


def test_list_with_lst_vars_and_tail_vars():
    v_x = Variable("X")
    v_y = Variable("Y")
    v_t = Variable("T")

    # l1 = [X, Y | T] -> .(X, .(Y, T))
    l1 = Term(".", v_x, Term(".", v_y, v_t))

    t_a1 = Term("a1")
    t_a2 = Term("a2")
    t_a3 = Term("a3")
    # l2 = [a1, a2, a3] -> .(a1, .(a2, .(a3, [])))
    l2 = py_list_to_prolog_list([t_a1, t_a2, t_a3])

    m = l1.match(l2)
    assert m is not None
    assert m.get(v_x) == t_a1
    assert m.get(v_y) == t_a2
    assert m.get(v_t) == py_list_to_prolog_list([t_a3])  # T bound to [a3]

    sub = l1.substitute(m)  # .(a1, .(a2, .(a3, [])))
    assert prolog_list_to_py_list(sub) == [t_a1, t_a2, t_a3]


def test_list_with_head_and_tail_vars():
    var_h = Variable("H")
    var_t = Variable("T")

    # l1 = [H | T] -> .(H, T)
    l1 = Term(".", var_h, var_t)

    t_a1 = Term("a1")
    t_a2 = Term("a2")
    t_a3 = Term("a3")
    # l2 = [a1, a2, a3] -> .(a1, .(a2, .(a3, [])))
    l2 = py_list_to_prolog_list([t_a1, t_a2, t_a3])

    m = l1.match(l2)
    assert m is not None
    assert m.get(var_h) == t_a1
    assert m.get(var_t) == py_list_to_prolog_list([t_a2, t_a3])  # T bound to [a2, a3]

    sub = l1.substitute(m)  # .(a1, .(a2, .(a3, [])))
    assert prolog_list_to_py_list(sub) == [t_a1, t_a2, t_a3]


def test_list_with_head_var_and_tail_list():
    var_h = Variable("H")
    var_x = Variable("X")
    var_y = Variable("Y")

    # l1 = [H | [X, Y]] -> .(H, .(X, .(Y, [])))
    l1 = Term(".", var_h, py_list_to_prolog_list([var_x, var_y]))

    t_a1 = Term("a1")
    t_a2 = Term("a2")
    t_a3 = Term("a3")
    # l2 = [a1, a2, a3] -> .(a1, .(a2, .(a3, [])))
    l2 = py_list_to_prolog_list([t_a1, t_a2, t_a3])

    m = l1.match(l2)
    assert m is not None
    assert m.get(var_h) == t_a1
    assert m.get(var_x) == t_a2
    assert m.get(var_y) == t_a3

    sub = l1.substitute(m)  # .(a1, .(a2, .(a3, [])))
    assert prolog_list_to_py_list(sub) == [t_a1, t_a2, t_a3]


def test_parser_match_list_with_simple_terms():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    # Assuming Parser._parse_list is updated to return Term('.', ...) and EMPTY_LIST_ATOM
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([red, green, blue])
    # This should be parsed as Term('rgb', [Term('.', Term('red'), Term('.', Term('green'), Term('.', Term('blue'), EMPTY_LIST_ATOM)))])
    # We will rely on the parser to correctly parse the goal string.
    goal_text = "rgb([red, green, blue])."
    goal_tokens = Scanner(goal_text).tokenize()
    # The parser should produce the correct Term structure for the list.
    # We need to ensure the Parser's _parse_list (or equivalent) is correctly implemented.
    # For this test, we assume the parser correctly translates "[red, green, blue]"
    # into Term('.', Term('red'), Term('.', Term('green'), Term('.', Term('blue'), EMPTY_LIST_ATOM)))
    # when it's part of a larger term like rgb(...).
    goal_parser = Parser(goal_tokens)
    # _parse_term might not be the right method if goal_text is a full fact/rule.
    # If goal_text is just the term 'rgb(...)', then _parse_term is okay.
    # Let's assume goal_text is just the term for now.
    # If the parser is parsing a query like "rgb([red,green,blue]).", it might return a Rule.
    # For a query, we usually parse just the term part.
    # Let's parse the term directly for the goal.

    # Re-parsing the goal string to get the Term object
    # This assumes the parser's _parse_term can handle list syntax directly or via _parse_list
    # and constructs the correct Term structure.
    # The test `Parser(Scanner('rgb([a,b]).').tokenize())._parse_term()` should yield
    # Term('rgb', [Term('.', Term('a'), Term('.', Term('b'), EMPTY_LIST_ATOM))])
    # if the parser's list parsing is correct.

    # To construct the goal term manually for assertion:
    # fact_list_term = py_list_to_prolog_list([Term('red'), Term('green'), Term('blue')])
    # fact_term_in_rule = Term('rgb', [fact_list_term])
    # parsed_rules should contain Rule(fact_term_in_rule, TRUE_TERM)

    # For the goal:
    goal_list_elements = [Term("red"), Term("green"), Term("blue")]
    goal_list_term_for_query = py_list_to_prolog_list(goal_list_elements)
    goal_query_term = Term("rgb", [goal_list_term_for_query])

    solutions = [s for s in runtime.execute(goal_query_term) if s is not FALSE_TERM]
    assert len(solutions) > 0
    assert solutions[0] is not None  # Should find a solution (empty bindings)


def test_parser_bind_list_with_simple_terms():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb(X)
    var_x = Variable("X")
    # The parser should parse 'rgb(X).' as a query.
    # For testing runtime.execute, we need the Term part of the query.
    goal_query_term = Term("rgb", [var_x])

    expected_bound_list_term = py_list_to_prolog_list(
        [Term("red"), Term("green"), Term("blue")]
    )

    has_solution = False
    for item_bindings in runtime.execute(goal_query_term):
        if item_bindings is FALSE_TERM:
            continue
        has_solution = True
        assert isinstance(item_bindings, dict)
        bound_value_for_x = item_bindings.get(var_x)
        assert bound_value_for_x == expected_bound_list_term
        assert prolog_list_str(bound_value_for_x) == "[red, green, blue]"
        break
    assert has_solution


def test_parser_match_list_with_wrong_number_of_vars():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([R, G])
    # Parsed as: Term('rgb', [Term('.', Variable('R'), Term('.', Variable('G'), EMPTY_LIST_ATOM))])
    goal_list_term = py_list_to_prolog_list([Variable("R"), Variable("G")])
    goal_query_term = Term("rgb", [goal_list_term])

    solutions = [s for s in runtime.execute(goal_query_term) if s is not FALSE_TERM]
    assert len(solutions) == 0


def test_parser_bind_list_with_vars():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([R, G, B])
    var_r, var_g, var_b = Variable("R"), Variable("G"), Variable("B")
    goal_list_term = py_list_to_prolog_list([var_r, var_g, var_b])
    goal_query_term = Term("rgb", [goal_list_term])

    expected_bindings = {var_r: Term("red"), var_g: Term("green"), var_b: Term("blue")}

    has_solution = False
    for item_bindings in runtime.execute(goal_query_term):
        if item_bindings is FALSE_TERM:
            continue
        has_solution = True
        assert isinstance(item_bindings, dict)
        assert item_bindings.get(var_r) == expected_bindings[var_r]
        assert item_bindings.get(var_g) == expected_bindings[var_g]
        assert item_bindings.get(var_b) == expected_bindings[var_b]
        break
    assert has_solution


def test_parser_bind_list_with_bar_tail_var():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([red, green | H])
    # This should be parsed by the Parser into:
    # Term('rgb', [Term('.', Term('red'), Term('.', Term('green'), Variable('H')))])
    var_h = Variable("H")
    # Manually construct the term the parser *should* produce for "[red, green | H]"
    # This relies on the parser's _parse_list (or equivalent) handling the '|' syntax.
    # If the parser produces Term('.', Term('red'), Term('.', Term('green'), Variable('H'))), this test is valid.
    goal_list_internal_term = Term(".", Term("red"), Term(".", Term("green"), var_h))
    goal_query_term = Term("rgb", [goal_list_internal_term])

    # H should be bound to [blue], which is Term('.', Term('blue'), EMPTY_LIST_ATOM)
    expected_h_binding = py_list_to_prolog_list([Term("blue")])

    has_solution = False
    for item_bindings in runtime.execute(goal_query_term):
        if item_bindings is FALSE_TERM:
            continue
        has_solution = True
        assert isinstance(item_bindings, dict)
        bound_value_for_h = item_bindings.get(var_h)
        assert bound_value_for_h == expected_h_binding
        assert prolog_list_str(bound_value_for_h) == "[blue]"
        break
    assert has_solution


def test_parser_list_with_head_and_bar_tail_var():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([H | T])
    # Parsed as: Term('rgb', [Term('.', Variable('H'), Variable('T'))])
    var_h, var_t = Variable("H"), Variable("T")
    goal_list_internal_term = Term(".", var_h, var_t)  # Represents [H|T]
    goal_query_term = Term("rgb", [goal_list_internal_term])

    expected_h_binding = Term("red")
    expected_t_binding = py_list_to_prolog_list(
        [Term("green"), Term("blue")]
    )  # T is [green, blue]

    has_solution = False
    for item_bindings in runtime.execute(goal_query_term):
        if item_bindings is FALSE_TERM:
            continue
        has_solution = True
        assert isinstance(item_bindings, dict)
        assert item_bindings.get(var_h) == expected_h_binding
        assert item_bindings.get(var_t) == expected_t_binding
        assert prolog_list_str(item_bindings.get(var_t)) == "[green, blue]"
        break
    assert has_solution


def test_parser_list_with_head_and_bar_tail_list():
    source = """
    rgb([red, green, blue]).
    """
    tokens = Scanner(source).tokenize()
    parsed_rules = Parser(tokens).parse()
    runtime = Runtime(parsed_rules if parsed_rules else [])

    # Goal: rgb([H | [X, Y]])
    # Parsed as: Term('rgb', [Term('.', Variable('H'), Term('.', Variable('X'), Term('.', Variable('Y'), EMPTY_LIST_ATOM)))])
    var_h, var_x, var_y = Variable("H"), Variable("X"), Variable("Y")
    # Constructing [X,Y]
    tail_list_xy = py_list_to_prolog_list([var_x, var_y])
    # Constructing [H | [X,Y]]
    goal_list_internal_term = Term(".", var_h, tail_list_xy)
    goal_query_term = Term("rgb", [goal_list_internal_term])

    expected_h_binding = Term("red")
    expected_x_binding = Term("green")
    expected_y_binding = Term("blue")

    has_solution = False
    for item_bindings in runtime.execute(goal_query_term):
        if item_bindings is FALSE_TERM:
            continue
        has_solution = True
        assert isinstance(item_bindings, dict)
        assert item_bindings.get(var_h) == expected_h_binding
        assert item_bindings.get(var_x) == expected_x_binding
        assert item_bindings.get(var_y) == expected_y_binding
        break
    assert has_solution
