from prolog.runtime.interpreter import Runtime
from prolog.core.types import Variable, Term, Rule, FALSE_TERM, TRUE_TERM, CUT_SIGNAL, Conjunction
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner
import cProfile
import functools
import pstats
import tempfile

def profile_me(func):
    @functools.wraps(func)
    def wraps(*args, **kwargs):
        file = tempfile.mktemp()
        profiler = cProfile.Profile()
        profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(file)
        metrics = pstats.Stats(file)
        metrics.strip_dirs().sort_stats('time').print_stats(100)
    return wraps

# test_simple_rule_match - MOVED to test_interpreter_basic.py
# test_query_with_multiple_results - MOVED to test_interpreter_basic.py
# test_multi_term_query - MOVED to test_interpreter_basic.py
# test_support_for_string_literals - MOVED to test_interpreter_basic.py

# test_query_with_builtins - MOVED to test_interpreter_builtins.py
# test_fail_builtin - MOVED to test_interpreter_builtins.py
# test_cut_predicate - MOVED to test_interpreter_builtins.py

# test_support_for_numbers - MOVED to test_interpreter_arithmetic.py
# test_simple_arithmetics - MOVED to test_interpreter_arithmetic.py
# test_arithmetics_with_grouping - MOVED to test_interpreter_arithmetic.py
# test_arithmetics_with_variables - MOVED to test_interpreter_arithmetic.py
# test_arithmetics_with_variables_same_as_rule - MOVED to test_interpreter_arithmetic.py

# test_logic_equal - MOVED to test_interpreter_comparison.py
# test_logic_not_equal - MOVED to test_interpreter_comparison.py
# test_logic_greater - MOVED to test_interpreter_comparison.py
# test_logic_greater_or_equal - MOVED to test_interpreter_comparison.py
# test_logic_less - MOVED to test_interpreter_comparison.py
# test_logic_less_or_equal - MOVED to test_interpreter_comparison.py

# test_insert_rule_left - MOVED to test_interpreter_dynamic_db.py
# test_insert_rule_right - MOVED to test_interpreter_dynamic_db.py
# test_remove_rule - MOVED to test_interpreter_dynamic_db.py
# test_remove_complex_rule - MOVED to test_interpreter_dynamic_db.py
# test_retract_rule_builtin_context - MOVED to test_interpreter_dynamic_db.py
# test_retract_and_asserta_rule - MOVED to test_interpreter_dynamic_db.py
# test_assertz_rule_builtin_context - MOVED to test_interpreter_dynamic_db.py

@profile_me
def test_puzzle1():
    puzzle_rules_text = '''
    exists(A, list(A, _, _, _, _)).
    exists(A, list(_, A, _, _, _)).
    exists(A, list(_, _, A, _, _)).
    exists(A, list(_, _, _, A, _)).
    exists(A, list(_, _, _, _, A)).

    rightOf(R, L, list(L, R, _, _, _)).
    rightOf(R, L, list(_, L, R, _, _)).
    rightOf(R, L, list(_, _, L, R, _)).
    rightOf(R, L, list(_, _, _, L, R)).

    middle(A, list(_, _, A, _, _)).
    first(A, list(A, _, _, _, _)).

    nextTo(A, B, list(B, A, _, _, _)).
    nextTo(A, B, list(_, B, A, _, _)).
    nextTo(A, B, list(_, _, B, A, _)).
    nextTo(A, B, list(_, _, _, B, A)).
    nextTo(A, B, list(A, B, _, _, _)).
    nextTo(A, B, list(_, A, B, _, _)).
    nextTo(A, B, list(_, _, A, B, _)).
    nextTo(A, B, list(_, _, _, A, B)).

    puzzle(Houses) :-
        exists(house(red, english, _, _, _), Houses),
        exists(house(_, spaniard, _, _, dog), Houses),
        exists(house(green, _, coffee, _, _), Houses),
        exists(house(_, ukrainian, tea, _, _), Houses),
        rightOf(house(green, _, _, _, _), house(ivory, _, _, _, _), Houses),
        exists(house(_, _, _, oldgold, snails), Houses),
        exists(house(yellow, _, _, kools, _), Houses),
        middle(house(_, _, milk, _, _), Houses),
        first(house(_, norwegian, _, _, _), Houses),
        nextTo(house(_, _, _, chesterfield, _), house(_, _, _, _, fox), Houses),
        nextTo(house(_, _, _, kools, _),house(_, _, _, _, horse), Houses),
        exists(house(_, _, orangejuice, luckystike, _), Houses),
        exists(house(_, japanese, _, parliament, _), Houses),
        nextTo(house(_, norwegian, _, _, _), house(blue, _, _, _, _), Houses),
        exists(house(_, _, water, _, _), Houses),
        exists(house(_, _, _, _, zebra), Houses).

    solution(WaterDrinker, ZebraOwner) :-
        puzzle(Houses),
        exists(house(_, WaterDrinker, water, _, _), Houses),
        exists(house(_, ZebraOwner, _, _, zebra), Houses).
    '''
    tokens = Scanner(puzzle_rules_text).tokenize()
    rules = Parser(tokens).parse_rules()
    assert rules is not None
    runtime = Runtime(rules)
    goal_text = 'solution(WaterDrinker, ZebraOwner).'
    
    water_drinker_var = Variable('WaterDrinker')
    zebra_owner_var = Variable('ZebraOwner')

    expected_solutions = [
        {'WaterDrinker': 'norwegian', 'ZebraOwner': 'japanese'}
    ]
    
    solutions_found = 0
    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert water_drinker_var in bindings_dict
        assert zebra_owner_var in bindings_dict
        
        assert str(bindings_dict[water_drinker_var]) == expected_solutions[i]['WaterDrinker']
        assert str(bindings_dict[zebra_owner_var]) == expected_solutions[i]['ZebraOwner']
            
    assert solutions_found == len(expected_solutions), f"Expected {len(expected_solutions)} solutions, got {solutions_found}"

