"""Unreal Engine CLI - Cooking and packaging module.

Handles content cooking, staging, and packaging for UE5 projects.
Uses UAT (Unreal Automation Tool) for cooking and packaging operations.
"""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .build import BuildSystem, BuildPlatform, BuildConfiguration


class CookTarget(Enum):
    """UE5 cooking targets."""
    WINDOWS = "Windows"
    WINDOWS_SERVER = "WindowsServer"
    MAC = "Mac"
    LINUX = "Linux"
    LINUX_SERVER = "LinuxServer"
    ANDROID = "Android"
    IOS = "IOS"
    TVOS = "TVOS"
    PS5 = "PS5"
    XBOX_SERIES_X = "XboxSeriesX"
    XBOX_SERIES_X_SERVER = "XboxSeriesXServer"


class CookFlavor(Enum):
    """UE5 cooking flavors."""
    DEVELOPMENT = "Development"
    TEST = "Test"
    SHIPPING = "Shipping"


class CookAction(Enum):
    """UE5 cooking actions."""
    COOK = auto()
    COOK_AND_STAGE = auto()
    PACKAGE = auto()


@dataclass
class CookOptions:
    """Options for UE5 cooking operations.

    Attributes:
        target: Target platform for cooking.
        flavor: Build flavor for cooking.
        maps: Specific maps to cook (empty for all).
        cultures: Cultures to cook (empty for all).
        compressed: Enable package compression.
        iterative: Use iterative cooking.
        skip_editor_content: Skip editor-specific content.
        unversioned_cooked_content: Cook content without version checks.
        cook_all: Cook all content.
        cook_maps_only: Cook only maps.
        staging_directory: Directory for staged files.
        archive: Create archive after cooking.
        pak: Create pak files.
        distribution: Create distribution build.
        extra_args: Additional UAT arguments.
    """
    target: CookTarget = CookTarget.WINDOWS
    flavor: CookFlavor = CookFlavor.DEVELOPMENT
    maps: List[str] = field(default_factory=list)
    cultures: List[str] = field(default_factory=list)
    compressed: bool = True
    iterative: bool = False
    skip_editor_content: bool = False
    unversioned_cooked_content: bool = False
    cook_all: bool = False
    cook_maps_only: bool = False
    staging_directory: Optional[Path] = None
    archive: bool = False
    pak: bool = True
    distribution: bool = False
    extra_args: List[str] = field(default_factory=list)


@dataclass
class PackageOptions:
    """Options for UE5 packaging operations.

    Attributes:
        target: Target platform for packaging.
        flavor: Build flavor for packaging.
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
        extra_args: Additional UAT arguments.
    """
    target: CookTarget = CookTarget.WINDOWS
    flavor: CookFlavor = CookFlavor.DEVELOPMENT
    staging_directory: Optional[Path] = None
    archive_directory: Optional[Path] = None
    build: bool = True
    cook: bool = True
    stage: bool = True
    archive: bool = False
    pak: bool = True
    prereqs: bool = True
    distribution: bool = False
    compressed: bool = True
    extra_args: List[str] = field(default_factory=list)


@dataclass
class CookResult:
    """Result of a cooking operation.

    Attributes:
        success: Whether the operation succeeded.
        cooked_content_dir: Directory containing cooked content.
        staged_content_dir: Directory containing staged content.
        packaged_content_dir: Directory containing packaged content.
        log_file: Path to the operation log file.
        duration_seconds: Duration of the operation in seconds.
        errors: List of error messages.
        warnings: List of warning messages.
    """
    success: bool
    cooked_content_dir: Optional[Path] = None
    staged_content_dir: Optional[Path] = None
    packaged_content_dir: Optional[Path] = None
    log_file: Optional[Path] = None
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CookError(Exception):
    """Base exception for cooking operations."""
    pass


class CookSystemNotFoundError(CookError):
    """Raised when UAT cannot be found."""
    pass


class CookFailedError(CookError):
    """Raised when a cooking operation fails."""
    pass


class PackageFailedError(CookError):
    """Raised when a packaging operation fails."""
    pass


