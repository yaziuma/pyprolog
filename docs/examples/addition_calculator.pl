% 入力待ち検知ガイド用のサンプルプログラム
% 2つの数字を入力して加算結果を出力

% 基本的な加算計算
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

% 詳細な対話プログラム
detailed_interaction :-
    write('=== 詳細な計算プログラム ==='), nl,
    write('あなたの名前を入力してください: '),
    read_line(Name),
    write('こんにちは、'), write(Name), write('さん！'), nl,
    write('1つ目の数値を入力: '),
    read_line(Num1),
    write('2つ目の数値を入力: '),
    read_line(Num2),
    Result is Num1 + Num2,
    write(Name), write('さん、'),
    write(Num1), write(' + '), write(Num2), write(' = '), write(Result), nl,
    write('結果を保存しますか？ (yes/no): '),
    read_line(Save),
    (Save == 'yes' -> 
        write('結果が保存されました。')
    ; 
        write('保存をキャンセルしました。')
    ),
    nl.

% 複数回計算
multiple_calculations :-
    write('何回計算を行いますか？: '),
    read_line(Count),
    repeat_calculation(Count).

repeat_calculation(0) :-
    write('計算を完了しました。'), nl.

repeat_calculation(N) :-
    N > 0,
    write('数値1を入力: '),
    read_line(A),
    write('数値2を入力: '),
    read_line(B),
    Sum is A + B,
    write('結果: '), write(Sum), nl,
    N1 is N - 1,
    repeat_calculation(N1).

% 文字入力のテスト
char_input_test :-
    write('y/n で答えてください: '),
    get_char(Char),
    (Char == 'y' -> 
        write('「はい」が選択されました。')
    ; Char == 'n' ->
        write('「いいえ」が選択されました。')
    ;
        write('無効な選択です。')
    ),
    nl.