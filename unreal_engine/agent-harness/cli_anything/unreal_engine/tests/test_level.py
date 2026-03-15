"""Smoke tests for level manager APIs."""

from pathlib import Path

from core.level import LevelManager, LevelOptions


def test_level_create_and_list(tmp_path: Path) -> None:
    (tmp_path / "Content").mkdir(parents=True, exist_ok=True)
    manager = LevelManager(project_path=tmp_path)

    created = manager.create_level("MainMap", subfolder="Maps", options=LevelOptions())
    levels = manager.list_levels(subfolder="Maps")

    assert created.exists()
    assert created.suffix == ".umap"
    assert any(level.name == "MainMap" for level in levels)


def test_level_rename_and_duplicate(tmp_path: Path) -> None:
    (tmp_path / "Content").mkdir(parents=True, exist_ok=True)
    manager = LevelManager(project_path=tmp_path)

    manager.create_level("Original", subfolder="Maps")
    renamed = manager.rename_level("/Game/Maps/Original", "Renamed")
    duplicated = manager.duplicate_level("/Game/Maps/Renamed", "Copy")

    assert renamed.name == "Renamed.umap"
    assert duplicated.name == "Copy.umap"
