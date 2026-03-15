"""Smoke tests for project management APIs."""

from pathlib import Path

import pytest

from core.project import (
    ProjectNotFoundError,
    UEProjectError,
    add_module,
    add_plugin,
    create_project,
    get_project_info,
    open_project,
    remove_module,
    remove_plugin,
    save_project,
    set_settings,
)


def test_create_project_and_info() -> None:
    project = create_project(name="DemoGame", description="Demo", target_platforms=["Win64", "Linux"])

    assert project["FileVersion"] == 3
    assert project["Modules"][0]["Name"] == "DemoGame"
    assert "TargetPlatforms" in project

    info = get_project_info(project)
    assert info["name"] == "DemoGame"
    assert "Win64" in info["target_platforms"]


def test_save_and_open_project_roundtrip(tmp_path: Path) -> None:
    project = create_project(name="SaveGame")
    project_file = tmp_path / "SaveGame.uproject"

    saved_path = save_project(project, project_file)
    loaded = open_project(saved_path)

    assert loaded["FileVersion"] == 3
    assert loaded["EngineAssociation"] == "5.4.0"


def test_save_project_creates_backup(tmp_path: Path) -> None:
    project = create_project(name="BackupGame")
    project_file = tmp_path / "BackupGame.uproject"

    save_project(project, project_file)
    updated = set_settings(project, description="updated")
    save_project(updated, project_file, backup=True)

    assert project_file.with_suffix(".uproject.backup").exists()


def test_module_and_plugin_lifecycle() -> None:
    project = create_project(name="FeatureGame")

    add_module(project, name="Inventory", module_type="Runtime")
    add_plugin(project, name="MyPlugin", enabled=True)

    assert any(m["Name"] == "Inventory" for m in project["Modules"])
    assert any(p["Name"] == "MyPlugin" for p in project["Plugins"])

    remove_module(project, "Inventory")
    remove_plugin(project, "MyPlugin")

    assert all(m["Name"] != "Inventory" for m in project["Modules"])
    assert all(p["Name"] != "MyPlugin" for p in project["Plugins"])


def test_open_project_missing_file_raises() -> None:
    with pytest.raises(ProjectNotFoundError):
        open_project("/does/not/exist/Nope.uproject")


def test_save_project_invalid_dir_raises(tmp_path: Path) -> None:
    bad_path = tmp_path / "missing_parent" / "Demo.uproject"
    # Save should create missing parent directories, so this verifies no UEProjectError is raised.
    try:
        save_project(create_project("Okay"), bad_path)
    except UEProjectError as exc:  # pragma: no cover
        pytest.fail(f"save_project unexpectedly failed: {exc}")
