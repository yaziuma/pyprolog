% ==========================================
% nrev.pl - Naive Reverse Benchmark
% ==========================================
% 実行方法: ?- benchmark(30).
% 引数はリストの長さ（標準は30）
% ==========================================

% エントリポイント
benchmark(N) :-
    make_list(N, List),
    write('Reversing list of length '), write(N), nl,
    nrev(List, _).

% リストの生成 (1からNまで)
make_list(0, []) :- !.
make_list(N, [N|Rest]) :-
    N > 0,
    N1 is N - 1,
    make_list(N1, Rest).

% Naive Reverse 本体
nrev([], []).
nrev([H|T], Reversed) :-
    nrev(T, RevT),
    append(RevT, [H], Reversed).

% 標準的な append
append([], L, L).
append([H|T], L, [H|Result]) :-
    append(T, L, Result).