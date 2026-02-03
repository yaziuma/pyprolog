% ==========================================
% recursion_depth.pl - Simple recursion depth test
% ==========================================
% Test simple recursive calls to verify no RecursionError.
% The recursive implementation fails around N=490 due to Python's
% default recursion limit of ~1000.
% ==========================================

% Simple countdown benchmark
benchmark(0).
benchmark(N) :- N > 0, N1 is N - 1, benchmark(N1).

% Test queries:
% ?- benchmark(100).    % Should succeed (light)
% ?- benchmark(500).    % Should succeed with iterative (medium)
% ?- benchmark(1000).   % Should succeed with iterative (heavy)
