"""Unreal Engine CLI - Build system module.

Handles UBT (Unreal Build Tool) and UAT (Unreal Automation Tool) commands.
Provides a Pythonic interface for building, cooking, and packaging UE5 projects.
"""

import os
import subprocess
import platform
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class BuildConfiguration(Enum):
    """UE5 build configurations."""
    DEBUG = "Debug"
    DEBUG_GAME = "DebugGame"
    DEVELOPMENT = "Development"
    TEST = "Test"
    SHIPPING = "Shipping"


class BuildTarget(Enum):
    """UE5 build targets."""
    GAME = "Game"
    EDITOR = "Editor"
    CLIENT = "Client"
    SERVER = "Server"
    PROGRAM = "Program"


class BuildPlatform(Enum):
    """UE5 target platforms."""
    WIN64 = "Win64"
    WIN32 = "Win32"
    MAC = "Mac"
    LINUX = "Linux"
    LINUX_ARM64 = "LinuxArm64"
    ANDROID = "Android"
    IOS = "IOS"
    TVOS = "TVOS"
    PS5 = "PS5"
    XBOX_SERIES_X = "XboxSeriesX"


class BuildAction(Enum):
    """UE5 build actions."""
    BUILD = auto()
    REBUILD = auto()
    CLEAN = auto()
    COOK = auto()
    PACKAGE = auto()
    STAGE = auto()
    ARCHIVE = auto()


@dataclass
class BuildOptions:
    """Options for UE5 build operations.

    Attributes:
        configuration: Build configuration (Debug, Development, Shipping, etc.).
        target: Build target (Game, Editor, Client, Server).
        platform: Target platform (Win64, Mac, Linux, etc.).
        verbose: Enable verbose output.
        silent: Suppress non-error output.
        parallel: Number of parallel actions (0 for auto).
        unity: Enable Unity build mode.
        precompile: Generate precompiled headers.
        hot_reload: Enable hot reload support.
        nop4: Disable Perforce integration.
        force_unity: Force Unity build even if disabled.
        single_file: Compile single file only.
        module: Specific module to build.
    """
    configuration: BuildConfiguration = BuildConfiguration.DEVELOPMENT
    target: BuildTarget = BuildTarget.EDITOR
    platform: BuildPlatform = BuildPlatform.WIN64
    verbose: bool = False
    silent: bool = False
    parallel: int = 0
    unity: bool = True
    precompile: bool = False
    hot_reload: bool = True
    nop4: bool = True
    force_unity: bool = False
    single_file: Optional[str] = None
    module: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)


@dataclass
class CookOptions:
    """Options for UE5 cook operations.

    Attributes:
        maps: List of maps to cook (empty for all).
        cultures: List of cultures to cook.
        compressed: Enable package compression.
        iterative: Use iterative cooking.
        skip_editor_content: Skip editor-specific content.
        unversioned_cooked_content: Cook content without version checks.
        cook_all: Cook all content.
        cook_maps_only: Cook only maps.
    """
    maps: List[str] = field(default_factory=list)
    cultures: List[str] = field(default_factory=list)
    compressed: bool = True
    iterative: bool = False
    skip_editor_content: bool = False
    unversioned_cooked_content: bool = False
    cook_all: bool = False
    cook_maps_only: bool = False
    extra_args: List[str] = field(default_factory=list)


@dataclass
class PackageOptions:
    """Options for UE5 package operations.

    Attributes:
        staging_directory: Directory for staged files.
        archive_directory: Directory for archived package.
        build: Build the project before packaging.
        cook: Cook content before packaging.
        stage: Stage files after cooking.
        archive: Archive the staged files.
        pak: Create pak files.
        prereqs: Include prerequisites installer.
        distribution: Create distribution build.
        compressed: Compress pak files.
    """
    staging_directory: Optional[str] = None
    archive_directory: Optional[str] = None
    build: bool = True
    cook: bool = True
    stage: bool = True
    archive: bool = False
    pak: bool = True
    prereqs: bool = True
    distribution: bool = False
    compressed: bool = True
    extra_args: List[str] = field(default_factory=list)


class BuildError(Exception):
    """Base exception for build operations."""
    pass


class BuildSystemNotFoundError(BuildError):
    """Raised when UBT or UAT cannot be found."""
    pass


class BuildFailedError(BuildError):
    """Raised when a build operation fails."""
    pass


