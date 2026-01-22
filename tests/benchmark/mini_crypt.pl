% ==========================================
% mini_crypt.pl - I + BB = ILL
% ==========================================
% 実行方法: ?- benchmark.
% ==========================================

benchmark :-
    write('Solving I + BB = ILL...'), nl,
    solve(I, B, L),
    write('  '), write(I), nl,
    write('+ '), write(B), write(B), nl,
    write('-----'), nl,
    write(' '), write(I), write(L), write(L), nl.

solve(I, B, L) :-
    digit(I), I > 0,
    digit(B), B > 0, B != I,
    digit(L), L != I, L != B,

    BB  is 10*B + B,
    ILL is 100*I + 10*L + L,

    ILL =:= I + BB.

% 数字の候補

digit(0). digit(1). digit(2). digit(3). digit(4).
digit(5). digit(6). digit(7). digit(8). digit(9).
