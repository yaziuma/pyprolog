% Working diagnosis system with simpler approach
test_write :- write('Hello from Prolog write'), nl.

% Simple disease facts
disease_symptom(cold, fever, 0.8).
disease_symptom(cold, cough, 0.7).

% Simple diagnosis predicate that works
simple_diagnosis(Result) :-
    write('Debug: simple_diagnosis called'), nl,
    Result = cold.

% Another working predicate
diagnose_cold(Symptoms, Disease) :-
    write('Diagnosing...'), nl,
    Disease = cold.

% Test with numeric result
get_probability(Disease, Prob) :-
    write('Getting probability for: '), write(Disease), nl,
    Prob = 0.85.

% Combined predicate
patient_diagnosis(Symptoms, Result) :-
    write('Starting diagnosis'), nl,
    simple_diagnosis(Disease),
    write('Got disease: '), write(Disease), nl,
    get_probability(Disease, Prob),
    write('Got probability: '), write(Prob), nl,
    Result = Disease.