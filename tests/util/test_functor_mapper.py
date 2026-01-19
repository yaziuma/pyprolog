from pyprolog.util.functor_mapper import FunctorMapper


class TestFunctorMapper:
    """FunctorMapperの単体テスト"""

    def test_needs_mapping_japanese_functors(self):
        """日本語ファンクターのマッピング必要性テスト"""
        mapper = FunctorMapper()

        # 日本語ファンクター（マッピング必要）
        assert mapper.needs_mapping("親")
        assert mapper.needs_mapping("男性")
        assert mapper.needs_mapping("疾患名")
        assert mapper.needs_mapping("test親")  # 混在
        assert mapper.needs_mapping("親_test")  # 混在

        # 英語ファンクター（マッピング不要）
        assert not mapper.needs_mapping("parent")
        assert not mapper.needs_mapping("male")
        assert not mapper.needs_mapping("disease_name")
        assert not mapper.needs_mapping("test123")

    def test_needs_mapping_unicode_functors(self):
        """Unicode文字のマッピング必要性テスト"""
        mapper = FunctorMapper()

        # 全角英数字（マッピング必要）
        assert mapper.needs_mapping("ＰＡＲＥＮＴ")
        assert mapper.needs_mapping("ｔｅｓｔ１")
        assert mapper.needs_mapping("テスト１２３")

        # その他のUnicode文字（マッピング必要）
        assert mapper.needs_mapping("café")  # フランス語（アクセント付き）
        assert mapper.needs_mapping("α")  # ギリシャ文字
        assert mapper.needs_mapping("родитель")  # キリル文字
        assert mapper.needs_mapping("测试")  # 中国語（簡体字）

        # ASCII文字（マッピング不要）
        assert not mapper.needs_mapping("test")
        assert not mapper.needs_mapping("parent123")
        assert not mapper.needs_mapping("TEST_FUNC")

    def test_needs_mapping_unsafe_characters(self):
        """安全でない文字のマッピング必要性テスト"""
        mapper = FunctorMapper()

        # 区切り文字を含む（マッピング必要）
        assert mapper.needs_mapping("test,name")
        assert mapper.needs_mapping("func(test)")
        assert mapper.needs_mapping("name.ext")
        assert mapper.needs_mapping("test:name")

        # 安全な文字のみ（マッピング不要）
        assert not mapper.needs_mapping("test_name")
        assert not mapper.needs_mapping("TestName123")
        assert not mapper.needs_mapping("func_test_123")

    def test_mapping_generation_consistency(self):
        """マッピング生成の一貫性テスト"""
        mapper = FunctorMapper()

        # 初回マッピング
        mapped1 = mapper.map_non_ascii_to_english("親")
        mapped2 = mapper.map_non_ascii_to_english("男性")

        # 期待されるパターン
        assert mapped1.startswith("MAPPED_F")
        assert mapped2.startswith("MAPPED_F")
        assert mapped1 != mapped2

        # 重複呼び出しで同じ結果
        assert mapper.map_non_ascii_to_english("親") == mapped1
        assert mapper.map_non_ascii_to_english("男性") == mapped2

        # 逆マッピング
        assert mapper.map_english_to_non_ascii(mapped1) == "親"
        assert mapper.map_english_to_non_ascii(mapped2) == "男性"

    def test_non_ascii_passthrough(self):
        """非マッピング対象のパススルーテスト"""
        mapper = FunctorMapper()

        # 英語はそのまま通す
        assert mapper.map_non_ascii_to_english("parent") == "parent"
        assert mapper.map_english_to_non_ascii("parent") == "parent"

        # 数字のみもそのまま通す
        assert mapper.map_non_ascii_to_english("123") == "123"
        assert mapper.map_english_to_non_ascii("123") == "123"

    def test_existing_functor_collision_avoidance(self):
        """既存ファンクターとの衝突回避テスト"""
        # 既存ファンクターを含むマッパー
        existing = {"MAPPED_F1", "MAPPED_F2", "parent", "child"}
        mapper = FunctorMapper(existing)

        # 日本語ファンクターのマッピング
        mapped1 = mapper.map_non_ascii_to_english("親")
        mapped2 = mapper.map_non_ascii_to_english("子")

        # 既存ファンクターと衝突しないことを確認
        assert mapped1 not in existing
        assert mapped2 not in existing
        assert mapped1 != mapped2

        # プレフィックスパターンの確認
        assert mapped1.startswith("MAPPED_F")
        assert mapped2.startswith("MAPPED_F")

        # 既存ファンクターはそのまま通ることを確認
        assert mapper.map_non_ascii_to_english("parent") == "parent"

    def test_register_existing_functors(self):
        """既存ファンクター動的登録テスト"""
        mapper = FunctorMapper()

        # 初期状態
        assert len(mapper.get_existing_functors()) == 0

        # ファンクター登録
        new_functors = {"test1", "test2", "MAPPED_F1"}
        mapper.register_existing_functors(new_functors)

        # 登録確認
        existing = mapper.get_existing_functors()
        assert len(existing) == 3
        assert "test1" in existing
        assert "test2" in existing
        assert "MAPPED_F1" in existing

        # マッピング時に衝突回避されることを確認
        mapped = mapper.map_non_ascii_to_english("親")
        assert mapped not in existing

    def test_extract_functors_from_string(self):
        """文字列からのファンクター抽出テスト"""
        mapper = FunctorMapper()

        # 基本的なファクト
        functors = mapper.extract_functors_from_string("parent(tom, bob).")
        assert "parent" in functors

        # 複数のファンクター
        functors = mapper.extract_functors_from_string(
            "parent(X, Y) :- father(X, Y), male(X)."
        )
        assert "parent" in functors
        assert "father" in functors
        assert "male" in functors

        # 複雑な式
        functors = mapper.extract_functors_from_string(
            "test_func(a, b), another_func(c)."
        )
        assert "test_func" in functors
        assert "another_func" in functors

    def test_clear_mapping(self):
        """マッピングクリアテスト"""
        mapper = FunctorMapper()

        # マッピング作成
        mapped1 = mapper.map_non_ascii_to_english("親")
        mapped2 = mapper.map_non_ascii_to_english("子")

        # マッピング存在確認
        non_ascii_map, english_map = mapper.get_all_mappings()
        assert len(non_ascii_map) == 2
        assert len(english_map) == 2

        # クリア
        mapper.clear_mapping()

        # クリア確認
        non_ascii_map, english_map = mapper.get_all_mappings()
        assert len(non_ascii_map) == 0
        assert len(english_map) == 0

    def test_large_scale_mapping_performance(self):
        """大規模マッピングの性能テスト"""
        mapper = FunctorMapper()

        # 1000個の日本語ファンクターをマッピング
        import time

        start_time = time.time()

        for i in range(1000):
            japanese_name = f"述語{i}"
            english_name = mapper.map_non_ascii_to_english(japanese_name)
            recovered_name = mapper.map_english_to_non_ascii(english_name)
            assert recovered_name == japanese_name

        end_time = time.time()

        # 1秒以内で完了することを確認
        assert end_time - start_time < 1.0

    def test_mixed_character_sets(self):
        """混在文字セットのテスト"""
        mapper = FunctorMapper()

        # 日本語+英語混在
        mixed1 = "親_parent"
        mapped1 = mapper.map_non_ascii_to_english(mixed1)
        assert mapped1.startswith("MAPPED_F")
        assert mapper.map_english_to_non_ascii(mapped1) == mixed1

        # Unicode+ASCII混在
        mixed2 = "café_test"
        mapped2 = mapper.map_non_ascii_to_english(mixed2)
        assert mapped2.startswith("MAPPED_F")
        assert mapper.map_english_to_non_ascii(mapped2) == mixed2
