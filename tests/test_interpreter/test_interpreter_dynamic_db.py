from prolog.runtime.interpreter import Runtime
from prolog.core.types import Variable, Term, Rule, FALSE_TERM, TRUE_TERM, Conjunction
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner

def test_insert_rule_left(): # asserta (direct runtime call)
    initial_rules_text = '''
    block(a).
    room(kitchen).
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    original_rule_count = len(runtime.rules)

    # New rule: room(bathroom).
    new_rule_head = Term('room', Term('bathroom'))
    # Facts are rules with TRUE_TERM as their body
    new_rule_obj = Rule(new_rule_head, TRUE_TERM) 
    
    runtime.asserta(new_rule_obj)
    
    assert len(runtime.rules) == original_rule_count + 1
    # asserta adds to the beginning of the database (or predicate-specific list)
    # For simplicity, assuming it's added to the global list's start for now.
    # Rule.__eq__ needs to be reliable for this comparison.
    assert runtime.rules[0] == new_rule_obj 

    # Verify the new rule is queryable
    solutions = list(runtime.query("room(bathroom)."))
    assert len(solutions) > 0, "Asserted rule room(bathroom) should be queryable"
    
    # Verify order if possible (bathroom should be found before kitchen for room(X))
    X_var = Variable('X')
    room_solutions = [str(b[X_var]) for b in runtime.query("room(X).") if X_var in b]
    # Assuming 'bathroom' was added before 'kitchen' in the effective rule list for 'room'
    expected_room_order = ['bathroom', 'kitchen'] 
    assert room_solutions == expected_room_order, f"Expected order {expected_room_order}, got {room_solutions}"


def test_insert_rule_right(): # assertz (direct runtime call)
    initial_rules_text = '''
    block(a).
    room(kitchen).
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    original_rule_count = len(runtime.rules)

    new_rule_head = Term('room', Term('bathroom'))
    new_rule_obj = Rule(new_rule_head, TRUE_TERM)
    
    runtime.assertz(new_rule_obj)
    
    assert len(runtime.rules) == original_rule_count + 1
    # assertz adds to the end
    assert runtime.rules[-1] == new_rule_obj

    solutions = list(runtime.query("room(bathroom)."))
    assert len(solutions) > 0, "Asserted rule room(bathroom) should be queryable"

    # Verify order (kitchen should be found before bathroom for room(X))
    X_var = Variable('X')
    room_solutions = [str(b[X_var]) for b in runtime.query("room(X).") if X_var in b]
    expected_room_order = ['kitchen', 'bathroom']
    assert room_solutions == expected_room_order, f"Expected order {expected_room_order}, got {room_solutions}"


def test_remove_rule_fact(): # retract (direct runtime call for a fact)
    initial_rules_text = '''
    block(a).
    room(kitchen).
    room(hallway).
    room(bathroom). 
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    original_rule_count = len(runtime.rules)

    # Verify 'room(bathroom)' is initially queryable
    assert len(list(runtime.query("room(bathroom)."))) > 0

    # Rule to retract: room(bathroom).
    # This can be represented as a Term or a Rule object.
    # Runtime.retract should be able to take a Term (head) to find matching facts/rules.
    rule_to_retract_template = Term('room', Term('bathroom'))
    
    retracted_count = runtime.retract(rule_to_retract_template) # Assuming retract returns number of rules removed or True/False
    # For simplicity, let's assume it returns True if at least one rule was retracted.
    # Or, if it returns the rule object, we can check that.
    # The original test checked for a boolean.
    assert retracted_count is True or retracted_count > 0, "retract should indicate success"
    
    # If retract returns the number of rules removed:
    # assert retracted_count == 1 
    # If it returns True/False:
    # assert retracted_count is True

    assert len(runtime.rules) == original_rule_count - 1
    
    # Verify 'room(bathroom)' is no longer queryable
    assert len(list(runtime.query("room(bathroom)."))) == 0, "Retracted rule should not be queryable"
    
    # Verify other rules are still there
    assert len(list(runtime.query("room(kitchen)."))) > 0
    assert len(list(runtime.query("room(hallway)."))) > 0


def test_remove_complex_rule(): # retract (direct runtime call for a rule with body)
    initial_rules_text = '''
    here(kitchen).
    location(table, kitchen).
    take(X) :- here(Y), location(X, Y).
    take(pen). % Another rule for take/1
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    original_rule_count = len(runtime.rules)

    # Verify 'take(table)' is initially queryable via the complex rule
    assert len(list(runtime.query("take(table)."))) > 0
    # Verify 'take(pen)' is also queryable
    assert len(list(runtime.query("take(pen)."))) > 0


    # Rule to retract: take(X) :- here(Y), location(X, Y).
    # To retract a specific rule, we need to provide a template that unifies with it.
    # This usually means providing the head and optionally the body.
    # If Runtime.retract can match based on head unification:
    # template_to_retract = Term('take', Variable('AnyX')) 
    # This would retract the first rule matching take(X), which could be the complex one or take(pen).
    
    # To be specific, we need to construct a Rule object for retraction if the retract
    # implementation supports full rule unification.
    # head_take = Term('take', Variable('X_template'))
    # body_take = Conjunction(Term('here', Variable('Y_template')), Term('location', Variable('X_template'), Variable('Y_template')))
    # rule_obj_to_retract = Rule(head_take, body_take)
    # retracted = runtime.retract(rule_obj_to_retract)

    # For now, let's assume retract(Term) retracts the first rule whose head unifies with Term.
    # To ensure we retract the complex rule and not `take(pen).` if it came first,
    # we might need a more specific template or rely on the current order.
    # Let's assume the complex rule is the first `take/1` rule.
    # The original test used `Term('take', Variable('AnyX'))`
    template_to_retract = Term('take', Variable('AnyX')) 

    retracted_count = runtime.retract(template_to_retract) # This will retract the first matching rule for take/1.
    assert retracted_count is True or retracted_count > 0
    
    # Assuming the complex rule was indeed the first one for take/1 and got retracted.
    assert len(runtime.rules) == original_rule_count - 1
    
    # 'take(table)' should no longer be provable if the complex rule was removed.
    assert len(list(runtime.query("take(table)."))) == 0
    # 'take(pen)' should still be provable if it wasn't the one retracted.
    # This depends on the retract behavior (which one it picks if multiple match).
    # If `take(pen).` was defined after the complex rule, it should remain.
    # If `retract` removes ALL matching, then this assertion would be different.
    # Standard retract typically removes the first one.
    # Let's verify the remaining rules for take/1.
    X_var = Variable('X')
    take_solutions = [str(b[X_var]) for b in runtime.query("take(X).") if X_var in b]
    assert 'table' not in take_solutions
    # If take(pen) was the second rule, it should still be there.
    # This assertion needs to be robust to the order of rules in the source.
    # If the complex rule was `take(X) :- ...` and `take(pen).` was also present,
    # and `retract(take(X))` was called, it's ambiguous which one is removed without more info
    # on how rules are ordered and matched by retract.
    # For this test to be robust, we should ensure the complex rule is uniquely identifiable
    # or that we retract it specifically.
    # The original test implies `take(table)` becomes unprovable.

