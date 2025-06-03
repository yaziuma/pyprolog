#!/usr/bin/env python3
"""
PyProlog動的ルール追加サンプル
実行時のルール追加、データベースの動的更新、複雑なルール構築
"""

from prolog import Runtime
from prolog.core.errors import PrologError

def demonstrate_basic_dynamic_rules():
    """基本的な動的ルール追加"""
    print("=== 基本的な動的ルール追加 ===")
    
    runtime = Runtime()
    
    # 段階的にルールを追加
    print("段階1: 基本的なファクトの追加")
    basic_facts = [
        "city(tokyo).",
        "city(osaka).",
        "city(kyoto).",
        "population(tokyo, 14000000).",
        "population(osaka, 2700000).",
        "population(kyoto, 1500000)."
    ]
    
    for fact in basic_facts:
        runtime.add_rule(fact)
        print(f"  + {fact}")
    
    # 追加されたファクトをテスト
    print("\n追加されたファクトのテスト:")
    results = runtime.query("city(X)")
    print(f"  都市: {len(results)}件")
    for result in results:
        for var_name, value in result.items():
            if str(var_name) == 'X' or (hasattr(var_name, 'name') and var_name.name == 'X'):
                print(f"    - {value}")
                break
    
    print("\n段階2: ルールの追加")
    rules = [
        "large_city(X) :- population(X, P), P > 5000000.",
        "medium_city(X) :- population(X, P), P > 1000000, P =< 5000000.",
        "small_city(X) :- population(X, P), P =< 1000000."
    ]
    
    for rule in rules:
        runtime.add_rule(rule)
        print(f"  + {rule}")
    
    # ルールのテスト
    print("\nルールのテスト:")
    rule_tests = [
        ("large_city(X)", "大都市"),
        ("medium_city(X)", "中都市"),
        ("small_city(X)", "小都市")
    ]
    
    for query, description in rule_tests:
        results = runtime.query(query)
        print(f"  {description}: {len(results)}件")
        for result in results:
            for var_name, value in result.items():
                if str(var_name) == 'X' or (hasattr(var_name, 'name') and var_name.name == 'X'):
                    print(f"    - {value}")
                    break
    
    print()

def demonstrate_dynamic_database_operations():
    """動的データベース操作（asserta/assertz）"""
    print("=== 動的データベース操作 ===")
    
    runtime = Runtime()
    
    # 初期データ
    print("初期データの設定:")
    initial_data = [
        "student(alice, 20).",
        "student(bob, 22).",
        "grade(alice, math, 85).",
        "grade(bob, math, 78)."
    ]
    
    for data in initial_data:
        runtime.add_rule(data)
        print(f"  + {data}")
    
    print("\n初期状態のクエリ:")
    results = runtime.query("student(X, Age)")
    print(f"  学生数: {len(results)}名")
    
    # assertaを使った先頭追加
    print("\nassertaを使った先頭追加:")
    runtime.query("asserta(student(charlie, 19))")
    runtime.query("asserta(grade(charlie, math, 92))")
    print("  + student(charlie, 19) を先頭に追加")
    print("  + grade(charlie, math, 92) を先頭に追加")
    
    # assertzを使った末尾追加
    print("\nassertzを使った末尾追加:")
    runtime.query("assertz(student(diana, 21))")
    runtime.query("assertz(grade(diana, math, 88))")
    print("  + student(diana, 21) を末尾に追加")
    print("  + grade(diana, math, 88) を末尾に追加")
    
    # 更新後の状態を確認
    print("\n更新後の学生一覧:")
    results = runtime.query("student(X, Age)")
    print(f"  学生数: {len(results)}名")
    for i, result in enumerate(results, 1):
        name = age = None
        for var_name, value in result.items():
            var_str = str(var_name)
            if var_str == 'X' or (hasattr(var_name, 'name') and var_name.name == 'X'):
                name = value
            elif var_str == 'Age' or (hasattr(var_name, 'name') and var_name.name == 'Age'):
                age = value
        print(f"    {i}. {name} ({age}歳)")
    
    # 成績の確認
    print("\n数学の成績一覧:")
    results = runtime.query("grade(Student, math, Score)")
    for result in results:
        student = score = None
        for var_name, value in result.items():
            var_str = str(var_name)
            if var_str == 'Student' or (hasattr(var_name, 'name') and var_name.name == 'Student'):
                student = value
            elif var_str == 'Score' or (hasattr(var_name, 'name') and var_name.name == 'Score'):
                score = value
        print(f"  {student}: {score}点")
    
    print()

