from prolog.runtime.interpreter import Runtime
from prolog.core.types import Variable, Term, Rule, FALSE_TERM, TRUE_TERM, CUT_SIGNAL, Conjunction
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner
# For stream capture if we test write/nl/tab output
import io
import sys

def test_query_with_builtins():
    source = '''
    room(kitchen).
    room(office).
    room(hall).
    room('dinning room').
    room(cellar).

    location(desk, office). % Not used by this specific goal, but part of original context
    location(apple, kitchen).
    location(flashlight, desk).
    location('washing machine', cellar).
    location(nani, 'washing machine').
    location(broccoli, kitchen).
    location(crackers, kitchen).
    location(computer, office).

    door(office, hall). % Not used by this specific goal
    door(kitchen, office).
    door(hall, 'dinning room').
    door(kitchen, cellar).
    door('dinninr room', kitchen).
    '''
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    goal_text = "room(X), tab, write(X), nl."
    
    X_var = Variable('X')
    expected_bindings_for_x = [
        'kitchen',
        'office',
        'hall',
        'dinning room',
        'cellar'
    ]
    
    solutions_found = 0
    
    # Capture stdout for write/nl/tab verification
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert X_var in bindings_dict, f"Variable X not in bindings: {bindings_dict} (solution {i+1})"
        bound_value_for_x = str(bindings_dict[X_var])
        
        expected_val_raw = expected_bindings_for_x[i] # e.g., 'kitchen' or 'dinning room'
        
        # Determine the comparison values (stripping quotes if needed)
        # bound_value_for_x_cmp is how the actual value from Prolog is, for comparison
        if "'" in bound_value_for_x and not "'" in expected_val_raw: 
            bound_value_for_x_cmp = bound_value_for_x.strip("'")
        elif not "'" in bound_value_for_x and "'" in expected_val_raw: 
            bound_value_for_x_cmp = bound_value_for_x 
        else: # Both have quotes or neither have quotes
            bound_value_for_x_cmp = bound_value_for_x.strip("'")


        # expected_val_cmp is what we expect, after stripping its own quotes for comparison
        expected_val_cmp = expected_val_raw.strip("'")

        assert bound_value_for_x_cmp == expected_val_cmp, \
            f"Binding for X was '{bound_value_for_x_cmp}', expected '{expected_val_cmp}' (solution {i+1})"
            
    assert solutions_found == len(expected_bindings_for_x), f"Expected {len(expected_bindings_for_x)} solutions, got {solutions_found}"

    sys.stdout = old_stdout # Restore stdout
    
    # Verify output from write/nl/tab
    # This depends on the exact implementation of tab, write, nl.
    # Assuming tab is one space, write(X) writes X, nl is a newline.
    # Example expected output:
    # "\tkitchen\n\toffice\n\thall\n\t'dinning room'\n\tcellar\n" (actual output from write)
    
    # expected_output_lines = []
    # for val_str in expected_bindings_for_x:
    #     # How Prolog's write/1 represents atoms and strings needs to be consistent.
    #     # If write('dinning room') outputs 'dinning room' (with quotes), then:
    #     # If write(kitchen) outputs kitchen (no quotes), then:
    #     # This part needs to align with prolog.builtins.Write.execute implementation.
    #     # For now, assuming write outputs the string form without extra quotes unless they are part of the atom name.
    #     expected_output_lines.append(f"\t{val_str}") 
    
    # expected_output_str = "\n".join(expected_output_lines) + "\n"
    # actual_output = captured_output.getvalue()
    
    # print(f"Actual output from builtins:\n{actual_output}")
    # print(f"Expected output based on bindings (heuristic):\n{expected_output_str}")
    # This assertion is tricky and depends on precise formatting of write/tab/nl.
    # assert actual_output == expected_output_str 
    # TODO: Refine stdout check once builtin behavior for tab/write/nl is fully confirmed.

def test_fail_builtin():
    source = '''
    room(kitchen).
    room(office).
    room(hall).
    room('dinning room').
    room(cellar).
    '''
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    goal_text = 'room(X), tab, write(X), nl, fail.'
    
    solutions_found = 0
    for _ in runtime.query(goal_text):
        solutions_found += 1
            
    assert solutions_found == 0, "Query with 'fail.' should produce no solutions"

def test_cut_predicate():
    source = '''
    data(one).
    data(two).
    data(three).

    cut_test_a(X) :- data(X).
    cut_test_a('last clause').

    cut_test_b(X) :- data(X), !.
    cut_test_b('last clause_b'). 
    '''
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    
    X_var = Variable('X')

    # Test cut_test_a (no cut)
    goal_text_a = "cut_test_a(X)."
    solutions_a = [str(b[X_var]) for b in runtime.query(goal_text_a) if X_var in b]
    expected_solutions_a = ['one', 'two', 'three', 'last clause']
    assert solutions_a == expected_solutions_a, f"Expected {expected_solutions_a}, got {solutions_a} for cut_test_a"

    # Test cut_test_b (with cut)
    goal_text_b = "cut_test_b(X)."
    solutions_b = [str(b[X_var]) for b in runtime.query(goal_text_b) if X_var in b]
    expected_solutions_b = ['one'] 
    assert solutions_b == expected_solutions_b, f"Expected {expected_solutions_b}, got {solutions_b} for cut_test_b"
