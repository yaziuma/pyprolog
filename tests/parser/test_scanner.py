"""
Scanner テスト

Prologインタープリターのスキャナー（字句解析器）の
動作を検証するテストスイート。
"""

from prolog.parser.scanner import Scanner
from prolog.parser.token_type import TokenType
from prolog.parser.token import Token


class TestScanner:
    """スキャナーのテスト"""

    def test_basic_tokens(self):
        """基本トークンのスキャンテスト"""
        source = "( ) [ ] , . |"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        expected_types = [
            TokenType.LEFTPAREN,
            TokenType.RIGHTPAREN,
            TokenType.LEFTBRACKET,
            TokenType.RIGHTBRACKET,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.BAR,
            TokenType.EOF
        ]
        
        assert len(tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert tokens[i].token_type == expected_type

    def test_operators_scanning(self):
        """演算子のスキャンテスト"""
        source = ":- + - * / = \\= < > =< >= is"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # EOFを除外
        operator_tokens = [token for token in tokens if token.token_type != TokenType.EOF]
        
        # 基本的な演算子がスキャンされることを確認
        assert len(operator_tokens) > 0
        
        # :- の確認
        colon_minus_found = any(token.token_type == TokenType.COLONMINUS for token in operator_tokens)
        assert colon_minus_found

    def test_numbers_and_strings(self):
        """数値と文字列のスキャンテスト"""
        source = "42 3.14 'hello world' 'test'"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # 数値と文字列のトークンを抽出
        value_tokens = [token for token in tokens if token.token_type in [TokenType.NUMBER, TokenType.STRING]]
        
        assert len(value_tokens) == 4
        assert value_tokens[0].token_type == TokenType.NUMBER
        assert value_tokens[0].literal == 42.0
        
        assert value_tokens[1].token_type == TokenType.NUMBER
        assert value_tokens[1].literal == 3.14
        
        assert value_tokens[2].token_type == TokenType.STRING
        assert value_tokens[2].literal == "hello world"
        
        assert value_tokens[3].token_type == TokenType.STRING
        assert value_tokens[3].literal == "test"

    def test_variables_and_atoms(self):
        """変数とアトムのスキャンテスト"""
        source = "X Y _var lowercase UPPERCASE atom123"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # EOF以外のトークンを抽出
        identifier_tokens = [token for token in tokens if token.token_type in [TokenType.VARIABLE, TokenType.ATOM]]
        
        assert len(identifier_tokens) == 6
        
        # 大文字で始まるものは変数
        assert identifier_tokens[0].token_type == TokenType.VARIABLE  # X
        assert identifier_tokens[0].lexeme == "X"
        
        assert identifier_tokens[1].token_type == TokenType.VARIABLE  # Y
        assert identifier_tokens[1].lexeme == "Y"
        
        assert identifier_tokens[2].token_type == TokenType.VARIABLE  # _var
        assert identifier_tokens[2].lexeme == "_var"
        
        # 小文字で始まるものはアトム
        assert identifier_tokens[3].token_type == TokenType.ATOM  # lowercase
        assert identifier_tokens[3].lexeme == "lowercase"
        
        assert identifier_tokens[4].token_type == TokenType.VARIABLE  # UPPERCASE
        assert identifier_tokens[4].lexeme == "UPPERCASE"
        
        assert identifier_tokens[5].token_type == TokenType.ATOM  # atom123
        assert identifier_tokens[5].lexeme == "atom123"

    def test_special_characters(self):
        """特殊文字のスキャンテスト"""
        source = ":-"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        assert len(tokens) == 2  # :- と EOF
        assert tokens[0].token_type == TokenType.COLONMINUS
        assert tokens[0].lexeme == ":-"

    def test_comments_handling(self):
        """コメント処理のテスト"""
        source = """
        atom1  % this is a comment
        atom2
        % another comment
        atom3
        """
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # コメントは無視され、アトムのみが残る
        atom_tokens = [token for token in tokens if token.token_type == TokenType.ATOM]
        assert len(atom_tokens) == 3
        assert atom_tokens[0].lexeme == "atom1"
        assert atom_tokens[1].lexeme == "atom2"
        assert atom_tokens[2].lexeme == "atom3"

    def test_error_cases(self):
        """エラーケースのテスト"""
        # 未終端文字列
        source1 = "'unterminated string"
        scanner1 = Scanner(source1)
        tokens1 = scanner1.scan_tokens()
        # エラーが発生してもEOFトークンは生成される
        assert tokens1[-1].token_type == TokenType.EOF

    def test_keywords_recognition(self):
        """キーワード認識のテスト"""
        source = "true fail retract asserta assertz"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        keyword_tokens = [token for token in tokens if token.token_type != TokenType.EOF]
        
        assert len(keyword_tokens) == 5
        assert keyword_tokens[0].token_type == TokenType.TRUE
        assert keyword_tokens[1].token_type == TokenType.FAIL
        assert keyword_tokens[2].token_type == TokenType.RETRACT
        assert keyword_tokens[3].token_type == TokenType.ASSERTA
        assert keyword_tokens[4].token_type == TokenType.ASSERTZ

    def test_whitespace_handling(self):
        """空白処理のテスト"""
        source = "  atom1   atom2\t\tatom3\n\natom4  "
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        atom_tokens = [token for token in tokens if token.token_type == TokenType.ATOM]
        assert len(atom_tokens) == 4
        assert atom_tokens[0].lexeme == "atom1"
        assert atom_tokens[1].lexeme == "atom2"
        assert atom_tokens[2].lexeme == "atom3"
        assert atom_tokens[3].lexeme == "atom4"

    def test_line_tracking(self):
        """行番号追跡のテスト"""
        source = """atom1
        atom2
        atom3"""
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        atom_tokens = [token for token in tokens if token.token_type == TokenType.ATOM]
        assert atom_tokens[0].line == 1
        assert atom_tokens[1].line == 2
        assert atom_tokens[2].line == 3

    def test_complex_expression(self):
        """複雑な式のスキャンテスト"""
        source = "parent(X, Y) :- father(X, Y)."
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # EOFを除く
        expr_tokens = [token for token in tokens if token.token_type != TokenType.EOF]
        
        expected_lexemes = ["parent", "(", "X", ",", "Y", ")", ":-", "father", "(", "X", ",", "Y", ")", "."]
        assert len(expr_tokens) == len(expected_lexemes)
        
        for i, expected_lexeme in enumerate(expected_lexemes):
            assert expr_tokens[i].lexeme == expected_lexeme

    def test_list_syntax(self):
        """リスト構文のスキャンテスト"""
        source = "[a, b, c | Tail]"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        # EOFを除く
        list_tokens = [token for token in tokens if token.token_type != TokenType.EOF]
        
        expected_types = [
            TokenType.LEFTBRACKET,
            TokenType.ATOM,       # a
            TokenType.COMMA,
            TokenType.ATOM,       # b
            TokenType.COMMA,
            TokenType.ATOM,       # c
            TokenType.BAR,
            TokenType.VARIABLE,   # Tail
            TokenType.RIGHTBRACKET
        ]
        
        assert len(list_tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert list_tokens[i].token_type == expected_type

    def test_float_numbers(self):
        """浮動小数点数のスキャンテスト"""
        source = "1.0 123.456 0.5"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        number_tokens = [token for token in tokens if token.token_type == TokenType.NUMBER]
        
        assert len(number_tokens) == 3
        assert number_tokens[0].literal == 1.0
        assert number_tokens[1].literal == 123.456
        assert number_tokens[2].literal == 0.5

    def test_empty_source(self):
        """空のソースのテスト"""
        source = ""
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.EOF

    def test_multiline_string(self):
        """複数行文字列のテスト"""
        source = "'line1\nline2'"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        string_tokens = [token for token in tokens if token.token_type == TokenType.STRING]
        assert len(string_tokens) == 1
        assert string_tokens[0].literal == "line1\nline2"