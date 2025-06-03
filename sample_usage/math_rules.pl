% 数学計算ルールのサンプル

% フィボナッチ数列
fibonacci(0, 0).
fibonacci(1, 1).
fibonacci(N, F) :- 
    N > 1,
    N1 is N - 1,
    N2 is N - 2,
    fibonacci(N1, F1),
    fibonacci(N2, F2),
    F is F1 + F2.

% 階乗計算
factorial(0, 1).
factorial(N, F) :- 
    N > 0,
    N1 is N - 1,
    factorial(N1, F1),
    F is N * F1.

% 最大公約数（ユークリッドの互除法）
gcd(X, 0, X) :- X > 0.
gcd(X, Y, G) :- 
    Y > 0,
    R is X mod Y,
    gcd(Y, R, G).

% 最小公倍数
lcm(X, Y, L) :- 
    gcd(X, Y, G),
    L is (X * Y) // G.

% べき乗計算
power(_, 0, 1).
power(X, N, P) :- 
    N > 0,
    N1 is N - 1,
    power(X, N1, P1),
    P is X * P1.

% 素数判定
is_prime(2).
is_prime(N) :- 
    N > 2,
    N mod 2 =\= 0,
    check_divisors(N, 3).

check_divisors(N, D) :- 
    D * D > N.
check_divisors(N, D) :- 
    D * D =< N,
    N mod D =\= 0,
    D1 is D + 2,
    check_divisors(N, D1).

% 数列の合計
sum_list([], 0).
sum_list([H|T], Sum) :- 
    sum_list(T, TailSum),
    Sum is H + TailSum.

% 数列の平均
average(List, Avg) :- 
    sum_list(List, Sum),
    length(List, Len),
    Len > 0,
    Avg is Sum / Len.

% 数列の最大値
max_list([X], X).
max_list([H|T], Max) :- 
    max_list(T, TailMax),
    (H > TailMax -> Max = H; Max = TailMax).

% 数列の最小値
min_list([X], X).
min_list([H|T], Min) :- 
    min_list(T, TailMin),
    (H < TailMin -> Min = H; Min = TailMin).

% 範囲内の数値生成
range(Start, End, Start) :- Start =< End.
range(Start, End, N) :- 
    Start < End,
    Start1 is Start + 1,
    range(Start1, End, N).

% 二次方程式の解（実数解のみ）
quadratic_solution(A, B, C, X) :- 
    A =\= 0,
    Discriminant is B * B - 4 * A * C,
    Discriminant >= 0,
    SqrtD is sqrt(Discriminant),
    (X is (-B + SqrtD) / (2 * A) ; X is (-B - SqrtD) / (2 * A)).

% 温度変換
celsius_to_fahrenheit(C, F) :- F is C * 9 / 5 + 32.
fahrenheit_to_celsius(F, C) :- C is (F - 32) * 5 / 9.

% 複利計算
compound_interest(Principal, Rate, Time, Amount) :- 
    Amount is Principal * (1 + Rate / 100) ** Time.