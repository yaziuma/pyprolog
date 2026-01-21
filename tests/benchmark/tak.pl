% ==========================================
% tak.pl - Takeuchi function
% ==========================================
% 実行方法: ?- benchmark(18, 12, 6, R).
% ==========================================

benchmark(X, Y, Z, R) :-
    write('Calculating tak('), write(X), write(','), write(Y), write(','), write(Z), write(')...'), nl,
    tak(X, Y, Z, R),
    write('Result: '), write(R), nl.

tak(X, Y, Z, Z) :-
    X =< Y, !.
tak(X, Y, Z, R) :-
    X > Y,
    X1 is X - 1,
    tak(X1, Y, Z, R1),
    Y1 is Y - 1,
    tak(Y1, Z, X, R2),
    Z1 is Z - 1,
    tak(Z1, X, Y, R3),
    tak(R1, R2, R3, R).
