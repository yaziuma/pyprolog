% ==========================================
% crypt.pl - SEND + MORE = MONEY
% ==========================================
% 実行方法: ?- benchmark.
% ==========================================

benchmark :-
    write('Solving SEND + MORE = MONEY...'), nl,
    solve(S, E, N, D, M, O, R, Y),
    write('  '), write(S), write(E), write(N), write(D), nl,
    write('+ '), write(M), write(O), write(R), write(E), nl,
    write('-----'), nl,
    write(' '), write(M), write(O), write(N), write(E), write(Y), nl.

solve(S, E, N, D, M, O, R, Y) :-
    % 桁の割り当て (Generate)
    digit(S), S > 0, % Sは0ではない
    digit(M), M > 0, % Mは0ではない
    S =\= M,
    
    digit(E), E =\= S, E =\= M,
    digit(O), O =\= S, O =\= M, O =\= E,
    digit(N), N =\= S, N =\= M, N =\= E, N =\= O,
    digit(R), R =\= S, R =\= M, R =\= E, R =\= O, R =\= N,
    digit(D), D =\= S, D =\= M, D =\= E, D =\= O, D =\= N, D =\= R,
    digit(Y), Y =\= S, Y =\= M, Y =\= E, Y =\= O, Y =\= N, Y =\= R, Y =\= D,

    % 計算チェック (Test)
    % 下の桁からチェックすると高速化できるが、
    % ベンチマークとしては素朴な計算の方が負荷がかかるため全体計算を行う
    
    Send  is 1000*S + 100*E + 10*N + D,
    More  is 1000*M + 100*O + 10*R + E,
    Money is 10000*M + 1000*O + 100*N + 10*E + Y,
    
    Money is Send + More.

% 数字の候補
digit(0). digit(1). digit(2). digit(3). digit(4).
digit(5). digit(6). digit(7). digit(8). digit(9).