"""Smoke tests for session manager APIs."""

from pathlib import Path

from core.session import Session, SessionError


def _create_project_file(root: Path) -> Path:
    project_file = root / "MyGame.uproject"
    project_file.write_text('{"FileVersion":3,"EngineAssociation":"5.4.0"}', encoding="utf-8")
    return project_file


def test_session_set_project_and_map(tmp_path: Path) -> None:
    project_file = _create_project_file(tmp_path)
    session = Session(working_dir=tmp_path)

    session.set_project(project_file)
    session.set_current_map("/Game/Maps/Main")

    assert session.get_project() == project_file.resolve()
    assert session.get_current_map() == "/Game/Maps/Main"


def test_session_environment_and_history(tmp_path: Path) -> None:
    session = Session(working_dir=tmp_path)

    session.set_environment_variable("UE_TEST", "1")
    session.add_command_history("build", {"target": "Editor"}, "ok")

    assert session.get_environment_variable("UE_TEST") == "1"
    assert len(session.get_command_history()) == 1


def test_session_set_project_invalid_path_raises(tmp_path: Path) -> None:
    session = Session(working_dir=tmp_path)

    try:
        session.set_project(tmp_path / "missing.uproject")
        assert False, "Expected SessionError"
    except SessionError:
        assert True
