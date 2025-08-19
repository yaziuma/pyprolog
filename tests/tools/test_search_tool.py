"""
SearchToolのテスト

Prologルールと事実の検索機能のテストです。
"""
import pytest
from pyprolog.tools.search_tool import SearchTool
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Fact, Rule, Term, Atom


class TestSearchTool:
    """SearchToolのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        # テスト用のルールセットを作成
        rules = [
            Fact(Term(Atom("location"), [Atom("tokyo"), Atom("japan")])),
            Fact(Term(Atom("location"), [Atom("osaka"), Atom("japan")])),
            Fact(Term(Atom("population"), [Atom("tokyo"), Atom("14000000")])),
            Rule(
                Term(Atom("major_city"), [Atom("X")]),
                Term(Atom(","), [
                    Term(Atom("location"), [Atom("X"), Atom("japan")]),
                    Term(Atom("population"), [Atom("X"), Atom("P")]),
                    Term(Atom(">"), [Atom("P"), Atom("1000000")])
                ])
            ),
            Fact(Term(Atom("weather"), [Atom("tokyo"), Atom("sunny")])),
            Rule(
                Term(Atom("travel_advice"), [Atom("City"), Atom("Advice")]),
                Term(Atom(","), [
                    Term(Atom("weather"), [Atom("City"), Atom("sunny")]),
                    Term(Atom("="), [Atom("Advice"), Atom("good_for_sightseeing")])
                ])
            )
        ]
        
        self.runtime = Runtime(rules)
        self.search_tool = SearchTool(self.runtime)
    
    def test_search_tool_initialization(self):
        """SearchToolの初期化テスト"""
        assert self.search_tool.runtime is not None
        assert hasattr(self.search_tool, 'search_engine')
    
    def test_search_predicate_exact_match(self):
        """述語名での完全一致検索テスト"""
        result = self.search_tool.search_query("location", "predicate", 10)
        
        assert result["success"] is True
        assert result["result_count"] >= 2  # location/2の事実が2つ
        assert len(result["results"]) >= 2
        
        # 結果の内容をチェック
        for search_result in result["results"]:
            assert "location" in search_result["rule"]
    
    def test_search_predicate_partial_match(self):
        """述語名での部分一致検索テスト"""
        result = self.search_tool.search_query("loc", "predicate", 10)
        
        assert result["success"] is True
        # "location"が部分一致するはず
        assert result["result_count"] >= 1
    
    def test_search_argument_match(self):
        """引数での検索テスト"""
        result = self.search_tool.search_query("tokyo", "argument", 10)
        
        assert result["success"] is True
        assert result["result_count"] >= 1
        
        # tokyoが引数に含まれるルールが見つかるはず
        found_tokyo = any("tokyo" in res["rule"] for res in result["results"])
        assert found_tokyo
    
    def test_search_full_text_match(self):
        """全文検索テスト"""
        result = self.search_tool.search_query("japan", "full_text", 10)
        
        assert result["success"] is True
        assert result["result_count"] >= 1
        
        # japanが含まれるルールが見つかるはず
        found_japan = any("japan" in res["rule"] for res in result["results"])
        assert found_japan
    
    def test_search_with_limit(self):
        """検索結果数制限のテスト"""
        result = self.search_tool.search_query("location", "predicate", 1)
        
        assert result["success"] is True
        assert len(result["results"]) <= 1
        # result_count は制限後の件数を示す
        assert result["result_count"] <= 1
    
    def test_search_nonexistent_pattern(self):
        """存在しないパターンの検索テスト"""
        result = self.search_tool.search_query("nonexistent", "predicate", 10)
        
        assert result["success"] is True
        assert result["result_count"] == 0
        assert len(result["results"]) == 0
    
    def test_search_empty_pattern(self):
        """空パターンの検索テスト"""
        result = self.search_tool.search_query("", "predicate", 10)
        
        assert result["success"] is True
        # 現在の実装では、空パターンは全てにマッチする
        assert result["result_count"] == 6
    
    def test_search_invalid_type(self):
        """無効な検索タイプのテスト"""
        result = self.search_tool.search_query("location", "invalid_type", 10)
        
        # 無効なタイプでもエラーにならず、デフォルト動作をするはず
        assert result["success"] is True
    
    def test_format_results_text(self):
        """検索結果のテキスト形式フォーマットテスト"""
        result = self.search_tool.search_query("location", "predicate", 10)
        formatted = self.search_tool.format_results(result, "text")
        
        assert isinstance(formatted, str)
        assert "location" in formatted
        assert "検索結果" in formatted or "Search Results" in formatted or str(result["result_count"]) in formatted
    
    def test_format_results_json(self):
        """検索結果のJSON形式フォーマットテスト"""
        result = self.search_tool.search_query("location", "predicate", 10)
        formatted = self.search_tool.format_results(result, "json")
        
        assert isinstance(formatted, str)
        # JSON形式として解析可能かチェック
        import json
        parsed = json.loads(formatted)
        assert "success" in parsed
        assert "results" in parsed
    
    def test_format_results_table(self):
        """検索結果のテーブル形式フォーマットテスト"""
        result = self.search_tool.search_query("location", "predicate", 10)
        formatted = self.search_tool.format_results(result, "table")
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "No." in formatted
        assert "タイプ" in formatted
        assert "ルール" in formatted
    
    def test_get_search_statistics(self):
        """検索エンジン統計情報の取得テスト"""
        stats = self.search_tool.get_search_statistics()
        
        assert isinstance(stats, dict)
        assert "indexed" in stats
        assert "total_rules" in stats
        assert "predicate_index_size" in stats
        assert "argument_index_size" in stats
        assert "text_index_size" in stats
        assert "cache_valid" in stats
    
    def test_rebuild_index(self):
        """インデックス再構築テスト"""
        # 初回構築
        success = self.search_tool.rebuild_index()
        assert success is True
        
        # 統計情報を確認
        stats = self.search_tool.get_search_statistics()
        assert stats["indexed"] is True
        
        # 再構築
        success = self.search_tool.rebuild_index()
        assert success is True
    
    def test_search_after_index_rebuild(self):
        """インデックス再構築後の検索テスト"""
        # インデックスを再構築
        self.search_tool.rebuild_index()
        
        # 検索を実行
        result = self.search_tool.search_query("location", "predicate", 10)
        
        assert result["success"] is True
        assert result["result_count"] >= 2
    
    def test_search_complex_pattern(self):
        """複雑なパターンの検索テスト"""
        result = self.search_tool.search_query("major_city", "predicate", 10)
        
        assert result["success"] is True
        if result["result_count"] > 0:
            # major_cityルールが見つかるはず
            found_major_city = any("major_city" in res["rule"] for res in result["results"])
            assert found_major_city
    
    def test_search_case_sensitivity(self):
        """大文字小文字の扱いテスト"""
        result_lower = self.search_tool.search_query("tokyo", "argument", 10)
        result_upper = self.search_tool.search_query("TOKYO", "argument", 10)
        
        # 実装依存だが、少なくともエラーにならないことを確認
        assert result_lower["success"] is True
        assert result_upper["success"] is True
        assert result_lower["result_count"] == result_upper["result_count"]

    # --- Tests for parse_search_command ---

    def test_parse_search_full_command(self):
        """'parse_search_command' with all arguments"""
        command = 'search("location", "predicate", 50).'
        pattern, search_type, limit = self.search_tool.parse_search_command(command)
        assert pattern == 'location'
        assert search_type == "predicate"
        assert limit == 50

    def test_parse_search_command_with_default_limit(self):
        """'parse_search_command' with default limit"""
        command = 'search("tokyo", "argument").'
        pattern, search_type, limit = self.search_tool.parse_search_command(command)
        assert pattern == 'tokyo'
        assert search_type == "argument"
        assert limit == 100

    def test_parse_search_command_with_default_type_and_limit(self):
        """'parse_search_command' with default type and limit"""
        command = 'search("japan").'
        pattern, search_type, limit = self.search_tool.parse_search_command(command)
        assert pattern == 'japan'
        assert search_type == "predicate"
        assert limit == 100

    def test_parse_search_invalid_command_format(self):
        """'parse_search_command' with an invalid format"""
        command = 'find("bad format").'
        # The parser should return the original command as pattern and defaults for others
        pattern, search_type, limit = self.search_tool.parse_search_command(command)
        assert pattern == 'find("bad format").'
        assert search_type == "predicate"
        assert limit == 100