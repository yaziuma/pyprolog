% --- Test Write Predicate ---
test_write :- write('Hello from Prolog write'), nl.

% --- Disease Database ---
disease_symptom(cold, fever, 0.8).
disease_symptom(cold, cough, 0.7).
disease_symptom(cold, sore_throat, 0.6).
disease_symptom(cold, runny_nose, 0.9).

disease_symptom(flu, fever, 0.95).
disease_symptom(flu, cough, 0.85).
disease_symptom(flu, joint_pain, 0.9).
disease_symptom(flu, fatigue, 0.9).
disease_symptom(flu, sore_throat, 0.7).

disease_symptom(pneumonia, fever, 0.9).
disease_symptom(pneumonia, cough, 0.95). % Characteristic cough in pneumonia
disease_symptom(pneumonia, shortness_of_breath, 0.8).
disease_symptom(pneumonia, chest_pain, 0.7).
disease_symptom(pneumonia, fatigue, 0.85).

disease_symptom(bronchitis, cough, 0.9). % Main symptom in bronchitis
disease_symptom(bronchitis, low_fever, 0.6).
disease_symptom(bronchitis, fatigue, 0.7).
disease_symptom(bronchitis, chest_discomfort, 0.65).

disease_symptom(tonsillitis, sore_throat, 0.95). % Strong sore throat in tonsillitis
disease_symptom(tonsillitis, fever, 0.8).
disease_symptom(tonsillitis, swallowing_pain, 0.85).

% --- Underlying Condition Risk ---
condition_risk(diabetes, pneumonia, 1.5).
condition_risk(heart_disease, pneumonia, 1.3).
condition_risk(asthma, bronchitis, 1.6).
condition_risk(immunodeficiency, flu, 1.8).
condition_risk(immunodeficiency, pneumonia, 2.0).

% --- Age Risk ---
age_risk(65, flu, 1.4). % 65 and older
age_risk(65, pneumonia, 1.7).
age_risk(5, flu, 1.2).  % 5 and younger (children)
age_risk(5, bronchitis, 1.3).

% --- Lifestyle Risk ---
lifestyle_risk(smoking, bronchitis, 1.5).
lifestyle_risk(smoking, pneumonia, 1.2).
lifestyle_risk(excessive_drinking, pneumonia, 1.1).

% --- Urgency Determination ---
% urgency(disease, probability_threshold, urgency_level)
urgency(pneumonia, 0.7, high). % If pneumonia probability >= 0.7, urgency is high
urgency(flu, 0.6, medium).
urgency(bronchitis, 0.5, medium).
urgency(tonsillitis, 0.4, low).
urgency(cold, 0.0, low). % Cold is generally low, but if others are high, prioritize those

% --- Recommended Tests ---
recommended_test(pneumonia, [chest_xray, blood_test]).
recommended_test(flu, [rapid_antigen_test]).
recommended_test(bronchitis, [chest_xray, sputum_test]).
recommended_test(tonsillitis, [throat_examination]).
recommended_test(cold, []). % No specific tests for cold

% --- Helper: Sort and Unique list of atoms (bypassed for now) ---
simple_sort_unique(List, List). % No-op, just pass through for now.

% --- Diagnosis Rules ---

% Calculate symptom match score from symptom list and disease
calculate_symptom_match_score(_ReportedSymptoms, _Disease, 0.75). % Simplified for testing

% Calculate risk factor based on underlying conditions
calculate_condition_risk_factor(PatientConditions, Disease, Factor) :-
    findall(Risk, (member(Cond, PatientConditions), condition_risk(Cond, Disease, Risk)), Risks),
    (Risks = [] -> Factor = 1.0 ; product_list(Risks, Factor)).

% Calculate risk factor based on age
calculate_age_risk_factor(Age, Disease, Factor) :-
    ( (Age >= 65, age_risk(65, Disease, RiskElderly)) -> Factor = RiskElderly
    ; (Age =< 5, age_risk(5, Disease, RiskChild)) -> Factor = RiskChild
    ; Factor = 1.0
    ).

