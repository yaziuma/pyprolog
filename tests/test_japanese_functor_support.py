"""
PyProlog日本語ファンクター機能の統合テストスイート

このテストファイルは、今回実装した日本語ファンクター機能のすべての側面をテストします：
- FunctorMapper単体機能
- Scanner統合
- Parser統合  
- Runtime統合
- エンドツーエンド機能
"""

import unittest
from pyprolog.util.functor_mapper import FunctorMapper
from pyprolog.util.variable_mapper import VariableMapper
from pyprolog.parser.scanner import Scanner
from pyprolog.parser.parser import Parser
from pyprolog.runtime.interpreter import Runtime


class TestJapaneseFunctorSupport(unittest.TestCase):
    """日本語ファンクターサポートの統合テスト"""
    
    def setUp(self):
        """各テストの前準備"""
        self.functor_mapper = FunctorMapper()
        self.variable_mapper = VariableMapper()
        self.runtime = Runtime(
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        )
    
    def test_functor_mapper_basic_functionality(self):
        """FunctorMapper基本機能テスト"""
        mapper = FunctorMapper()
        
        # 日本語ファンクターのマッピング必要性判定
        self.assertTrue(mapper.needs_mapping("親"))
        self.assertTrue(mapper.needs_mapping("男性"))
        self.assertFalse(mapper.needs_mapping("parent"))
        self.assertFalse(mapper.needs_mapping("test123"))
        
        # Unicode文字対応
        self.assertTrue(mapper.needs_mapping("café"))  # フランス語
        self.assertTrue(mapper.needs_mapping("α"))     # ギリシャ文字
        
        # マッピング生成
        mapped = mapper.map_non_ascii_to_english("親")
        self.assertTrue(mapped.startswith("MAPPED_F"))
        
        # 逆マッピング
        recovered = mapper.map_english_to_non_ascii(mapped)
        self.assertEqual(recovered, "親")
    
    def test_scanner_integration(self):
        """Scanner統合テスト"""
        test_source = '親(太郎, 花子).'
        scanner = Scanner(
            test_source, 
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        )
        tokens = scanner.scan_tokens()
        
        # トークン数確認（親, (, 太郎, ,, 花子, ), ., EOF = 8個）
        self.assertEqual(len(tokens), 8)
        
        # ファンクター名マッピング確認
        parent_token = tokens[0]
        self.assertEqual(parent_token.lexeme, "親")
        self.assertTrue(parent_token.literal.startswith("MAPPED_F"))
        
        # アトムマッピング確認
        taro_token = tokens[2]
        self.assertEqual(taro_token.lexeme, "太郎")
        self.assertTrue(taro_token.literal.startswith("MAPPED_F"))
    
    def test_variable_vs_functor_distinction(self):
        """変数とファンクターの区別テスト"""
        test_cases = [
            ('親(太郎, 花子).', ['ATOM', 'ATOM', 'ATOM']),  # 全てアトム
            ('親(X, Y).', ['ATOM', 'VARIABLE', 'VARIABLE']), # 混在
            ('親(太郎, X).', ['ATOM', 'ATOM', 'VARIABLE']),  # 混在
        ]
        
        for source, expected_types in test_cases:
            scanner = Scanner(
                source,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper
            )
            tokens = scanner.scan_tokens()
            
            # 主要トークンの型チェック（親、引数1、引数2）
            actual_types = [
                tokens[0].token_type.name,  # 親
                tokens[2].token_type.name,  # 第1引数
                tokens[4].token_type.name   # 第2引数
            ]
            
            self.assertEqual(actual_types, expected_types, 
                           f"Source: {source}, Expected: {expected_types}, Actual: {actual_types}")
    
    def test_parser_integration(self):
        """Parser統合テスト"""
        test_source = '親(太郎, 花子).'
        scanner = Scanner(
            test_source,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        )
        tokens = scanner.scan_tokens()
        
        parser = Parser(
            tokens,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        )
        results = parser.parse()
        
        # パース結果の確認
        self.assertEqual(len(results), 1)
        fact = results[0]
        self.assertEqual(fact.__class__.__name__, 'Fact')
    
    def test_runtime_integration(self):
        """Runtime統合テスト"""
        # 日本語ルール追加
        rules = [
            "親(太郎, 花子).",
            "親(太郎, 次郎).", 
            "男性(太郎).",
            "男性(次郎).",
            "女性(花子).",
        ]
        
        for rule in rules:
            result = self.runtime.add_rule(rule)
            self.assertTrue(result, f"ルール追加失敗: {rule}")
        
        # クエリ実行テスト
        queries = [
            "親(太郎, X).",   # 2件の結果期待
            "男性(Y).",       # 2件の結果期待
            "女性(Z).",       # 1件の結果期待
        ]
        
        for query in queries:
            results = self.runtime.query(query)
            self.assertGreater(len(results), 0, f"クエリ結果なし: {query}")
    
    def test_collision_avoidance(self):
        """衝突回避機能テスト"""
        existing_functors = {'MAPPED_F1', 'MAPPED_F2', 'parent'}
        mapper = FunctorMapper(existing_functors)
        
        # 新しいマッピングが既存と衝突しないことを確認
        mapped = mapper.map_non_ascii_to_english('親')
        self.assertNotIn(mapped, existing_functors)
        self.assertTrue(mapped.startswith('MAPPED_F'))
    
    def test_unicode_character_sets(self):
        """多言語Unicode文字セットテスト"""
        test_cases = [
            ("親", "日本語"),
            ("café", "フランス語"),
            ("α", "ギリシャ文字"),
            ("тест", "キリル文字"),
            ("测试", "中国語"),
        ]
        
        mapper = FunctorMapper()
        mappings = {}
        
        for char, lang in test_cases:
            # マッピング必要性確認
            self.assertTrue(mapper.needs_mapping(char), f"{lang}文字 '{char}' のマッピングが必要と判定されない")
            
            # マッピング生成
            mapped = mapper.map_non_ascii_to_english(char)
            mappings[char] = mapped
            self.assertTrue(mapped.startswith("MAPPED_F"), f"{lang}文字のマッピング形式が不正: {mapped}")
            
            # 逆マッピング確認
            recovered = mapper.map_english_to_non_ascii(mapped)
            self.assertEqual(recovered, char, f"{lang}文字の逆マッピングが失敗: {char} -> {mapped} -> {recovered}")
    
    def test_performance_large_scale(self):
        """大規模マッピング性能テスト"""
        import time
        
        mapper = FunctorMapper()
        start_time = time.time()
        
        # 1000個のユニークなマッピングを生成
        for i in range(1000):
            functor = f"述語{i}"
            mapped = mapper.map_non_ascii_to_english(functor)
            recovered = mapper.map_english_to_non_ascii(mapped)
            self.assertEqual(recovered, functor)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 1000件のマッピングが1秒以内に完了することを確認
        self.assertLess(elapsed, 1.0, f"大規模マッピングの性能が低下: {elapsed:.2f}秒")
    
    def test_mapping_consistency(self):
        """マッピングの一貫性テスト"""
        mapper = FunctorMapper()
        
        # 同じファンクターは常に同じマッピングを返すことを確認
        functor = "親"
        mapped1 = mapper.map_non_ascii_to_english(functor)
        mapped2 = mapper.map_non_ascii_to_english(functor)
        
        self.assertEqual(mapped1, mapped2, "同一ファンクターのマッピングが一貫していない")
        
        # 異なるFunctorMapperインスタンスでも一貫性を保つことを確認
        mapper2 = FunctorMapper()
        mapped3 = mapper2.map_non_ascii_to_english(functor)
        
        # 実装では、異なるインスタンスでも同じマッピングを生成する
        # （決定論的なマッピング生成）
        self.assertEqual(mapped1, mapped3, "異なるインスタンスで異なるマッピングが生成された")
    
    def test_complex_japanese_expressions(self):
        """複雑な日本語表現テスト"""
        complex_rules = [
            "父親(X, Y) :- 親(X, Y), 男性(X).",
            "母親(X, Y) :- 親(X, Y), 女性(X).",
            "祖父(X, Z) :- 父親(X, Y), 親(Y, Z).",
        ]
        
        for rule in complex_rules:
            try:
                result = self.runtime.add_rule(rule)
                self.assertTrue(result, f"複雑な日本語ルール追加失敗: {rule}")
            except Exception as e:
                self.fail(f"複雑な日本語ルールでエラー: {rule} - {e}")


def run_all_tests():
    """全テストを実行し、結果を表示"""
    print("=" * 60)
    print("PyProlog 日本語ファンクター機能 統合テストスイート")
    print("=" * 60)
    
    # テストスイート作成
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestJapaneseFunctorSupport)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)