class CookManager:
    """UE5 cooking and packaging manager.

    Provides methods for cooking content, staging, and packaging UE5 projects.

    Attributes:
        engine_path: Path to UE5 engine installation.
        project_path: Path to UE5 project.
        build_system: Build system instance.
    """

    def __init__(
        self,
        engine_path: Union[str, Path],
        project_path: Optional[Union[str, Path]] = None
    ) -> None:
        """Initialize cooking manager.

        Args:
            engine_path: Path to UE5 engine installation.
            project_path: Path to UE5 project.

        Raises:
            CookSystemNotFoundError: If UAT cannot be found.
        """
        self.engine_path = Path(engine_path).resolve()
        self.project_path = Path(project_path).resolve() if project_path else None
        
        # Validate engine path
        self._validate_engine_path()
        
        # Initialize build system
        self.build_system = BuildSystem(self.engine_path)
        
        # Get UAT path
        self.uat_path = self._get_uat_path()

    def _validate_engine_path(self) -> None:
        """Validate that the engine path contains required directories.

        Raises:
            CookSystemNotFoundError: If engine path is invalid.
        """
        required_dirs = [
            "Engine",
            "Engine/Binaries",
            "Engine/Build",
        ]
        
        for dir_name in required_dirs:
            dir_path = self.engine_path / dir_name
            if not dir_path.exists():
                raise CookSystemNotFoundError(
                    f"Invalid engine path: {dir_name} not found in {self.engine_path}"
                )

    def _get_uat_path(self) -> Path:
        """Get UAT (Unreal Automation Tool) executable path.

        Returns:
            Path to UAT executable.

        Raises:
            CookSystemNotFoundError: If UAT cannot be found.
        """
        # Try different UAT executable names based on platform
        if os.name == 'nt':  # Windows
            uat_names = ["RunUAT.bat", "RunUAT.cmd"]
        else:  # Unix-like
            uat_names = ["RunUAT.sh"]

        for uat_name in uat_names:
            uat_path = self.engine_path / "Engine" / "Build" / "BatchFiles" / uat_name
            if uat_path.exists():
                return uat_path

        raise CookSystemNotFoundError(
            f"UAT executable not found in {self.engine_path}/Engine/Build/BatchFiles/"
        )

    def cook_content(
        self,
        options: Optional[CookOptions] = None,
        project_path: Optional[Union[str, Path]] = None
    ) -> CookResult:
        """Cook project content.

        Args:
            options: Cooking options.
            project_path: Optional project path (overrides instance project_path).

        Returns:
            CookResult containing operation results.

        Raises:
            CookFailedError: If cooking fails.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            raise CookFailedError("No project path specified")

        options = options or CookOptions()

        # Validate project
        if not current_project.exists():
            raise CookFailedError(f"Project not found: {current_project}")
        if current_project.suffix != '.uproject':
            raise CookFailedError(f"Not a valid .uproject file: {current_project}")

        # Create log directory
        log_dir = current_project.parent / "Saved" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"Cook_{options.target.value}_{options.flavor.value}.log"

        # Build UAT command
        cmd = self._build_cook_command(current_project, options, log_file)

        # Execute cooking
        start_time = os.times().elapsed
        success, errors, warnings = self._execute_uat_command(cmd, log_file)
        duration = os.times().elapsed - start_time

        # Determine cooked content directory
        cooked_content_dir = self._get_cooked_content_dir(current_project, options)

        return CookResult(
            success=success,
            cooked_content_dir=cooked_content_dir if success else None,
            log_file=log_file,
            duration_seconds=duration,
            errors=errors,
            warnings=warnings
        )

    def _build_cook_command(
        self,
        project_path: Path,
        options: CookOptions,
        log_file: Path
    ) -> List[str]:
        """Build UAT command for cooking.

        Args:
            project_path: Path to .uproject file.
            options: Cooking options.
            log_file: Path to log file.

        Returns:
            List of command arguments.
        """
        cmd = [str(self.uat_path), "Cook"]

        # Project file
        cmd.extend(["-project", str(project_path)])

        # Target platform
        cmd.extend(["-targetplatform", options.target.value])

        # Build configuration
        cmd.extend(["-build", options.flavor.value])

        # Maps
        if options.maps:
            for map_name in options.maps:
                cmd.extend(["-map", map_name])
        elif options.cook_maps_only:
            cmd.extend(["-MapOnly"])
        elif options.cook_all:
            cmd.extend(["-CookAll"])

        # Cultures
        if options.cultures:
            for culture in options.cultures:
                cmd.extend(["-culture", culture])

        # Options
        if options.compressed:
            cmd.append("-compressed")
        if options.iterative:
            cmd.append("-iterative")
        if options.skip_editor_content:
            cmd.append("-SkipEditorContent")
        if options.unversioned_cooked_content:
            cmd.append("-Unversioned")

        # Staging directory
        if options.staging_directory:
            cmd.extend(["-stagingdirectory", str(options.staging_directory)])
            if options.archive:
                cmd.append("-archive")
            if options.pak:
                cmd.append("-pak")
            if options.distribution:
                cmd.append("-distribution")

        # Extra arguments
        cmd.extend(options.extra_args)

        # Log file
        cmd.extend(["-stdout", "-FullStdoutLogOutput", f"-LogCmds=\"LogSaveToFile {log_file}\""])

        return cmd

    def _get_cooked_content_dir(
        self,
        project_path: Path,
        options: CookOptions
    ) -> Path:
        """Get cooked content directory.

        Args:
            project_path: Path to .uproject file.
            options: Cooking options.

        Returns:
            Path to cooked content directory.
        """
        project_name = project_path.stem
        platform_map = {
            CookTarget.WINDOWS: "Windows",
            CookTarget.WINDOWS_SERVER: "WindowsServer",
            CookTarget.MAC: "Mac",
            CookTarget.LINUX: "Linux",
            CookTarget.LINUX_SERVER: "LinuxServer",
            CookTarget.ANDROID: "Android",
            CookTarget.IOS: "IOS",
            CookTarget.TVOS: "TVOS",
            CookTarget.PS5: "PS5",
            CookTarget.XBOX_SERIES_X: "XboxSeriesX",
            CookTarget.XBOX_SERIES_X_SERVER: "XboxSeriesXServer",
        }
        
        platform = platform_map.get(options.target, options.target.value)
        
        return (
            project_path.parent / "Saved" / "Cooked" / 
            platform / project_name / options.flavor.value
        )

    def cook_and_stage(
        self,
        options: Optional[CookOptions] = None,
        project_path: Optional[Union[str, Path]] = None
    ) -> CookResult:
        """Cook content and stage for packaging.

        Args:
            options: Cooking options.
            project_path: Optional project path (overrides instance project_path).

        Returns:
            CookResult containing operation results.

        Raises:
            CookFailedError: If cooking and staging fails.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            raise CookFailedError("No project path specified")

        options = options or CookOptions()
        
        # Ensure staging is enabled
        if not options.staging_directory:
            options.staging_directory = (
                current_project.parent / "Saved" / "StagedBuilds" / options.target.value
            )

        # Create log directory
        log_dir = current_project.parent / "Saved" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"CookAndStage_{options.target.value}_{options.flavor.value}.log"

        # Build UAT command for cook and stage
        cmd = self._build_cook_and_stage_command(current_project, options, log_file)

        # Execute command
        start_time = os.times().elapsed
        success, errors, warnings = self._execute_uat_command(cmd, log_file)
        duration = os.times().elapsed - start_time

        # Get directories
        cooked_content_dir = self._get_cooked_content_dir(current_project, options)
        staged_content_dir = options.staging_directory

        return CookResult(
            success=success,
            cooked_content_dir=cooked_content_dir if success else None,
            staged_content_dir=staged_content_dir if success else None,
            log_file=log_file,
            duration_seconds=duration,
            errors=errors,
            warnings=warnings
        )

    def _build_cook_and_stage_command(
        self,
        project_path: Path,
        options: CookOptions,
        log_file: Path
    ) -> List[str]:
        """Build UAT command for cook and stage.

        Args:
            project_path: Path to .uproject file.
            options: Cooking options.
            log_file: Path to log file.

        Returns:
            List of command arguments.
        """
        cmd = [str(self.uat_path), "Cook", "-stage"]

        # Project file
        cmd.extend(["-project", str(project_path)])

        # Target platform
        cmd.extend(["-targetplatform", options.target.value])

        # Build configuration
        cmd.extend(["-build", options.flavor.value])

        # Maps
        if options.maps:
            for map_name in options.maps:
                cmd.extend(["-map", map_name])
        elif options.cook_maps_only:
            cmd.extend(["-MapOnly"])
        elif options.cook_all:
            cmd.extend(["-CookAll"])

        # Cultures
        if options.cultures:
            for culture in options.cultures:
                cmd.extend(["-culture", culture])

        # Options
        if options.compressed:
            cmd.append("-compressed")
        if options.iterative:
            cmd.append("-iterative")
        if options.skip_editor_content:
            cmd.append("-SkipEditorContent")
        if options.unversioned_cooked_content:
            cmd.append("-Unversioned")

        # Staging directory
        if options.staging_directory:
            cmd.extend(["-stagingdirectory", str(options.staging_directory)])

        # Package options
        if options.pak:
            cmd.append("-pak")
        if options.distribution:
            cmd.append("-distribution")

        # Extra arguments
        cmd.extend(options.extra_args)

        # Log file
        cmd.extend(["-stdout", "-FullStdoutLogOutput", f"-LogCmds=\"LogSaveToFile {log_file}\""])

        return cmd

    def package_project(
        self,
        options: Optional[PackageOptions] = None,
        project_path: Optional[Union[str, Path]] = None
    ) -> CookResult:
        """Package project for distribution.

        Args:
            options: Packaging options.
            project_path: Optional project path (overrides instance project_path).

        Returns:
            CookResult containing operation results.

        Raises:
            PackageFailedError: If packaging fails.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            raise PackageFailedError("No project path specified")

        options = options or PackageOptions()

        # Validate project
        if not current_project.exists():
            raise PackageFailedError(f"Project not found: {current_project}")
        if current_project.suffix != '.uproject':
            raise PackageFailedError(f"Not a valid .uproject file: {current_project}")

        # Create log directory
        log_dir = current_project.parent / "Saved" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"Package_{options.target.value}_{options.flavor.value}.log"

        # Build UAT command
        cmd = self._build_package_command(current_project, options, log_file)

        # Execute packaging
        start_time = os.times().elapsed
        success, errors, warnings = self._execute_uat_command(cmd, log_file)
        duration = os.times().elapsed - start_time

        # Get packaged content directory
        packaged_content_dir = self._get_packaged_content_dir(current_project, options)

        return CookResult(
            success=success,
            packaged_content_dir=packaged_content_dir if success else None,
            log_file=log_file,
            duration_seconds=duration,
            errors=errors,
            warnings=warnings
        )

    def _build_package_command(
        self,
        project_path: Path,
        options: PackageOptions,
        log_file: Path
    ) -> List[str]:
        """Build UAT command for packaging.

        Args:
            project_path: Path to .uproject file.
            options: Packaging options.
            log_file: Path to log file.

        Returns:
            List of command arguments.
        """
        cmd = [str(self.uat_path)]

        # Determine packaging command
        if options.cook and options.stage:
            cmd.append("BuildCookRun")
        elif options.cook:
            cmd.append("Cook")
        else:
            cmd.append("Package")

        # Project file
        cmd.extend(["-project", str(project_path)])

        # Target platform
        cmd.extend(["-platform", options.target.value])

        # Build configuration
        cmd.extend(["-clientconfig", options.flavor.value])

        # Build options
        if options.build:
            cmd.append("-build")
        if options.cook:
            cmd.append("-cook")
        if options.stage:
            cmd.append("-stage")
        if options.archive:
            cmd.append("-archive")
        if options.pak:
            cmd.append("-pak")
        if options.prereqs:
            cmd.append("-prereqs")
        if options.distribution:
            cmd.append("-distribution")

        # Staging directory
        if options.staging_directory:
            cmd.extend(["-stagingdirectory", str(options.staging_directory)])

        # Archive directory
        if options.archive_directory:
            cmd.extend(["-archivedirectory", str(options.archive_directory)])

        # Compression
        if options.compressed:
            cmd.append("-compressed")

        # Extra arguments
        cmd.extend(options.extra_args)

        # Log file
        cmd.extend(["-stdout", "-FullStdoutLogOutput", f"-LogCmds=\"LogSaveToFile {log_file}\""])

        return cmd

    def _get_packaged_content_dir(
        self,
        project_path: Path,
        options: PackageOptions
    ) -> Path:
        """Get packaged content directory.

        Args:
            project_path: Path to .uproject file.
            options: Packaging options.

        Returns:
            Path to packaged content directory.
        """
        project_name = project_path.stem
        platform_map = {
            CookTarget.WINDOWS: "Windows",
            CookTarget.WINDOWS_SERVER: "WindowsServer",
            CookTarget.MAC: "Mac",
            CookTarget.LINUX: "Linux",
            CookTarget.LINUX_SERVER: "LinuxServer",
            CookTarget.ANDROID: "Android",
            CookTarget.IOS: "IOS",
            CookTarget.TVOS: "TVOS",
            CookTarget.PS5: "PS5",
            CookTarget.XBOX_SERIES_X: "XboxSeriesX",
            CookTarget.XBOX_SERIES_X_SERVER: "XboxSeriesXServer",
        }
        
        platform = platform_map.get(options.target, options.target.value)
        
        if options.archive_directory:
            return options.archive_directory
        elif options.staging_directory:
            return options.staging_directory
        else:
            return (
                project_path.parent / "Saved" / "StagedBuilds" / 
                platform / project_name / options.flavor.value
            )

    def _execute_uat_command(
        self,
        cmd: List[str],
        log_file: Path
    ) -> tuple[bool, List[str], List[str]]:
        """Execute UAT command and parse results.

        Args:
            cmd: Command to execute.
            log_file: Path to log file.

        Returns:
            Tuple of (success, errors, warnings).
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            # Execute command
            env = os.environ.copy()
            
            # Add engine binaries to PATH for Windows
            if os.name == 'nt':
                engine_bin_dir = self.engine_path / "Engine" / "Binaries" / "Win64"
                if engine_bin_dir.exists():
                    env["PATH"] = str(engine_bin_dir) + os.pathsep + env["PATH"]

            # Run UAT command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=self.engine_path
            )

            # Write output to log file
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Command: {' '.join(cmd)}\n\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)

            # Parse output for errors and warnings
            output = result.stdout + "\n" + result.stderr
            
            # Look for common error patterns
            error_patterns = [
                "ERROR:",
                "Failed to",
                "Error:",
                "exception",
                "fatal error",
                "build failed",
                "cook failed",
                "package failed",
            ]
            
            warning_patterns = [
                "WARNING:",
                "Warning:",
                "deprecated",
                "obsolete",
            ]

            for line in output.split('\n'):
                line_lower = line.lower()
                # Check for errors
                for pattern in error_patterns:
                    if pattern.lower() in line_lower:
                        errors.append(line.strip())
                        break
                # Check for warnings
                for pattern in warning_patterns:
                    if pattern.lower() in line_lower:
                        warnings.append(line.strip())
                        break

            # Check return code
            success = result.returncode == 0
            
            # If command succeeded but we found errors in output, still mark as failure
            if success and errors:
                # Some errors might be non-fatal, but we'll log them
                pass

            return success, errors, warnings

        except subprocess.CalledProcessError as e:
            error_msg = f"UAT command failed with return code {e.returncode}: {e}"
            errors.append(error_msg)
            return False, errors, warnings
        except Exception as e:
            error_msg = f"Failed to execute UAT command: {e}"
            errors.append(error_msg)
            return False, errors, warnings

    def get_cook_status(
        self,
        project_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Get cooking status for a project.

        Args:
            project_path: Optional project path (overrides instance project_path).

        Returns:
            Dictionary containing cooking status information.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            return {"error": "No project path specified"}

        status: Dict[str, Any] = {
            "project": str(current_project),
            "cooked_content": {},
            "staged_content": {},
            "packaged_content": {},
        }

        # Check for cooked content
        cooked_dir = current_project.parent / "Saved" / "Cooked"
        if cooked_dir.exists():
            for platform_dir in cooked_dir.iterdir():
                if platform_dir.is_dir():
                    platform_name = platform_dir.name
                    status["cooked_content"][platform_name] = {}
                    
                    for config_dir in platform_dir.iterdir():
                        if config_dir.is_dir():
                            config_name = config_dir.name
                            content_count = sum(1 for _ in config_dir.rglob("*") if _.is_file())
                            status["cooked_content"][platform_name][config_name] = {
                                "path": str(config_dir),
                                "file_count": content_count,
                                "exists": True,
                            }

        # Check for staged content
        staged_dir = current_project.parent / "Saved" / "StagedBuilds"
        if staged_dir.exists():
            for platform_dir in staged_dir.iterdir():
                if platform_dir.is_dir():
                    platform_name = platform_dir.name
                    status["staged_content"][platform_name] = {}
                    
                    for config_dir in platform_dir.iterdir():
                        if config_dir.is_dir():
                            config_name = config_dir.name
                            content_count = sum(1 for _ in config_dir.rglob("*") if _.is_file())
                            status["staged_content"][platform_name][config_name] = {
                                "path": str(config_dir),
                                "file_count": content_count,
                                "exists": True,
                            }

        # Check for packaged content
        packaged_dir = current_project.parent / "Saved" / "Packaged"
        if packaged_dir.exists():
            for platform_dir in packaged_dir.iterdir():
                if platform_dir.is_dir():
                    platform_name = platform_dir.name
                    status["packaged_content"][platform_name] = {}
                    
                    for config_dir in platform_dir.iterdir():
                        if config_dir.is_dir():
                            config_name = config_dir.name
                            content_count = sum(1 for _ in config_dir.rglob("*") if _.is_file())
                            status["packaged_content"][platform_name][config_name] = {
                                "path": str(config_dir),
                                "file_count": content_count,
                                "exists": True,
                            }

        return status

    def clean_cooked_content(
        self,
        project_path: Optional[Union[str, Path]] = None,
        platform: Optional[str] = None,
        config: Optional[str] = None
    ) -> bool:
        """Clean cooked content for a project.

        Args:
            project_path: Optional project path (overrides instance project_path).
            platform: Optional platform to clean (None for all).
            config: Optional configuration to clean (None for all).

        Returns:
            True if cleaning succeeded, False otherwise.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            return False

        cooked_dir = current_project.parent / "Saved" / "Cooked"
        if not cooked_dir.exists():
            return True  # Nothing to clean

        try:
            if platform:
                platform_dir = cooked_dir / platform
                if platform_dir.exists():
                    if config:
                        config_dir = platform_dir / config
                        if config_dir.exists():
                            shutil.rmtree(config_dir)
                    else:
                        shutil.rmtree(platform_dir)
            else:
                # Clean all cooked content
                shutil.rmtree(cooked_dir)
                cooked_dir.mkdir(parents=True, exist_ok=True)

            return True

        except Exception as e:
            print(f"Failed to clean cooked content: {e}")
            return False

    def clean_staged_content(
        self,
        project_path: Optional[Union[str, Path]] = None,
        platform: Optional[str] = None,
        config: Optional[str] = None
    ) -> bool:
        """Clean staged content for a project.

        Args:
            project_path: Optional project path (overrides instance project_path).
            platform: Optional platform to clean (None for all).
            config: Optional configuration to clean (None for all).

        Returns:
            True if cleaning succeeded, False otherwise.
        """
        if project_path:
            current_project = Path(project_path).resolve()
        elif self.project_path:
            current_project = self.project_path
        else:
            return False

        staged_dir = current_project.parent / "Saved" / "StagedBuilds"
        if not staged_dir.exists():
            return True  # Nothing to clean

        try:
            if platform:
                platform_dir = staged_dir / platform
                if platform_dir.exists():
                    if config:
                        config_dir = platform_dir / config
                        if config_dir.exists():
                            shutil.rmtree(config_dir)
                    else:
                        shutil.rmtree(platform_dir)
            else:
                # Clean all staged content
                shutil.rmtree(staged_dir)
                staged_dir.mkdir(parents=True, exist_ok=True)

            return True

        except Exception as e:
            print(f"Failed to clean staged content: {e}")
            return False
