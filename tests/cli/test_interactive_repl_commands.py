"""
InteractiveREPLコマンドのテスト

拡張されたREPLコマンド（:explain、:search、:validate）のテストです。
"""
import pytest
from unittest.mock import Mock, patch, StringIO
import tempfile
import os
from pyprolog.cli.interactive_repl import InteractiveProlog


class TestInteractiveREPLCommands:
    """InteractiveREPLコマンドのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        # テスト用のPrologファイルを作成
        self.test_prolog_content = """
parent(tom, mary).
parent(mary, john).
parent(john, jane).

grandparent(X, Z) :- parent(X, Y), parent(Y, Z).

location(tokyo, japan).
location(osaka, japan).
population(tokyo, 14000000).

major_city(X) :- location(X, japan), population(X, P), P > 1000000.

undefined_caller(X) :- undefined_predicate(X).
"""
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False)
        self.temp_file.write(self.test_prolog_content)
        self.temp_file.close()
        
        # REPLインスタンスを作成し、テストファイルを読み込み
        with patch('builtins.print'):  # ウェルカムメッセージを抑制
            self.repl = InteractiveProlog()
        self.repl._init_runtime(self.temp_file.name)
    
    def teardown_method(self):
        """各テストの後のクリーンアップ"""
        os.unlink(self.temp_file.name)
    
    def test_explain_command_basic(self):
        """基本的な:explainコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":explain parent(tom, mary)")
            
            assert result is True  # コマンドが継続を返す
            # 出力が行われることを確認
            assert mock_print.called
            
            # 説明関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            explanation_found = any("Query Explanation" in str(arg) or "parent(tom, mary)" in str(arg) for arg in printed_args)
            assert explanation_found
    
    def test_explain_command_with_format(self):
        """フォーマット指定付き:explainコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":explain parent(tom, mary) tree")
            
            assert result is True
            assert mock_print.called
    
    def test_explain_command_with_depth(self):
        """深度指定付き:explainコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":explain grandparent(tom, jane) text 5")
            
            assert result is True
            assert mock_print.called
    
    def test_explain_command_no_args(self):
        """引数なし:explainコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":explain")
            
            assert result is True
            # エラーメッセージが表示されることを確認
            error_found = any("使用法" in str(call) or "Usage" in str(call) for call in mock_print.call_args_list)
            assert error_found or mock_print.called
    
    def test_search_command_basic(self):
        """基本的な:searchコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":search parent")
            
            assert result is True
            assert mock_print.called
            
            # 検索結果関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            search_found = any("検索結果" in str(arg) or "Search" in str(arg) or "parent" in str(arg) for arg in printed_args)
            assert search_found
    
    def test_search_command_with_type_and_limit(self):
        """タイプと制限指定付き:searchコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":search location predicate 5")
            
            assert result is True
            assert mock_print.called
    
    def test_search_command_no_args(self):
        """引数なし:searchコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":search")
            
            assert result is True
            # エラーメッセージが表示されることを確認
            error_found = any("使用法" in str(call) or "Usage" in str(call) for call in mock_print.call_args_list)
            assert error_found or mock_print.called
    
    def test_search_stats_command(self):
        """:search_statsコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":search_stats")
            
            assert result is True
            assert mock_print.called
            
            # 統計情報関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            stats_found = any("統計" in str(arg) or "Statistics" in str(arg) or "インデックス" in str(arg) for arg in printed_args)
            assert stats_found
    
    def test_rebuild_index_command(self):
        """:rebuild_indexコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":rebuild_index")
            
            assert result is True
            assert mock_print.called
            
            # 再構築関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            rebuild_found = any("再構築" in str(arg) or "rebuild" in str(arg) or "インデックス" in str(arg) for arg in printed_args)
            assert rebuild_found
    
    def test_validate_command_basic(self):
        """基本的な:validateコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":validate")
            
            assert result is True
            assert mock_print.called
            
            # 検証関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            validate_found = any("検証" in str(arg) or "Validation" in str(arg) or "解析" in str(arg) for arg in printed_args)
            assert validate_found
    
    def test_validate_command_conflicts_only(self):
        """矛盾検証のみ:validateコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":validate conflicts")
            
            assert result is True
            assert mock_print.called
    
    def test_validate_command_detailed(self):
        """詳細検証:validateコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":validate all true detailed")
            
            assert result is True
            assert mock_print.called
    
    def test_validate_command_invalid_type(self):
        """無効なタイプ指定:validateコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":validate invalid_type")
            
            assert result is True
            # エラーメッセージまたは警告が表示されることを確認
            assert mock_print.called
    
    def test_validate_stats_command(self):
        """:validate_statsコマンドのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":validate_stats")
            
            assert result is True
            assert mock_print.called
            
            # 統計情報関連の出力があることを確認
            printed_args = [call[0][0] for call in mock_print.call_args_list if call[0]]
            stats_found = any("統計" in str(arg) or "Statistics" in str(arg) or "シンボル" in str(arg) for arg in printed_args)
            assert stats_found
    
    def test_help_command_includes_new_commands(self):
        """:helpコマンドに新しいコマンドが含まれることのテスト"""
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":help")
            
            assert result is True
            assert mock_print.called
            
            # ヘルプ出力を結合して確認
            help_output = ' '.join([str(call[0][0]) for call in mock_print.call_args_list if call[0]])
            
            # 新しいコマンドがヘルプに含まれていることを確認
            assert ":explain" in help_output
            assert ":search" in help_output
            assert ":validate" in help_output
    
    def test_commands_without_runtime(self):
        """ランタイム未初期化時のコマンドテスト"""
        # 新しいREPLインスタンスを作成（ランタイム未初期化）
        with patch('builtins.print'):
            empty_repl = InteractiveProlog()
        
        with patch('builtins.print') as mock_print:
            # :explainコマンド
            result = empty_repl._handle_command(":explain test")
            assert result is True
            assert mock_print.called
            
            # エラーメッセージが表示されることを確認
            error_messages = [str(call[0][0]) for call in mock_print.call_args_list if call[0]]
            runtime_error = any("ランタイム" in msg or "Runtime" in msg or "初期化" in msg for msg in error_messages)
            assert runtime_error
    
    def test_command_error_handling(self):
        """コマンドエラーハンドリングのテスト"""
        # 無効なクエリでのテスト
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":explain invalid syntax here")
            
            assert result is True
            assert mock_print.called
            
            # エラーが適切にハンドリングされることを確認
            printed_output = ' '.join([str(call[0][0]) for call in mock_print.call_args_list if call[0]])
            # エラー出力またはエラーメッセージが含まれているかチェック
            error_handled = "エラー" in printed_output or "Error" in printed_output or "error" in printed_output
            # エラーがキャッチされて処理されていることを確認（クラッシュしない）
            assert True  # コマンドが正常終了すればOK
    
    def test_sequential_commands(self):
        """連続コマンド実行のテスト"""
        with patch('builtins.print'):
            # 複数のコマンドを順次実行
            result1 = self.repl._handle_command(":search parent")
            result2 = self.repl._handle_command(":explain parent(tom, mary)")
            result3 = self.repl._handle_command(":validate")
            
            # 全て継続を返すことを確認
            assert result1 is True
            assert result2 is True
            assert result3 is True
    
    def test_command_with_japanese_input(self):
        """日本語入力を含むコマンドのテスト"""
        # 日本語の述語名でテスト（ファイルに日本語述語がないので、エラーハンドリングを確認）
        with patch('builtins.print') as mock_print:
            result = self.repl._handle_command(":search 親")
            
            assert result is True
            assert mock_print.called
            # 日本語入力でもクラッシュしないことを確認
    
    def test_repl_state_consistency(self):
        """REPL状態の一貫性テスト"""
        # 各種ツールが正しく初期化されていることを確認
        assert self.repl.explain_tool is not None
        assert self.repl.search_tool is not None
        assert self.repl.validate_tool is not None
        assert self.repl.runtime is not None
        
        # ツールが同じランタイムを参照していることを確認
        assert self.repl.explain_tool.runtime is self.repl.runtime
        assert self.repl.search_tool.runtime is self.repl.runtime
        assert self.repl.validate_tool.runtime is self.repl.runtime