def demonstrate_complex_rule_construction():
    """複雑なルール構築"""
    print("=== 複雑なルール構築 ===")
    
    runtime = Runtime()
    
    # 商品データベースの構築
    print("商品データベースの構築:")
    product_data = [
        "product(laptop, electronics, 80000).",
        "product(smartphone, electronics, 60000).",
        "product(book, media, 1500).",
        "product(chair, furniture, 15000).",
        "product(desk, furniture, 25000).",
        "product(tablet, electronics, 40000)."
    ]
    
    for data in product_data:
        runtime.add_rule(data)
        print(f"  + {data}")
    
    # 在庫と割引情報を動的に追加
    print("\n在庫と割引情報の動的追加:")
    inventory_rules = [
        "stock(laptop, 5).",
        "stock(smartphone, 10).",
        "stock(book, 100).",
        "stock(chair, 20).",
        "stock(desk, 8).",
        "stock(tablet, 15).",
        "discount(electronics, 0.1).",  # 10%割引
        "discount(media, 0.05).",       # 5%割引
        "discount(furniture, 0.15).",   # 15%割引
    ]
    
    for rule in inventory_rules:
        runtime.add_rule(rule)
        print(f"  + {rule}")
    
    # 複雑なビジネスルールを追加
    print("\nビジネスルールの追加:")
    business_rules = [
        "available(Product) :- stock(Product, Quantity), Quantity > 0.",
        "expensive(Product) :- product(Product, _, Price), Price > 50000.",
        "affordable(Product) :- product(Product, _, Price), Price =< 30000.",
        "discounted_price(Product, FinalPrice) :- product(Product, Category, Price), discount(Category, Rate), FinalPrice is Price * (1 - Rate).",
        "low_stock(Product) :- stock(Product, Quantity), Quantity < 10.",
        "category_average(Category, Avg) :- findall(Price, product(_, Category, Price), Prices), average(Prices, Avg).",
        "bestseller(Product) :- product(Product, electronics, _), stock(Product, Quantity), Quantity > 5."
    ]
    
    for rule in business_rules:
        try:
            runtime.add_rule(rule)
            print(f"  + {rule}")
        except Exception as e:
            print(f"  ✗ エラー: {rule} - {e}")
    
    # 構築されたルールのテスト
    print("\nビジネスルールのテスト:")
    business_queries = [
        ("available(X)", "在庫あり商品"),
        ("expensive(X)", "高額商品"),
        ("affordable(X)", "手頃な商品"),
        ("low_stock(X)", "在庫少商品"),
        ("discounted_price(laptop, Price)", "ラップトップの割引価格")
    ]
    
    for query, description in business_queries:
        try:
            results = runtime.query(query)
            print(f"  {description}: {len(results)}件")
            if len(results) <= 5:  # 5件以下なら詳細表示
                for result in results:
                    var_strs = []
                    for var_name, value in result.items():
                        var_strs.append(f"{var_name}={value}")
                    if var_strs:
                        print(f"    - {', '.join(var_strs)}")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    print()

def demonstrate_conditional_rule_addition():
    """条件付きルール追加"""
    print("=== 条件付きルール追加 ===")
    
    runtime = Runtime()
    
    # 基本データ
    base_data = [
        "employee(alice, manager, 5).",
        "employee(bob, developer, 3).",
        "employee(charlie, developer, 1).",
        "employee(diana, designer, 2)."
    ]
    
    for data in base_data:
        runtime.add_rule(data)
        print(f"基本データ: {data}")
    
    # 条件に基づいて動的にルールを追加
    print("\n条件に基づく動的ルール追加:")
    
    # 経験年数に基づくレベル分け
    experience_levels = [
        ("senior_employee(X) :- employee(X, _, Years), Years >= 5.", "シニア従業員"),
        ("junior_employee(X) :- employee(X, _, Years), Years < 2.", "ジュニア従業員"),
        ("mid_employee(X) :- employee(X, _, Years), Years >= 2, Years < 5.", "中堅従業員")
    ]
    
    for rule, description in experience_levels:
        runtime.add_rule(rule)
        print(f"  + {description}: {rule}")
    
    # 職種別の特別ルール
    print("\n職種別特別ルールの追加:")
    
    # 開発者が複数いる場合のチームルール
    dev_count_result = runtime.query("findall(X, employee(X, developer, _), Devs)")
    if dev_count_result:
        devs = None
        for var_name, value in dev_count_result[0].items():
            if str(var_name) == 'Devs' or (hasattr(var_name, 'name') and var_name.name == 'Devs'):
                devs = value
                break
        
        if devs and len(str(devs)) > 10:  # 簡易的な開発者数チェック
            team_rules = [
                "dev_team_member(X) :- employee(X, developer, _).",
                "can_pair_program(X, Y) :- dev_team_member(X), dev_team_member(Y), X \\= Y.",
                "team_lead(X) :- employee(X, developer, Years), Years >= 3."
            ]
            
            for rule in team_rules:
                runtime.add_rule(rule)
                print(f"  + 開発チームルール: {rule}")
    
    # 追加されたルールのテスト
    print("\n追加されたルールのテスト:")
    level_queries = [
        ("senior_employee(X)", "シニア従業員"),
        ("junior_employee(X)", "ジュニア従業員"),
        ("mid_employee(X)", "中堅従業員"),
        ("dev_team_member(X)", "開発チームメンバー"),
        ("can_pair_program(X, Y)", "ペアプログラミング可能")
    ]
    
    for query, description in level_queries:
        try:
            results = runtime.query(query)
            print(f"  {description}: {len(results)}件")
            if len(results) <= 3:
                for result in results:
                    var_strs = []
                    for var_name, value in result.items():
                        var_strs.append(f"{var_name}={value}")
                    if var_strs:
                        print(f"    - {', '.join(var_strs)}")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    print()

def main():
    """メイン関数"""
    print("PyProlog動的ルール追加サンプル")
    print("=" * 50)
    print()
    
    demonstrate_basic_dynamic_rules()
    demonstrate_dynamic_database_operations()
    demonstrate_complex_rule_construction()
    demonstrate_conditional_rule_addition()
    
    print("動的ルール追加サンプルが完了しました。")

if __name__ == "__main__":
    main()