% ==========================================
% tak.pl - Takeuchi Function Benchmark
% ==========================================
% 実行方法: ?- benchmark.
% 標準的な入力 (18, 12, 6) で実行します。
% ==========================================

benchmark :-
    write('Calculating tak(18, 12, 6)...'), nl,
    tak(18, 12, 6, Result),
    write('Result: '), write(Result), nl.

% 竹内関数の定義
tak(X, Y, Z, A) :-
    X =< Y, !,
    A = Z.
tak(X, Y, Z, A) :-
    X1 is X - 1,
    tak(X1, Y, Z, A1),
    Y1 is Y - 1,
    tak(Y1, Z, X, A2),
    Z1 is Z - 1,
    tak(Z1, X, Y, A3),
    tak(A1, A2, A3, A).