import logging

import pytest

from pyprolog.util.logger import switch_to_production_mode, switch_to_test_mode


def _force_info_level():
    """ベンチマーク時はINFO固定にする（root/prolog/handler）。"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in root_logger.handlers:
        handler.setLevel(logging.INFO)

    prolog_logger = logging.getLogger("prolog")
    prolog_logger.setLevel(logging.INFO)
    for handler in prolog_logger.handlers:
        handler.setLevel(logging.INFO)


@pytest.fixture(autouse=True)
def _apply_logging_policy(request):
    """info_logマーカー付きテストのみINFO固定にする。"""
    if request.node.get_closest_marker("info_log"):
        switch_to_production_mode()
        _force_info_level()
        yield
        switch_to_test_mode()
    else:
        yield
