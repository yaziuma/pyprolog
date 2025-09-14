% 2つの数字を入力して加算結果を出力するプログラム
% PyProlog v0.6.0対応

% メイン処理
calculate_sum :-
    write('最初の数字を入力してください: '),
    read_line(First),
    write('次の数字を入力してください: '),
    read_line(Second),
    Sum is First + Second,
    write('計算結果: '),
    write(Sum),
    nl.

% 日本語版
数字加算 :-
    write('一つ目の数字を入力: '),
    read_line(X),
    write('二つ目の数字を入力: '),
    read_line(Y),
    Z is X + Y,
    write('合計: '),
    write(Z),
    nl.