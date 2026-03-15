"""Compatibility smoke tests for optional config parser module."""

import importlib

import pytest

MODULE_NAME = "unreal_engine.utils.config_parser"


spec = importlib.util.find_spec(MODULE_NAME)
pytestmark = pytest.mark.skipif(spec is None, reason="Optional config parser module is not present in current implementation")


if spec is not None:
    config_parser = importlib.import_module(MODULE_NAME)


    def test_config_parser_exports_core_symbols() -> None:
        required = [
            "ConfigValue",
            "ConfigSection",
            "ConfigFileType",
            "ConfigSectionType",
            "IniConfigParser",
            "ConfigMerger",
            "ConfigValidator",
        ]
        for symbol in required:
            assert hasattr(config_parser, symbol)
