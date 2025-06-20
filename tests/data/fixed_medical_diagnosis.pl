% Fixed Medical Diagnosis System
% Simplified version that avoids parse errors

% Test predicate
test_write :- write('Hello from medical system'), nl.

% Disease symptom facts
disease_symptom(cold, fever, 0.8).
disease_symptom(cold, cough, 0.7).
disease_symptom(flu, fever, 0.95).
disease_symptom(flu, cough, 0.85).
disease_symptom(pneumonia, fever, 0.9).
disease_symptom(pneumonia, cough, 0.95).

% Simple diagnosis predicate that works
diagnose_disease(Symptoms, Disease, Probability) :-
    member(Symptom, Symptoms),
    disease_symptom(Disease, Symptom, Probability).

% Working patient diagnosis predicate
patient_diagnosis(Symptoms, Age, Conditions, Lifestyles, Result) :-
    write('Starting diagnosis...'), nl,
    diagnose_disease(Symptoms, Disease, Prob),
    write('Found disease: '), write(Disease), nl,
    Result = diagnosis_result(Disease, Prob).

% Alternative simple diagnosis
simple_patient_diagnosis(Symptoms, Result) :-
    write('Simple diagnosis started'), nl,
    Result = [diagnosis(cold, 0.75), urgency(low)],
    write('Simple diagnosis completed'), nl.

% Test for compound terms
compound_term_test(Result) :-
    write('Creating compound term'), nl,
    Result = medical_result(diagnosis(cold, 0.8), urgency(medium)),
    write('Compound term created'), nl.