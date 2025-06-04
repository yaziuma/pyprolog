"""ログ設定管理モジュール

通常利用時とテスト時でログ設定を分けて管理します。
設定ファイル（.conf）ベースでログ設定を管理します。
"""
import os
import sys
import logging.config
from pathlib import Path
from typing import Optional, List, Dict, Any


def get_config_file_path(environment: str) -> Path:
    """指定された環境の設定ファイルパスを取得します。
    
    Args:
        environment: 環境名（'production', 'test', 'debug'）
        
    Returns:
        設定ファイルのパス
        
    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
    """
    # プロジェクトルートから設定ファイルを探す
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    config_file = project_root / "config" / "logging" / f"{environment}.conf"
    
    if not config_file.exists():
        raise FileNotFoundError(f"ログ設定ファイルが見つかりません: {config_file}")
    
    return config_file


def setup_logs_directory():
    """ログディレクトリを作成します。"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)


def detect_environment() -> str:
    """実行環境を自動検出します。
    
    Returns:
        環境名（'test', 'debug', 'production'）
    """
    # pytest実行中の検出
    if "PYTEST_CURRENT_TEST" in os.environ:
        return "test"
    
    # unittest実行中の検出
    if any("unittest" in arg for arg in sys.argv if arg):
        return "test"
    
    # デバッグモードの検出
    if os.environ.get("PROLOG_DEBUG", "").lower() in ("1", "true", "yes"):
        return "debug"
    
    # 開発環境の検出
    if os.environ.get("PROLOG_ENV", "").lower() == "development":
        return "debug"
    
    # デフォルトは本番環境
    return "production"


def load_logging_config(environment: str) -> None:
    """指定された環境のログ設定を読み込みます。
    
    Args:
        environment: 環境名（'production', 'test', 'debug'）
        
    Raises:
        ValueError: 未知の環境名が指定された場合
        FileNotFoundError: 設定ファイルが見つからない場合
    """
    valid_environments = {"production", "test", "debug"}
    if environment not in valid_environments:
        raise ValueError(f"未知の環境: {environment}. 使用可能な環境: {valid_environments}")
    
    # ログディレクトリを作成
    setup_logs_directory()
    
    # 設定ファイルを読み込み
    config_file = get_config_file_path(environment)
    logging.config.fileConfig(config_file, disable_existing_loggers=False)


def get_available_environments() -> List[str]:
    """利用可能な環境一覧を取得します。
    
    Returns:
        利用可能な環境名のリスト
    """
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        config_dir = project_root / "config" / "logging"
        
        if not config_dir.exists():
            return []
        
        environments = []
        for config_file in config_dir.glob("*.conf"):
            environments.append(config_file.stem)
        
        return sorted(environments)
    except Exception:
        return ["production", "test", "debug"]  # フォールバック


def validate_config_files() -> Dict[str, bool]:
    """すべての設定ファイルの存在を確認します。
    
    Returns:
        環境名と存在確認結果の辞書
    """
    environments = ["production", "test", "debug"]
    results = {}
    
    for env in environments:
        try:
            config_file = get_config_file_path(env)
            results[env] = config_file.exists()
        except Exception:
            results[env] = False
    
    return results


def get_config_info(environment: str) -> Dict[str, Any]:
    """指定された環境の設定情報を取得します。
    
    Args:
        environment: 環境名
        
    Returns:
        設定情報の辞書
    """
    try:
        config_file = get_config_file_path(environment)
        return {
            "environment": environment,
            "config_file": str(config_file),
            "exists": config_file.exists(),
            "size": config_file.stat().st_size if config_file.exists() else 0,
            "modified": config_file.stat().st_mtime if config_file.exists() else None
        }
    except Exception as e:
        return {
            "environment": environment,
            "config_file": None,
            "exists": False,
            "error": str(e)
        }