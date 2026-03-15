"""Smoke tests for UE5 core modules aligned with current APIs."""

from pathlib import Path

from core.build import BuildOptions, BuildConfiguration, BuildTarget, BuildPlatform
from core.project import create_project, get_project_info, save_project, open_project


def test_project_create_save_open_roundtrip(tmp_path: Path) -> None:
    project = create_project(name="TestGame", engine_version="5.4.0")
    saved = save_project(project, tmp_path / "TestGame.uproject", backup=False)
    loaded = open_project(saved)

    assert loaded["Modules"][0]["Name"] == "TestGame"
    assert loaded["EngineAssociation"] == "5.4.0"


def test_project_info_contains_expected_fields() -> None:
    project = create_project(name="Demo")
    info = get_project_info(project)

    assert info["name"] == "Demo"
    assert "engine_association" in info
    assert "module_count" in info


def test_build_options_can_be_constructed() -> None:
    options = BuildOptions(
        configuration=BuildConfiguration.DEVELOPMENT,
        target=BuildTarget.EDITOR,
        platform=BuildPlatform.WIN64,
    )

    assert options.configuration == BuildConfiguration.DEVELOPMENT
    assert options.target == BuildTarget.EDITOR
    assert options.platform == BuildPlatform.WIN64
