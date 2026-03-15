"""Smoke tests for cook manager APIs."""

from pathlib import Path

from core.cook import CookManager, CookOptions, CookTarget, PackageOptions


def _create_fake_engine(engine_root: Path) -> None:
    (engine_root / "Engine" / "Build" / "BatchFiles").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Binaries").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Build").mkdir(parents=True, exist_ok=True)

    (engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat").write_text("", encoding="utf-8")
    (engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe").write_text("", encoding="utf-8")


def _create_project(project_file: Path) -> None:
    project_file.parent.mkdir(parents=True, exist_ok=True)
    project_file.write_text('{"FileVersion": 3, "EngineAssociation": "5.4"}', encoding="utf-8")


def test_cook_manager_init_with_valid_paths(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    project = tmp_path / "Demo" / "Demo.uproject"
    _create_fake_engine(engine)
    _create_project(project)

    manager = CookManager(engine_path=engine, project_path=project)
    assert manager.engine_path == engine.resolve()
    assert manager.project_path == project.resolve()
    assert manager.uat_path.name in {"RunUAT.bat", "RunUAT.cmd"}


def test_build_cook_command_contains_target_and_flags(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    project = tmp_path / "Demo" / "Demo.uproject"
    _create_fake_engine(engine)
    _create_project(project)

    manager = CookManager(engine_path=engine, project_path=project)
    options = CookOptions(target=CookTarget.WINDOWS, maps=["/Game/Maps/Main"], iterative=True)
    cmd = manager._build_cook_command(project.resolve(), options, tmp_path / "cook.log")

    assert "Cook" in cmd
    assert "-targetplatform" in cmd
    assert "Windows" in cmd
    assert "-iterative" in cmd


def test_build_package_command_contains_archive_directory(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    project = tmp_path / "Demo" / "Demo.uproject"
    _create_fake_engine(engine)
    _create_project(project)

    manager = CookManager(engine_path=engine, project_path=project)
    options = PackageOptions(archive=True, archive_directory=tmp_path / "Archive")
    cmd = manager._build_package_command(project.resolve(), options, tmp_path / "package.log")

    assert any(part.startswith("-archivedirectory") for part in cmd)
    assert "-archive" in cmd