class BuildSystem:
    """Interface to UE5 build system (UBT/UAT).

    This class provides methods to invoke UBT and UAT commands with
    proper argument construction and error handling.

    Example:
        >>> from core.build import BuildSystem, BuildOptions
        >>> from utils.ue_backend import UEEngineLocator
        >>> 
        >>> locator = UEEngineLocator()
        >>> engine_path = locator.find_engine("5.4")
        >>> 
        >>> bs = BuildSystem(engine_path)
        >>> options = BuildOptions(
        ...     configuration=BuildConfiguration.DEVELOPMENT,
        ...     target=BuildTarget.EDITOR,
        ... )
        >>> result = bs.build_project("/path/to/MyProject.uproject", options)
    """

    def __init__(self, engine_path: Union[str, Path]):
        """Initialize the build system.

        Args:
            engine_path: Path to UE5 engine installation.

        Raises:
            BuildSystemNotFoundError: If UBT/UAT executables are not found.
        """
        self.engine_path = Path(engine_path).resolve()
        self._validate_engine_path()
        self._ubt_path = self._get_ubt_path()
        self._uat_path = self._get_uat_path()

    def _validate_engine_path(self) -> None:
        """Validate that the engine path contains required directories."""
        if not self.engine_path.exists():
            raise BuildSystemNotFoundError(
                f"Engine path does not exist: {self.engine_path}"
            )

        required_dirs = ["Engine", "Engine\\Build", "Engine\\Binaries"]
        for dir_name in required_dirs:
            if not (self.engine_path / dir_name).exists():
                raise BuildSystemNotFoundError(
                    f"Invalid engine path, missing: {dir_name}"
                )

    def _get_ubt_path(self) -> Path:
        """Get the path to UnrealBuildTool executable."""
        system = platform.system()
        
        if system == "Windows":
            ubt_paths = [
                self.engine_path / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe",
                self.engine_path / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe",
            ]
        elif system == "Darwin":  # macOS
            ubt_paths = [
                self.engine_path / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool",
                self.engine_path / "Engine" / "Binaries" / "Mac" / "UnrealBuildTool.app" / "Contents" / "MacOS" / "UnrealBuildTool",
            ]
        else:  # Linux
            ubt_paths = [
                self.engine_path / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool",
                self.engine_path / "Engine" / "Binaries" / "Linux" / "UnrealBuildTool",
            ]

        for path in ubt_paths:
            if path.exists():
                return path

        raise BuildSystemNotFoundError(
            f"UnrealBuildTool not found in: {self.engine_path}"
        )

    def _get_uat_path(self) -> Path:
        """Get the path to AutomationTool executable."""
        system = platform.system()
        
        # UAT is typically a script/batch file
        if system == "Windows":
            uat_paths = [
                self.engine_path / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat",
                self.engine_path / "Engine" / "Build" / "BatchFiles" / "Build.bat",
            ]
        else:
            uat_paths = [
                self.engine_path / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh",
                self.engine_path / "Engine" / "Build" / "BatchFiles" / "Build.sh",
            ]

        for path in uat_paths:
            if path.exists():
                return path

        raise BuildSystemNotFoundError(
            f"AutomationTool not found in: {self.engine_path}"
        )

    def _build_ubt_args(
        self,
        project_path: Union[str, Path],
        options: BuildOptions,
    ) -> List[str]:
        """Build command line arguments for UBT.

        Args:
            project_path: Path to the .uproject file.
            options: Build options.

        Returns:
            List of command line arguments.
        """
        args: List[str] = []

        # Target specification
        project_name = Path(project_path).stem
        target_name = f"{project_name}{options.target.value}"
        args.extend([target_name, options.platform.value, options.configuration.value])

        # Project file
        args.extend(["-Project", str(project_path)])

        # Optional flags
        if options.verbose:
            args.append("-Verbose")
        if options.silent:
            args.append("-Silent")
        if options.parallel > 0:
            args.extend(["-ParallelExecutor", f"-MaxParallelActions={options.parallel}"])
        if not options.unity:
            args.append("-NoUnity")
        if options.force_unity:
            args.append("-ForceUnity")
        if options.precompile:
            args.append("-Precompile")
        if options.hot_reload:
            args.append("-HotReload")
        if options.nop4:
            args.append("-NoP4")
        if options.single_file:
            args.extend(["-SingleFile", options.single_file])
        if options.module:
            args.extend(["-Module", options.module])

        # Extra arguments
        args.extend(options.extra_args)

        return args

    def build_project(
        self,
        project_path: Union[str, Path],
        options: Optional[BuildOptions] = None,
        rebuild: bool = False,
    ) -> Dict[str, Any]:
        """Build a UE5 project using UBT.

        Args:
            project_path: Path to the .uproject file.
            options: Build options. Uses defaults if not provided.
            rebuild: Whether to rebuild instead of incremental build.

        Returns:
            Dictionary containing build results.

        Raises:
            BuildFailedError: If the build fails.
        """
        options = options or BuildOptions()
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise BuildFailedError(f"Project not found: {project_path}")

        # Build command
        cmd = [str(self._ubt_path)]
        if rebuild:
            cmd.append("-Rebuild")
        cmd.extend(self._build_ubt_args(project_path, options))

        return self._run_command(cmd, "Build")

    def clean_project(
        self,
        project_path: Union[str, Path],
        options: Optional[BuildOptions] = None,
    ) -> Dict[str, Any]:
        """Clean build artifacts for a project.

        Args:
            project_path: Path to the .uproject file.
            options: Build options.

        Returns:
            Dictionary containing clean results.
        """
        options = options or BuildOptions()
        project_path = Path(project_path).resolve()

        cmd = [str(self._ubt_path), "-Clean"]
        cmd.extend(self._build_ubt_args(project_path, options))

        return self._run_command(cmd, "Clean")

    def cook_project(
        self,
        project_path: Union[str, Path],
        options: Optional[CookOptions] = None,
    ) -> Dict[str, Any]:
        """Cook content for a project using UAT.

        Args:
            project_path: Path to the .uproject file.
            options: Cook options.

        Returns:
            Dictionary containing cook results.
        """
        options = options or CookOptions()
        project_path = Path(project_path).resolve()

        cmd = [
            str(self._uat_path),
            "BuildCookRun",
            f"-project={project_path}",
            "-noP4",
            "-cook",
        ]

        # Add cook options
        if options.maps:
            cmd.append(f"-maps={','.join(options.maps)}")
        if options.cultures:
            cmd.append(f"-cultures={','.join(options.cultures)}")
        if options.compressed:
            cmd.append("-compressed")
        if options.iterative:
            cmd.append("-iterativecooking")
        if options.skip_editor_content:
            cmd.append("-SkipCookingEditorContent")
        if options.unversioned_cooked_content:
            cmd.append("-unversionedcookedcontent")
        if options.cook_all:
            cmd.append("-CookAll")
        if options.cook_maps_only:
            cmd.append("-CookMapsOnly")

        cmd.extend(options.extra_args)

        return self._run_command(cmd, "Cook")

    def package_project(
        self,
        project_path: Union[str, Path],
        options: Optional[PackageOptions] = None,
    ) -> Dict[str, Any]:
        """Package a project for distribution using UAT.

        Args:
            project_path: Path to the .uproject file.
            options: Package options.

        Returns:
            Dictionary containing package results.
        """
        options = options or PackageOptions()
        project_path = Path(project_path).resolve()

        cmd = [
            str(self._uat_path),
            "BuildCookRun",
            f"-project={project_path}",
            "-noP4",
        ]

        # Build steps
        if options.build:
            cmd.append("-build")
        if options.cook:
            cmd.append("-cook")
        if options.stage:
            cmd.append("-stage")
        if options.archive:
            cmd.append("-archive")

        # Directories
        if options.staging_directory:
            cmd.append(f"-stagingdirectory={options.staging_directory}")
        if options.archive_directory:
            cmd.append(f"-archivedirectory={options.archive_directory}")

        # Package options
        if options.pak:
            cmd.append("-pak")
        if options.prereqs:
            cmd.append("-prereqs")
        if options.distribution:
            cmd.append("-distribution")
        if options.compressed:
            cmd.append("-compressed")

        cmd.extend(options.extra_args)

        return self._run_command(cmd, "Package")

    def generate_project_files(
        self,
        project_path: Union[str, Path],
        ide: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate IDE project files.

        Args:
            project_path: Path to the .uproject file.
            ide: Target IDE (VisualStudio2022, VisualStudio2019, etc.).

        Returns:
            Dictionary containing generation results.
        """
        project_path = Path(project_path).resolve()

        cmd = [
            str(self._ubt_path),
            "-ProjectFiles",
            f"-Project={project_path}",
            "-Game",
            "-Engine",
        ]

        if ide:
            cmd.append(f"-{ide}")

        return self._run_command(cmd, "GenerateProjectFiles")

    def _run_command(
        self,
        cmd: List[str],
        operation: str,
    ) -> Dict[str, Any]:
        """Execute a build command and capture results.

        Args:
            cmd: Command and arguments to execute.
            operation: Name of the operation for logging.

        Returns:
            Dictionary with success status, return code, and output.
        """
        result = {
            "operation": operation,
            "command": " ".join(cmd),
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": "",
        }

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["success"] = process.returncode == 0
        except Exception as e:
            result["stderr"] = str(e)
            raise BuildFailedError(f"{operation} failed: {e}")

        if not result["success"]:
            raise BuildFailedError(
                f"{operation} failed with code {result['return_code']}: "
                f"{result['stderr']}"
            )

        return result

    @property
    def ubt_path(self) -> Path:
        """Path to UnrealBuildTool executable."""
        return self._ubt_path

    @property
    def uat_path(self) -> Path:
        """Path to AutomationTool script."""
        return self._uat_path
