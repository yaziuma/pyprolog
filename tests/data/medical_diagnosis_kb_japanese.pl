% --- Test Write Predicate ---
test_write :- write('Hello from Prolog write'), nl.

% --- 疾患データベース ---
疾患症状(風邪, 発熱, 0.8).
疾患症状(風邪, 咳, 0.7).
疾患症状(風邪, のどの痛み, 0.6).
疾患症状(風邪, 鼻水, 0.9).

疾患症状(インフルエンザ, 発熱, 0.95).
疾患症状(インフルエンザ, 咳, 0.85).
疾患症状(インフルエンザ, 関節痛, 0.9).
疾患症状(インフルエンザ, 倦怠感, 0.9).
疾患症状(インフルエンザ, のどの痛み, 0.7).

疾患症状(肺炎, 発熱, 0.9).
疾患症状(肺炎, 咳, 0.95). % 肺炎では咳が特徴的
疾患症状(肺炎, 息切れ, 0.8).
疾患症状(肺炎, 胸痛, 0.7).
疾患症状(肺炎, 倦怠感, 0.85).

疾患症状(気管支炎, 咳, 0.9). % 気管支炎も咳が主
疾患症状(気管支炎, 微熱, 0.6).
疾患症状(気管支炎, 倦怠感, 0.7).
疾患症状(気管支炎, 胸の不快感, 0.65).

疾患症状(扁桃炎, のどの痛み, 0.95). % 扁桃炎はのどの痛みが強い
疾患症状(扁桃炎, 発熱, 0.8).
疾患症状(扁桃炎, 嚥下痛, 0.85).

% --- 基礎疾患リスク ---
基礎疾患リスク(糖尿病, 肺炎, 1.5).
基礎疾患リスク(心疾患, 肺炎, 1.3).
基礎疾患リスク(喘息, 気管支炎, 1.6).
基礎疾患リスク(免疫不全, インフルエンザ, 1.8).
基礎疾患リスク(免疫不全, 肺炎, 2.0).

% --- 年齢リスク ---
年齢リスク(65, インフルエンザ, 1.4). % 65歳以上
年齢リスク(65, 肺炎, 1.7).
年齢リスク(5, インフルエンザ, 1.2).  % 5歳以下 (幼児)
年齢リスク(5, 気管支炎, 1.3).

% --- 生活習慣リスク ---
生活習慣リスク(喫煙, 気管支炎, 1.5).
生活習慣リスク(喫煙, 肺炎, 1.2).
生活習慣リスク(過度の飲酒, 肺炎, 1.1).


% --- 緊急度判定 ---
% 緊急度(疾患, スコア閾値, 緊急レベル)
緊急度(肺炎, 0.7, 高). % 肺炎の診断確率が0.7以上なら緊急度「高」
緊急度(インフルエンザ, 0.6, 中).
緊急度(気管支炎, 0.5, 中).
緊急度(扁桃炎, 0.4, 低).
緊急度(風邪, 0.0, 低). % 風邪は基本的に低いが, 他で高ければそちらを優先


% --- 推奨検査 ---
推奨検査(肺炎, [胸部X線, 血液検査]).
推奨検査(インフルエンザ, [迅速抗原検査]).
推奨検査(気管支炎, [胸部X線, 喀痰検査]).
推奨検査(扁桃炎, [喉頭鏡検査]).
推奨検査(風邪, []). % 風邪は特になし

% --- Helper: Sort and Unique list of atoms (bypassed for now) ---
simple_sort_unique(List, List). % No-op, just pass through for now.

% --- 診断ルール ---

% 症状リストと疾患から症状マッチスコアを計算
calculate_symptom_match_score(_ReportedSymptoms, _Disease, 0.75). % Simplified for testing

% 基礎疾患に基づいてリスク係数を計算
calculate_condition_risk_factor(PatientConditions, Disease, Factor) :-
    findall(Risk, (member(Cond, PatientConditions), 基礎疾患リスク(Cond, Disease, Risk)), Risks),
    (Risks = [] -> Factor = 1.0 ; product_list(Risks, Factor)).

