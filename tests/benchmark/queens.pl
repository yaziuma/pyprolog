% ==========================================
% queens.pl - N-Queens Benchmark
% ==========================================
% 実行方法: ?- benchmark(8).
% 引数はボードのサイズ（標準は8）
% ==========================================

benchmark(N) :-
    write('Solving '), write(N), write('-Queens problem...'), nl,
    solve_queens(N, Solution),
    write('Solution found: '), write(Solution), nl.

% Nクイーンの解決
solve_queens(N, Solution) :-
    range(1, N, Rows),
    queens(Rows, [], Solution).

% メインロジック
queens([], Solution, Solution).
queens(UnplacedRows, SafeQueens, Solution) :-
    select(Row, UnplacedRows, RemainingRows),
    Length is 1 + 0, % 現在の列位置を計算する簡易的な方法（実際の列番号はSafeQueensの長さでわかる）
    list_length(SafeQueens, Col0),
    Col is Col0 + 1,
    is_safe(Row, Col, SafeQueens),
    queens(RemainingRows, [q(Row, Col)|SafeQueens], Solution).

% 配置が可能かチェック
is_safe(_, _, []).
is_safe(Row, Col, [q(R, C)|Rest]) :-
    Row =\= R,          % 同じ行ではない（selectで保証されるが一応）
    diff(Row, R, D1),
    diff(Col, C, D2),
    D1 =\= D2,          % 斜めではない (|Row-R| != |Col-C|)
    is_safe(Row, Col, Rest).

% 補助述語
range(N, N, [N]) :- !.
range(I, N, [I|Rest]) :-
    I < N,
    I1 is I + 1,
    range(I1, N, Rest).

select(X, [X|Rest], Rest).
select(X, [H|Rest], [H|RestWithoutX]) :-
    select(X, Rest, RestWithoutX).

list_length([], 0).
list_length([_|T], N) :-
    list_length(T, N0),
    N is N0 + 1.

diff(A, B, D) :- A >= B, !, D is A - B.
diff(A, B, D) :- D is B - A.