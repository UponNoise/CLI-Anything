"""Smoke tests for plugin manager APIs."""

import json
from pathlib import Path

from core.plugin import PluginManager


def _write_plugin_descriptor(plugin_dir: Path, name: str, enabled_by_default: bool = False) -> None:
    plugin_dir.mkdir(parents=True, exist_ok=True)
    descriptor = {
        "FileVersion": 3,
        "Version": 1,
        "VersionName": "1.0.0",
        "FriendlyName": name,
        "Description": "Test plugin",
        "Category": "Other",
        "EnabledByDefault": enabled_by_default,
        "Modules": [{"Name": name, "Type": "Runtime"}],
    }
    (plugin_dir / f"{name}.uplugin").write_text(json.dumps(descriptor), encoding="utf-8")


def test_list_plugins_discovers_project_plugins(tmp_path: Path) -> None:
    project_root = tmp_path / "DemoProject"
    plugin_dir = project_root / "Plugins" / "TestPlugin"
    _write_plugin_descriptor(plugin_dir, "TestPlugin")

    manager = PluginManager(project_path=project_root)
    plugins = manager.list_plugins(include_engine=False)

    assert len(plugins) == 1
    assert plugins[0].name == "TestPlugin"
    assert plugins[0].is_project_plugin is True


def test_enable_plugin_updates_project_config(tmp_path: Path) -> None:
    project_root = tmp_path / "DemoProject"
    plugin_dir = project_root / "Plugins" / "GameplayTools"
    _write_plugin_descriptor(plugin_dir, "GameplayTools", enabled_by_default=False)

    manager = PluginManager(project_path=project_root)
    assert manager.enable_plugin("GameplayTools", enable=True) is True

    config_file = project_root / "Config" / "DefaultGame.ini"
    content = config_file.read_text(encoding="utf-8")
    assert "+Plugins=GameplayTools" in content


def test_disable_plugin_updates_project_config(tmp_path: Path) -> None:
    project_root = tmp_path / "DemoProject"
    plugin_dir = project_root / "Plugins" / "GameplayTools"
    _write_plugin_descriptor(plugin_dir, "GameplayTools", enabled_by_default=True)

    manager = PluginManager(project_path=project_root)
    assert manager.enable_plugin("GameplayTools", enable=False) is True

    config_file = project_root / "Config" / "DefaultGame.ini"
    content = config_file.read_text(encoding="utf-8")
    assert "-Plugins=GameplayTools" in content
