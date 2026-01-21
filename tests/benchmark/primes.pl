% ==========================================
% primes.pl - Sieve of Eratosthenes
% ==========================================
% 実行方法: ?- benchmark(100).
% 引数までの素数をリストアップします。
% ==========================================

benchmark(Limit) :-
    write('Generating primes up to '), write(Limit), nl,
    primes(Limit, Primes),
    write('Primes: '), write(Primes), nl.

primes(Limit, Ps) :-
    range(2, Limit, Integers),
    sieve(Integers, Ps).

% 篩のロジック
sieve([], []).
sieve([P|Rest], [P|SievedRest]) :-
    filter(Rest, P, Filtered),
    sieve(Filtered, SievedRest).

% 倍数を取り除く
filter([], _, []).
filter([H|T], P, Result) :-
    H mod P =:= 0, !,    % 割り切れる場合はスキップ
    filter(T, P, Result).
filter([H|T], P, [H|Result]) :-
    filter(T, P, Result).

% 補助述語 (range)
range(N, N, [N]) :- !.
range(I, N, [I|Rest]) :-
    I < N,
    I1 is I + 1,
    range(I1, N, Rest).