% Calculate risk factor based on lifestyle
calculate_lifestyle_risk_factor(PatientLifestyles, Disease, Factor) :-
    findall(Risk, (member(Lifestyle, PatientLifestyles), lifestyle_risk(Lifestyle, Disease, Risk)), Risks),
    (Risks = [] -> Factor = 1.0 ; product_list(Risks, Factor)).

% Calculate final disease probability
calculate_disease_probability(ReportedSymptoms, Age, PatientConditions, PatientLifestyles, Disease, Probability) :-
    calculate_symptom_match_score(ReportedSymptoms, Disease, SymptomScore),
    (SymptomScore > 0 ->
        calculate_condition_risk_factor(PatientConditions, Disease, ConditionFactor),
        calculate_age_risk_factor(Age, Disease, AgeFactor),
        calculate_lifestyle_risk_factor(PatientLifestyles, Disease, LifestyleFactor),
        BaseProbability is SymptomScore,
        Probability is BaseProbability * ConditionFactor * AgeFactor * LifestyleFactor,
        (Probability > 1.0 -> FinalProbability = 1.0 ; FinalProbability = Probability),
        Probability = FinalProbability
    ;
        Probability = 0.0
    ).

% Simplified test predicate
gadp_test(Arg1, Arg2, Arg3, Arg4, OutputResult) :-
    write('Debug: GADP_TEST CALLED with ground args'), nl,
    OutputResult = [diagnosis(cold, 0.88)].

% Determine urgency level
determine_urgency([], low).
determine_urgency([diagnosis(Disease, Prob) | RestProbs], Urgency) :-
    urgency(Disease, ProbThreshold, Level),
    (Prob >= ProbThreshold -> CurrentUrgency = Level ; CurrentUrgency = low),
    determine_urgency(RestProbs, RestUrgency),
    highest_urgency(CurrentUrgency, RestUrgency, Urgency).

% Select higher urgency level from two
highest_urgency(high, _, high).
highest_urgency(_, high, high).
highest_urgency(medium, low, medium).
highest_urgency(low, medium, medium).
highest_urgency(medium, medium, medium).
highest_urgency(low, low, low).

% Create recommended test list
get_recommended_tests([], []).
get_recommended_tests([diagnosis(Disease, Prob) | RestProbs], Tests) :-
    (Prob > 0.3 ->
        recommended_test(Disease, CurrentTests),
        get_recommended_tests(RestProbs, RestTests),
        union(CurrentTests, RestTests, Tests)
    ;
        get_recommended_tests(RestProbs, Tests)
    ).

% Custom comparator for sort/4
my_greater_equal(X, Y) :- X >= Y.

% Simplified main diagnosis predicate
patient_diagnosis(Symptoms, Age, Conditions, Lifestyles, Result) :-
    write('Debug: Entering patient_diagnosis'), nl,
    gadp_test(Symptoms, Age, Conditions, Lifestyles, TestOutput),
    write('Debug: gadp_test returned'), nl,
    Result = TestOutput.

% Alternative main predicate
diagnose(Symptoms, Age, Conditions, DiagnosisList) :-
    patient_diagnosis(Symptoms, Age, Conditions, [], DiagnosisList).

% Utilities
sum_list([], 0).
sum_list([H|T], Sum) :-
    sum_list(T, RestSum),
    Sum is H + RestSum.

product_list([], 1).
product_list([H|T], Product) :-
    product_list(T, RestProduct),
    Product is H * RestProduct.

union([], L, L).
union([H|T], L2, L3) :-
    member(H, L2), !,
    union(T, L2, L3).
union([H|T], L2, [H|L3]) :-
    union(T, L2, L3).

% Custom sort/4 is a NO-OP for testing.
sort(_KeyIndex, _Comparator, List, List).

% Re-adding custom call/N predicates
call(Goal) :- Goal.
call(Goal, Arg1) :- TempGoal =.. [Goal, Arg1], TempGoal.
call(Goal, Arg1, Arg2) :- TempGoal =.. [Goal, Arg1, Arg2], TempGoal.

% NOTE: Assumed system provides: member/2, append/3, arg/3, length/2, etc.
% System also needs to handle `is/2` for arithmetic.
% `simple_sort_unique` is a no-op.
% `sort/4` (custom keyed sort) is a no-op.