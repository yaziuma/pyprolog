#!/usr/bin/env python3
"""ログ設定ファイルの動作確認デモ

このファイルは、設定ファイルベースのログシステムの動作を確認するためのデモです。
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prolog.util.logger import (
    get_logger, 
    setup_logging, 
    switch_to_debug_mode, 
    switch_to_test_mode,
    switch_to_production_mode,
    get_current_environment,
    get_logging_info,
    reset_logging
)
from prolog.util.logging_config import (
    get_available_environments,
    validate_config_files,
    get_config_info
)


def demo_config_validation():
    """設定ファイルの検証デモ"""
    print("=== ログ設定ファイルの検証 ===")
    
    # 利用可能な環境を表示
    environments = get_available_environments()
    print(f"利用可能な環境: {environments}")
    
    # 各設定ファイルの存在確認
    validation_results = validate_config_files()
    print("\n設定ファイルの存在確認:")
    for env, exists in validation_results.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {env}.conf")
    
    print()


def demo_environment_detection():
    """環境検出のデモ"""
    print("=== 環境検出デモ ===")
    
    current_env = get_current_environment()
    print(f"現在の環境: {current_env}")
    
    # 環境変数を設定して検出テスト
    print("\n環境変数による検出テスト:")
    
    # デバッグ環境
    os.environ["PROLOG_DEBUG"] = "1"
    reset_logging()
    setup_logging()
    print(f"PROLOG_DEBUG=1 -> {get_current_environment()}")
    
    # 開発環境
    del os.environ["PROLOG_DEBUG"]
    os.environ["PROLOG_ENV"] = "development"
    reset_logging()
    setup_logging()
    print(f"PROLOG_ENV=development -> {get_current_environment()}")
    
    # クリーンアップ
    if "PROLOG_ENV" in os.environ:
        del os.environ["PROLOG_ENV"]
    
    print()


def demo_basic_logging():
    """基本的なログ出力デモ"""
    print("=== 基本的なログ出力デモ ===")
    
    logger = get_logger("demo.basic")
    
    print(f"現在の環境: {get_current_environment()}")
    print("以下のログが設定に応じて出力されます:")
    
    logger.debug("デバッグ情報: 詳細な処理情報")
    logger.info("情報: 通常の処理完了")
    logger.warning("警告: 非推奨機能の使用")
    logger.error("エラー: 処理に失敗しました")
    
    print()


def demo_environment_switching():
    """環境切り替えデモ"""
    print("=== 環境切り替えデモ ===")
    
    logger = get_logger("demo.switching")
    
    # 本番モード
    print("本番モードでのログ出力:")
    switch_to_production_mode()
    logger.info("本番環境での処理")
    logger.debug("本番環境でのデバッグ情報（ファイルのみ出力）")
    
    # デバッグモード
    print("\nデバッグモードでのログ出力:")
    switch_to_debug_mode()
    logger.info("デバッグ環境での処理")
    logger.debug("デバッグ環境でのデバッグ情報（コンソールにも出力）")
    
    # テストモード
    print("\nテストモードでのログ出力:")
    switch_to_test_mode()
    logger.warning("テスト環境での警告（出力される）")
    logger.info("テスト環境での情報（出力されない）")
    
    print()


def demo_config_info():
    """設定情報表示デモ"""
    print("=== 設定情報表示デモ ===")
    
    # 現在のログ設定情報を表示
    info = get_logging_info()
    print("現在のログ設定情報:")
    print(f"  初期化済み: {info['initialized']}")
    print(f"  現在の環境: {info['current_environment']}")
    print(f"  設定ファイル: {info['config_info']['config_file']}")
    print(f"  ファイル存在: {info['config_info']['exists']}")
    
    # ロガー情報
    print("  ロガー情報:")
    for logger_name, logger_info in info['loggers'].items():
        print(f"    {logger_name}: レベル={logger_info['level']}, ハンドラ数={logger_info['handlers']}")
    
    # 各環境の設定情報
    print("\n各環境の設定ファイル情報:")
    for env in ["production", "test", "debug"]:
        config_info = get_config_info(env)
        if config_info['exists']:
            print(f"  {env}: {config_info['config_file']} ({config_info['size']} bytes)")
        else:
            print(f"  {env}: ファイルが見つかりません")
    
    print()


def demo_module_specific_loggers():
    """モジュール固有ロガーのデモ"""
    print("=== モジュール固有ロガーのデモ ===")
    
    # 異なるモジュール名でロガーを作成
    parser_logger = get_logger("parser")
    runtime_logger = get_logger("runtime") 
    core_logger = get_logger("core")
    
    print("各モジュールからのログ出力:")
    parser_logger.info("パーサーモジュール: 構文解析完了")
    runtime_logger.info("ランタイムモジュール: クエリ実行中")
    core_logger.info("コアモジュール: 単一化処理")
    
    print()


def main():
    """メインデモ実行"""
    print("ログ設定ファイルベースシステム デモ")
    print("=" * 50)
    
    try:
        demo_config_validation()
        demo_environment_detection()
        demo_basic_logging()
        demo_environment_switching()
        demo_config_info()
        demo_module_specific_loggers()
        
        print("デモ完了！")
        print(f"ログファイルを確認してください: {project_root}/logs/")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()