def test_puzzle2():
    puzzle_rules_text = '''
    exists(A, list(A, _, _, _, _)).
    exists(A, list(_, A, _, _, _)).
    exists(A, list(_, _, A, _, _)).
    exists(A, list(_, _, _, A, _)).
    exists(A, list(_, _, _, _, A)).

    rightOf(R, L, list(L, R, _, _, _)).
    rightOf(R, L, list(_, L, R, _, _)).
    rightOf(R, L, list(_, _, L, R, _)).
    rightOf(R, L, list(_, _, _, L, R)).

    middle(A, list(_, _, A, _, _)).
    first(A, list(A, _, _, _, _)).

    nextTo(A, B, list(B, A, _, _, _)).
    nextTo(A, B, list(_, B, A, _, _)).
    nextTo(A, B, list(_, _, B, A, _)).
    nextTo(A, B, list(_, _, _, B, A)).
    nextTo(A, B, list(A, B, _, _, _)).
    nextTo(A, B, list(_, A, B, _, _)).
    nextTo(A, B, list(_, _, A, B, _)).
    nextTo(A, B, list(_, _, _, A, B)).

    puzzle(Houses) :-
    exists(house(red, british, _, _, _), Houses),
    exists(house(_, swedish, _, _, dog), Houses),
    exists(house(green, _, coffee, _, _), Houses),
    exists(house(_, danish, tea, _, _), Houses),
    rightOf(house(white, _, _, _, _), house(green, _, _, _, _), Houses),
    exists(house(_, _, _, pall_mall, bird), Houses),
    exists(house(yellow, _, _, dunhill, _), Houses),
    middle(house(_, _, milk, _, _), Houses),
    first(house(_, norwegian, _, _, _), Houses),
    nextTo(house(_, _, _, blend, _), house(_, _, _, _, cat), Houses),
    nextTo(house(_, _, _, dunhill, _),house(_, _, _, _, horse), Houses),
    exists(house(_, _, beer, bluemaster, _), Houses),
    exists(house(_, german, _, prince, _), Houses),
    nextTo(house(_, norwegian, _, _, _), house(blue, _, _, _, _), Houses),
    nextTo(house(_, _, _, blend, _), house(_, _, water_, _, _), Houses).

    solution(FishOwner) :-
    puzzle(Houses),
    exists(house(_, FishOwner, _, _, fish), Houses).
    '''
    tokens = Scanner(puzzle_rules_text).tokenize()
    rules = Parser(tokens).parse_rules()
    assert rules is not None
    runtime = Runtime(rules)
    goal_text = 'solution(FishOwner).'
    
    fish_owner_var = Variable('FishOwner')

    expected_solutions = [
        {'FishOwner': 'german'}
    ]
    
    solutions_found = 0
    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert fish_owner_var in bindings_dict
        assert str(bindings_dict[fish_owner_var]) == expected_solutions[i]['FishOwner']
            
    assert solutions_found == len(expected_solutions)
