import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ログ保存ディレクトリの設定
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# ログファイルパスの設定
LOG_FILE = LOG_DIR / "app.log"


def setup_logger(name: str = "prolog_mcp") -> logging.Logger:
    """アプリケーション全体で使用するロガーを設定します。

    Args:
        name: ロガー名。デフォルトは 'prolog_mcp' です。

    Returns:
        設定済みのロガーインスタンス。
    """
    logger = logging.getLogger(name)

    # 既に設定済みの場合は既存のロガーを返す
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ログフォーマットの設定
    formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # ファイルハンドラの設定（ログローテーション付き）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding="utf-8",
    )
    # pytest実行中はファイルへのログ出力を抑制する
    if "PYTEST_CURRENT_TEST" in os.environ:
        file_handler.setLevel(logging.CRITICAL + 1)  # CRITICALより上のレベルを設定して事実上無効化
    else:
        file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ハンドラの追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# デフォルトのロガーインスタンスを作成
logger = setup_logger()