def test_retract_rule_builtin_context(): # retract used within a rule
    initial_rules_text = '''
    here(kitchen).
    here(office).
    disappear(Place) :- retract(here(Place)). 
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    # Initial rules: here(kitchen), here(office), disappear(P) :- retract(here(P)).
    original_rule_count = len(runtime.rules) 

    # Verify here(kitchen) and here(office) are present
    assert len(list(runtime.query("here(kitchen)."))) > 0
    assert len(list(runtime.query("here(office)."))) > 0
    
    # Execute disappear(kitchen).
    solutions_disappear = list(runtime.query("disappear(kitchen)."))
    assert len(solutions_disappear) > 0, "disappear(kitchen). should succeed"
    
    # After disappear(kitchen), here(kitchen) should be gone.
    assert len(list(runtime.query("here(kitchen)."))) == 0
    # here(office) should still be present.
    assert len(list(runtime.query("here(office)."))) > 0
    
    # One rule (here(kitchen)) was removed.
    assert len(runtime.rules) == original_rule_count - 1

def test_retract_and_asserta_rule_builtin_context():
    initial_rules_text = '''
    here(kitchen).
    move(NewPlace) :- retract(here(_)), asserta(here(NewPlace)).
    '''
    # This rule is problematic: retract(here(_)) will retract the first `here` fact.
    # If there are multiple, it's non-deterministic which one `here(_)` refers to
    # unless `retract/1` is defined to backtrack and retract all on redo (which is standard).
    # Let's assume it retracts the first one it finds.
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    # here(kitchen), move(NP) :- ...
    original_rule_count = len(runtime.rules) 

    # Verify here(kitchen)
    assert len(list(runtime.query("here(kitchen)."))) > 0
    
    # Execute move(office).
    # 1. retract(here(_)) will retract here(kitchen).
    # 2. asserta(here(office)) will add here(office) at the beginning.
    solutions_move = list(runtime.query("move(office)."))
    assert len(solutions_move) > 0, "move(office). should succeed"
    
    # here(kitchen) should be gone.
    assert len(list(runtime.query("here(kitchen)."))) == 0
    # here(office) should be present.
    assert len(list(runtime.query("here(office)."))) > 0
    
    # The number of rules should remain the same (one fact retracted, one fact asserted).
    # The `move` rule itself is unchanged.
    assert len(runtime.rules) == original_rule_count 

    # If we call move(pantry) again:
    # 1. retract(here(_)) will retract here(office) (as it's now the first/only `here` fact).
    # 2. asserta(here(pantry)) will add here(pantry).
    solutions_move_again = list(runtime.query("move(pantry)."))
    assert len(solutions_move_again) > 0, "move(pantry). should succeed again"
    assert len(list(runtime.query("here(office)."))) == 0
    assert len(list(runtime.query("here(pantry)."))) > 0
    assert len(runtime.rules) == original_rule_count


def test_assertz_rule_builtin_context():
    initial_rules_text = '''
    block(a).
    appear(Item) :- assertz(block(Item)).
    '''
    tokens = Scanner(initial_rules_text).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)
    # block(a), appear(I) :- ...
    original_rule_count = len(runtime.rules)

    # Execute appear(b).
    solutions_appear = list(runtime.query("appear(b)."))
    assert len(solutions_appear) > 0, "appear(b). should succeed"
    
    # block(b) should be present.
    assert len(list(runtime.query("block(b)."))) > 0
    # A new rule block(b) was added.
    assert len(runtime.rules) == original_rule_count + 1

    # Check order: block(a) then block(b)
    X_var = Variable('X')
    results = [str(b[X_var]) for b in runtime.query("block(X).") if X_var in b]
    assert results == ['a', 'b'], f"Expected order ['a', 'b'], got {results}"

    # Execute appear(c).
    solutions_appear_c = list(runtime.query("appear(c)."))
    assert len(solutions_appear_c) > 0, "appear(c). should succeed"
    assert len(list(runtime.query("block(c)."))) > 0
    assert len(runtime.rules) == original_rule_count + 2
    results_after_c = [str(b[X_var]) for b in runtime.query("block(X).") if X_var in b]
    assert results_after_c == ['a', 'b', 'c'], f"Expected order ['a', 'b', 'c'], got {results_after_c}"
