"""Smoke tests for build system APIs."""

from pathlib import Path

from core.build import (
    BuildConfiguration,
    BuildOptions,
    BuildPlatform,
    BuildSystem,
    BuildTarget,
)


def _create_fake_engine(engine_root: Path) -> None:
    (engine_root / "Engine" / "Build" / "BatchFiles").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool").mkdir(
        parents=True, exist_ok=True
    )
    (engine_root / "Engine" / "Binaries" / "Win64").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Build").mkdir(parents=True, exist_ok=True)

    (engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe").write_text("", encoding="utf-8")
    (engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat").write_text("", encoding="utf-8")


def test_build_options_defaults_match_current_dataclass() -> None:
    options = BuildOptions()
    assert options.configuration == BuildConfiguration.DEVELOPMENT
    assert options.target == BuildTarget.EDITOR
    assert options.platform == BuildPlatform.WIN64
    assert options.unity is True
    assert options.hot_reload is True


def test_build_system_initializes_with_fake_engine(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    _create_fake_engine(engine)

    build_system = BuildSystem(engine)

    assert build_system.ubt_path.name == "UnrealBuildTool.exe"
    assert build_system.uat_path.name == "RunUAT.bat"


def test_build_ubt_args_contains_expected_flags(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    _create_fake_engine(engine)
    project = tmp_path / "Demo.uproject"
    project.write_text("{}", encoding="utf-8")

    build_system = BuildSystem(engine)
    options = BuildOptions(
        configuration=BuildConfiguration.SHIPPING,
        target=BuildTarget.GAME,
        platform=BuildPlatform.WIN64,
        verbose=True,
        unity=False,
        module="DemoModule",
    )

    args = build_system._build_ubt_args(project, options)
    assert "DemoGame" in args
    assert "Win64" in args
    assert "Shipping" in args
    assert "-Verbose" in args
    assert "-NoUnity" in args
    assert "-Module" in args
