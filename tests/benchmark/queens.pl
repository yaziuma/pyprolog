% ==========================================
% queens.pl - N-Queens Benchmark
% ==========================================
% 実行方法: ?- benchmark(8).
% 引数はボードのサイズ（標準は8）
% ==========================================

benchmark(N) :-
    write('Solving '), write(N), write('-Queens problem...'), nl,
    solve_queens(N, Solution),
    write('Solution found: '), write(Solution), nl,
    fail. % 全ての解を見つけたい場合はバックトラッキングさせる
benchmark(_).

% Nクイーンの解決
solve_queens(N, Solution) :-
    range(1, N, Rows),
    queens(Rows, [], Solution).

% メインロジック
queens([], Solution, Solution).
queens(UnplacedRows, SafeQueens, Solution) :-
    select(Row, UnplacedRows, RemainingRows),
    safe(Row, 1, SafeQueens),
    queens(RemainingRows, [Row|SafeQueens], Solution).

% 安全性の確認
safe(_, _, []).
safe(Row, Distance, [Q|Rest]) :-
    Row != Q,
    Row != Q + Distance,
    Row != Q - Distance,
    NextDistance is Distance + 1,
    safe(Row, NextDistance, Rest).

% 補助述語 (select)
select(X, [X|T], T).
select(X, [H|T], [H|Rest]) :-
    select(X, T, Rest).

% 補助述語 (range)
range(N, N, [N]) :- !.
range(I, N, [I|Rest]) :-
    I < N,
    I1 is I + 1,
    range(I1, N, Rest).
