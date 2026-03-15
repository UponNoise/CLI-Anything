"""Smoke tests for packaging manager APIs."""

from pathlib import Path

from core.packaging import (
    CompressionLevel,
    DeploymentTarget,
    PackagingConfig,
    PackagingFormat,
    PackagingManager,
    PackagingPlatform,
    PlatformSpecificConfig,
)


def _create_fake_engine(engine_root: Path) -> None:
    (engine_root / "Engine" / "Build" / "BatchFiles").mkdir(parents=True, exist_ok=True)
    (engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat").write_text("", encoding="utf-8")


def test_packaging_config_roundtrip_dict_and_file(tmp_path: Path) -> None:
    project = tmp_path / "Game.uproject"
    project.write_text("{}", encoding="utf-8")

    config = PackagingConfig(
        project_path=project,
        platform=PackagingPlatform.ANDROID,
        format=PackagingFormat.APK,
        compression=CompressionLevel.NORMAL,
        deployment_targets=[DeploymentTarget.GOOGLE_PLAY],
        custom_settings={"package_name": "com.example.game"},
    )

    as_dict = config.to_dict()
    restored = PackagingConfig.from_dict(as_dict)

    assert restored.project_path == project
    assert restored.platform == PackagingPlatform.ANDROID
    assert restored.deployment_targets == [DeploymentTarget.GOOGLE_PLAY]

    output = tmp_path / "packaging.json"
    config.save(output)
    loaded = PackagingConfig.load(output)
    assert loaded.custom_settings["package_name"] == "com.example.game"


def test_platform_specific_defaults_and_validation() -> None:
    defaults = PlatformSpecificConfig.get_defaults(PackagingPlatform.ANDROID)
    assert "package_name" in defaults

    errors = PlatformSpecificConfig.validate_config(
        PackagingPlatform.ANDROID,
        {"package_name": "com.example.game", "version_code": 1, "version_name": "1.0.0"},
    )
    assert errors == []


def test_packaging_manager_builds_uat_command(tmp_path: Path) -> None:
    engine = tmp_path / "UE_5.4"
    project = tmp_path / "Game.uproject"
    output_dir = tmp_path / "Packaged"
    _create_fake_engine(engine)
    project.write_text("{}", encoding="utf-8")

    manager = PackagingManager(engine_path=engine, project_path=project)
    config = manager.create_packaging_config(
        platform=PackagingPlatform.WINDOWS,
        output_dir=output_dir,
    )

    cmd = manager._build_uat_command(config)
    assert cmd[0].endswith("RunUAT.bat")
    assert "BuildCookRun" in cmd
    assert any(part.startswith("-project=") for part in cmd)
