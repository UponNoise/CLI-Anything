"""Smoke tests for path manager APIs."""

from pathlib import Path

from utils.path_manager import PathManager, InvalidAssetPathError


def _create_project_tree(root: Path) -> Path:
    project_file = root / "MyGame.uproject"
    project_file.write_text('{"FileVersion":3,"EngineAssociation":"5.4.0"}', encoding="utf-8")
    (root / "Content" / "Maps").mkdir(parents=True, exist_ok=True)
    (root / "Config").mkdir(parents=True, exist_ok=True)
    (root / "Source").mkdir(parents=True, exist_ok=True)
    return project_file


def test_virtual_to_physical_and_back(tmp_path: Path) -> None:
    project_file = _create_project_tree(tmp_path)
    pm = PathManager(project_file)

    physical = pm.virtual_to_physical("/Game/Maps/Main", extension=".umap")
    assert physical.name == "Main.umap"

    roundtrip = pm.physical_to_virtual(physical)
    assert roundtrip.startswith("/Game/")


def test_virtual_path_validation(tmp_path: Path) -> None:
    project_file = _create_project_tree(tmp_path)
    pm = PathManager(project_file)

    assert pm.is_valid_asset_path("/Game/Blueprints/BP_Player")

    try:
        pm.virtual_to_physical("Game/Invalid")
        assert False, "Expected InvalidAssetPathError"
    except InvalidAssetPathError:
        assert True