% 年齢に基づいてリスク係数を計算
calculate_age_risk_factor(Age, Disease, Factor) :-
    ( (Age >= 65, 年齢リスク(65, Disease, RiskElderly)) -> Factor = RiskElderly
    ; (Age =< 5, 年齢リスク(5, Disease, RiskChild)) -> Factor = RiskChild
    ; Factor = 1.0
    ).

% 生活習慣に基づいてリスク係数を計算
calculate_lifestyle_risk_factor(PatientLifestyles, Disease, Factor) :-
    findall(Risk, (member(Lifestyle, PatientLifestyles), 生活習慣リスク(Lifestyle, Disease, Risk)), Risks),
    (Risks = [] -> Factor = 1.0 ; product_list(Risks, Factor)).


% 最終的な疾患確率を計算
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

% Renamed and Simplified for testing with ground atomic/numeric arguments
gadp_test(Arg1, Arg2, Arg3, Arg4, OutputResult) :-
    write('Debug: GADP_TEST CALLED with ground args'), nl,
    write('Arg1: '), write(Arg1), nl,
    write('Arg2: '), write(Arg2), nl,
    write('Arg3: '), write(Arg3), nl,
    write('Arg4: '), write(Arg4), nl,
    OutputResult = [診断(風邪, 0.88)].

% 緊急度を決定する
determine_urgency([], 低).
determine_urgency([診断(Disease, Prob) | RestProbs], Urgency) :-
    緊急度(Disease, ProbThreshold, Level),
    (Prob >= ProbThreshold -> CurrentUrgency = Level ; CurrentUrgency = 低),
    determine_urgency(RestProbs, RestUrgency),
    highest_urgency(CurrentUrgency, RestUrgency, Urgency).

% 2つの緊急度レベルから高い方を選択
highest_urgency(高, _, 高).
highest_urgency(_, 高, 高).
highest_urgency(中, 低, 中).
highest_urgency(低, 中, 中).
highest_urgency(中, 中, 中).
highest_urgency(低, 低, 低).


% 推奨検査リストを作成
get_recommended_tests([], []).
get_recommended_tests([診断(Disease, Prob) | RestProbs], Tests) :-
    (Prob > 0.3 ->
        推奨検査(Disease, CurrentTests),
        get_recommended_tests(RestProbs, RestTests),
        union(CurrentTests, RestTests, Tests)
    ;
        get_recommended_tests(RestProbs, Tests)
    ).

% Custom comparator for sort/4
my_greater_equal(X, Y) :- X >= Y.

% メインの診断述語
患者診断(Symptoms, Age, Conditions, Lifestyles, 結果) :-
    write('Debug: Entering 患者診断'), % Removed nl here
    write('Debug: Calling gadp_test/5...'), nl,
    gadp_test(atom1, 99, atom2, atom3, TestOutput),
    write('Debug: gadp_test/5 returned, TestOutput = '), write(TestOutput), nl,
    DiseaseProbs = TestOutput,

    write('Debug: 患者診断 - DiseaseProbs = '), write(DiseaseProbs), nl,
    (DiseaseProbs = [] ->
        write('Debug: 患者診断 - DiseaseProbs is empty'), nl,
        結果 = [診断結果なし, 緊急度(低), 検査([])]
    ;
        write('Debug: 患者診断 - DiseaseProbs is NOT empty, processing...'), nl,
        sort(2, my_greater_equal, DiseaseProbs, SortedDiseaseProbs),
        write('Debug: 患者診断 - SortedDiseaseProbs = '), write(SortedDiseaseProbs), nl,
        determine_urgency(SortedDiseaseProbs, UrgencyLevel),
        write('Debug: 患者診断 - UrgencyLevel = '), write(UrgencyLevel), nl,
        get_recommended_tests(SortedDiseaseProbs, RecommendedTests),
        write('Debug: 患者診断 - RecommendedTests = '), write(RecommendedTests), nl,
        結果 = [診断結果(SortedDiseaseProbs), 緊急度(UrgencyLevel), 検査(RecommendedTests)],
        write('Debug: 患者診断 - 結果 unified = '), write(結果), nl
    ).

% 別のメイン述語
診断(Symptoms, Age, Conditions, DiagnosisList) :-
    患者診断(Symptoms, Age, Conditions, [], DiagnosisList).

% ユーティリティ
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
