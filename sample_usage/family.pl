% 家族関係のサンプルデータ
% 基本的な親子関係
parent(tom, bob).
parent(tom, liz).
parent(bob, ann).
parent(bob, pat).
parent(pat, jim).
parent(mary, bob).
parent(mary, liz).

% 性別
male(tom).
male(bob).
male(pat).
male(jim).
female(mary).
female(liz).
female(ann).

% 年齢
age(tom, 65).
age(mary, 63).
age(bob, 40).
age(liz, 38).
age(ann, 18).
age(pat, 16).
age(jim, 5).

% ルール定義
% 父親の定義
father(X, Y) :- parent(X, Y), male(X).

% 母親の定義
mother(X, Y) :- parent(X, Y), female(X).

% 祖父母の定義
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
grandfather(X, Z) :- grandparent(X, Z), male(X).
grandmother(X, Z) :- grandparent(X, Z), female(X).

% 兄弟姉妹の定義
sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \= Y.

% 叔父・叔母の定義
uncle(X, Y) :- sibling(X, Z), parent(Z, Y), male(X).
aunt(X, Y) :- sibling(X, Z), parent(Z, Y), female(X).

% 先祖の定義（再帰）
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

% 年上・年下の関係
older(X, Y) :- age(X, AgeX), age(Y, AgeY), AgeX > AgeY.
younger(X, Y) :- older(Y, X).

% 同世代（年齢差が5歳以内）
same_generation(X, Y) :- 
    age(X, AgeX), 
    age(Y, AgeY), 
    Diff is AgeX - AgeY,
    Diff >= -5,
    Diff =< 5,
    X \= Y.