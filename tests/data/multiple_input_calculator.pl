% 複数入力加算計算プログラム  
% 1つ目と2つ目の値を入力し、数値でない場合は再入力を求める

% メイン処理
calculate_sum :-
    write('数値を2つ入力して合計を計算します'), nl,
    get_first_number(First),
    get_second_number(Second),
    Sum is First + Second,
    write('合計: '), write(Sum), nl.

% 1つ目の数値を取得
get_first_number(Number) :-
    write('1つ目の値を入力してください: '), 
    read_line(Input),
    validate_number(Input, Number, first).

% 2つ目の数値を取得
get_second_number(Number) :-
    write('2つ目の値を入力してください: '),
    read_line(Input),
    validate_number(Input, Number, second).

% 入力値が数値かどうかを検証し、無効な場合は再入力を求める
validate_number(Input, Number, Position) :-
    number(Input), !,
    Number = Input.

validate_number(Input, Number, Position) :-
    atom(Input),
    atom_number(Input, Number), !.

validate_number(Input, Number, first) :-
    write('エラー: 数値ではありません'), nl,
    get_first_number(Number).

validate_number(Input, Number, second) :-
    write('エラー: 数値ではありません'), nl, 
    get_second_number(Number).

% 実行用クエリの例
% ?- calculate_sum.