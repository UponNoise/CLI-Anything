"""Smoke tests for editor manager APIs."""

from pathlib import Path

from core.editor import EditorManager, EditorOptions, EditorMode


def _create_fake_engine(engine_root: Path) -> Path:
    exe = engine_root / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("", encoding="utf-8")

    uat = engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
    uat.parent.mkdir(parents=True, exist_ok=True)
    uat.write_text("", encoding="utf-8")
    return exe


def test_editor_manager_build_command_contains_core_flags(tmp_path: Path) -> None:
    engine = tmp_path / "UE5"
    _create_fake_engine(engine)

    project_file = tmp_path / "Game.uproject"
    project_file.write_text('{"Name":"Game","FileVersion":3}', encoding="utf-8")

    manager = EditorManager(engine_path=engine, project_path=project_file)
    options = EditorOptions(map="/Game/Maps/Main", mode=EditorMode.HEADLESS, unattended=True)
    cmd = manager._build_launch_command(options)

    joined = " ".join(cmd)
    assert "UnrealEditor" in joined
    assert "/Game/Maps/Main" in joined
    assert "-NullRHI" in joined
    assert "-unattended" in joined
