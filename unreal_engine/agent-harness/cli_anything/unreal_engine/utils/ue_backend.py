"""Unreal Engine CLI - Backend utilities for UE engine detection.

Provides engine path detection, environment variable management,
and platform-specific UE5 installation discovery.
"""

import json
import os
import platform
import subprocess
import winreg
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class EngineInstallation:
    """Represents a UE5 engine installation.

    Attributes:
        version: Engine version string (e.g., "5.4.0").
        path: Installation path.
        association: Engine association identifier.
        is_source_build: Whether this is a source build.
        is_launcher_build: Whether this is an Epic Games Launcher install.
    """
    version: str
    path: Path
    association: str
    is_source_build: bool = False
    is_launcher_build: bool = False


@dataclass
class UEEnvironment:
    """UE5 environment configuration.

    Attributes:
        engine_path: Path to the active engine installation.
        project_path: Path to the current project (if any).
        platform_sdk_paths: Dictionary of platform SDK paths.
        additional_paths: Additional PATH entries.
        environment_variables: Environment variable overrides.
    """
    engine_path: Optional[Path] = None
    project_path: Optional[Path] = None
    platform_sdk_paths: Dict[str, Path] = field(default_factory=dict)
    additional_paths: List[Path] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)


class UEBackendError(Exception):
    """Base exception for UE backend operations."""
    pass


class EngineNotFoundError(UEBackendError):
    """Raised when a requested engine version cannot be found."""
    pass


class InvalidEnginePathError(UEBackendError):
    """Raised when an engine path is invalid."""
    pass


class UEEngineLocator:
    """Locates UE5 engine installations on the system.

    This class searches for UE5 installations in standard locations
    including Epic Games Launcher installs, custom builds, and
    environment variable overrides.

    Example:
        >>> from utils.ue_backend import UEEngineLocator
        >>> locator = UEEngineLocator()
        >>> 
        >>> # Find all installations
        >>> all_engines = locator.find_all_engines()
        >>> 
        >>> # Find specific version
        >>> engine_54 = locator.find_engine("5.4")
        >>> 
        >>> # Get default engine
        >>> default = locator.get_default_engine()
    """

    # Standard installation paths
    _LAUNCHER_PATHS = {
        "Windows": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.0",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.1",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.2",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.3",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.4",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games" / "UE_5.5",
            Path(os.environ.get("LOCALAPPDATA", "")) / "EpicGamesLauncher" / "InstalledEngines",
        ],
        "Darwin": [
            Path("/Users/Shared/Epic Games/UE_5.0"),
            Path("/Users/Shared/Epic Games/UE_5.1"),
            Path("/Users/Shared/Epic Games/UE_5.2"),
            Path("/Users/Shared/Epic Games/UE_5.3"),
            Path("/Users/Shared/Epic Games/UE_5.4"),
            Path("/Users/Shared/Epic Games/UE_5.5"),
            Path.home() / "Epic Games" / "UE_5.0",
            Path.home() / "Epic Games" / "UE_5.1",
            Path.home() / "Epic Games" / "UE_5.2",
            Path.home() / "Epic Games" / "UE_5.3",
            Path.home() / "Epic Games" / "UE_5.4",
            Path.home() / "Epic Games" / "UE_5.5",
        ],
        "Linux": [
            Path.home() / "Epic Games" / "UE_5.0",
            Path.home() / "Epic Games" / "UE_5.1",
            Path.home() / "Epic Games" / "UE_5.2",
            Path.home() / "Epic Games" / "UE_5.3",
            Path.home() / "Epic Games" / "UE_5.4",
            Path.home() / "Epic Games" / "UE_5.5",
            Path("/opt/Epic Games/UE_5.0"),
            Path("/opt/Epic Games/UE_5.1"),
            Path("/opt/Epic Games/UE_5.2"),
            Path("/opt/Epic Games/UE_5.3"),
            Path("/opt/Epic Games/UE_5.4"),
            Path("/opt/Epic Games/UE_5.5"),
        ],
    }

    def __init__(self):
        """Initialize the engine locator."""
        self._cache: Dict[str, EngineInstallation] = {}
        self._cache_valid = False

    def find_all_engines(self) -> List[EngineInstallation]:
        """Find all UE5 installations on the system.

        Returns:
            List of EngineInstallation objects.
        """
        engines: List[EngineInstallation] = []
        found_paths: set = set()

        # Check Epic Games Launcher installations
        launcher_engines = self._find_launcher_engines()
        for engine in launcher_engines:
            if str(engine.path) not in found_paths:
                engines.append(engine)
                found_paths.add(str(engine.path))

        # Check Windows registry
        if platform.system() == "Windows":
            registry_engines = self._find_registry_engines()
            for engine in registry_engines:
                if str(engine.path) not in found_paths:
                    engines.append(engine)
                    found_paths.add(str(engine.path))

        # Check environment variables
        env_engines = self._find_env_engines()
        for engine in env_engines:
            if str(engine.path) not in found_paths:
                engines.append(engine)
                found_paths.add(str(engine.path))

        # Check Epic Games Launcher data file
        data_engines = self._find_data_file_engines()
        for engine in data_engines:
            if str(engine.path) not in found_paths:
                engines.append(engine)
                found_paths.add(str(engine.path))

        # Sort by version
        engines.sort(key=lambda e: self._version_key(e.version), reverse=True)

        return engines

    def find_engine(
        self,
        version: Optional[str] = None,
        association: Optional[str] = None,
    ) -> EngineInstallation:
        """Find a specific engine installation.

        Args:
            version: Engine version to find (e.g., "5.4" or "5.4.0").
            association: Engine association identifier.

        Returns:
            EngineInstallation matching the criteria.

        Raises:
            EngineNotFoundError: If no matching engine is found.
        """
        all_engines = self.find_all_engines()

        if not all_engines:
            raise EngineNotFoundError("No UE5 installations found on this system")

        # If no criteria specified, return newest
        if version is None and association is None:
            return all_engines[0]

        # Search for matching engine
        for engine in all_engines:
            if version and engine.version.startswith(version):
                return engine
            if association and engine.association == association:
                return engine

        raise EngineNotFoundError(
            f"Engine not found: version={version}, association={association}"
        )

    def get_default_engine(self) -> EngineInstallation:
        """Get the default (newest) engine installation.

        Returns:
            The newest installed engine.

        Raises:
            EngineNotFoundError: If no engines are found.
        """
        return self.find_engine()

    def validate_engine_path(self, path: Union[str, Path]) -> bool:
        """Validate that a path contains a valid UE5 installation.

        Args:
            path: Path to validate.

        Returns:
            True if valid, False otherwise.
        """
        path_obj = Path(path).resolve()

        # Check for required directories
        required = [
            path_obj / "Engine",
            path_obj / "Engine" / "Build",
            path_obj / "Engine" / "Binaries",
        ]

        for req in required:
            if not req.exists():
                return False

        # Check for Build.version file
        version_file = path_obj / "Engine" / "Build" / "Build.version"
        if not version_file.exists():
            return False

        return True

    def get_engine_version(self, path: Union[str, Path]) -> Optional[str]:
        """Get the version of an engine installation.

        Args:
            path: Path to the engine installation.

        Returns:
            Version string (e.g., "5.4.0") or None if invalid.
        """
        path_obj = Path(path).resolve()
        version_file = path_obj / "Engine" / "Build" / "Build.version"

        if not version_file.exists():
            return None

        try:
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            major = data.get("MajorVersion", 0)
            minor = data.get("MinorVersion", 0)
            patch = data.get("PatchVersion", 0)
            return f"{major}.{minor}.{patch}"
        except (json.JSONDecodeError, IOError):
            return None

    def _find_launcher_engines(self) -> List[EngineInstallation]:
        """Find engines installed via Epic Games Launcher."""
        engines: List[EngineInstallation] = []
        system = platform.system()

        paths = self._LAUNCHER_PATHS.get(system, [])

        for path in paths:
            if not path.exists():
                continue

            # Check if this is a version directory
            if path.name.startswith("UE_"):
                version = path.name.replace("UE_", "")
                if self.validate_engine_path(path):
                    engines.append(EngineInstallation(
                        version=version,
                        path=path,
                        association=version,
                        is_launcher_build=True,
                    ))
            else:
                # Check subdirectories
                for subdir in path.iterdir():
                    if subdir.is_dir() and subdir.name.startswith("UE_"):
                        version = subdir.name.replace("UE_", "")
                        if self.validate_engine_path(subdir):
                            engines.append(EngineInstallation(
                                version=version,
                                path=subdir,
                                association=version,
                                is_launcher_build=True,
                            ))

        return engines

    def _find_registry_engines(self) -> List[EngineInstallation]:
        """Find engines from Windows registry."""
        engines: List[EngineInstallation] = []

        if platform.system() != "Windows":
            return engines

        try:
            # Check HKEY_CURRENT_USER
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Epic Games\Unreal Engine\Builds"
            ) as key:
                index = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                        index += 1
                        if isinstance(value, str):
                            path = Path(value)
                            if self.validate_engine_path(path):
                                version = self.get_engine_version(path) or name
                                engines.append(EngineInstallation(
                                    version=version,
                                    path=path,
                                    association=name,
                                    is_source_build=True,
                                ))
                    except OSError:
                        break
        except FileNotFoundError:
            pass

        return engines

    def _find_env_engines(self) -> List[EngineInstallation]:
        """Find engines from environment variables."""
        engines: List[EngineInstallation] = []

        # Check UE_ENGINE_PATH
        env_path = os.environ.get("UE_ENGINE_PATH")
        if env_path:
            path = Path(env_path)
            if self.validate_engine_path(path):
                version = self.get_engine_version(path) or "unknown"
                engines.append(EngineInstallation(
                    version=version,
                    path=path,
                    association="env",
                    is_source_build=True,
                ))

        # Check for version-specific variables
        for version in ["5.0", "5.1", "5.2", "5.3", "5.4", "5.5"]:
            env_var = f"UE_{version.replace('.', '_')}_PATH"
            env_path = os.environ.get(env_var)
            if env_path:
                path = Path(env_path)
                if self.validate_engine_path(path):
                    engines.append(EngineInstallation(
                        version=version,
                        path=path,
                        association=f"env_{version}",
                        is_source_build=True,
                    ))

        return engines

    def _find_data_file_engines(self) -> List[EngineInstallation]:
        """Find engines from Epic Games Launcher data file."""
        engines: List[EngineInstallation] = []

        data_file_paths: List[Path] = []

        if platform.system() == "Windows":
            app_data = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
            data_file_paths.append(
                Path(app_data) / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"
            )
        elif platform.system() == "Darwin":
            data_file_paths.append(
                Path.home() / "Library" / "Application Support" / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"
            )
        else:  # Linux
            data_file_paths.append(
                Path.home() / ".config" / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"
            )

        for data_file in data_file_paths:
            if not data_file.exists():
                continue

            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for installation in data.get("InstallationList", []):
                    install_path = Path(installation.get("InstallLocation", ""))
                    app_name = installation.get("AppName", "")

                    if app_name.startswith("UE_") and self.validate_engine_path(install_path):
                        version = app_name.replace("UE_", "")
                        engines.append(EngineInstallation(
                            version=version,
                            path=install_path,
                            association=version,
                            is_launcher_build=True,
                        ))
            except (json.JSONDecodeError, IOError):
                continue

        return engines

    def _version_key(self, version: str) -> tuple:
        """Convert version string to sortable tuple."""
        parts = version.split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts[:3])


class UEBackend:
    """Manages UE5 backend operations and environment.

    This class provides a high-level interface for managing UE5
    engine paths, environment variables, and platform SDKs.

    Example:
        >>> from utils.ue_backend import UEBackend, UEEngineLocator
        >>> locator = UEEngineLocator()
        >>> engine = locator.find_engine("5.4")
        >>> 
        >>> backend = UEBackend(engine.path)
        >>> env = backend.setup_environment()
    """

    def __init__(self, engine_path: Union[str, Path]):
        """Initialize the backend.

        Args:
            engine_path: Path to the UE5 engine installation.

        Raises:
            InvalidEnginePathError: If the engine path is invalid.
        """
        self.engine_path = Path(engine_path).resolve()
        self.locator = UEEngineLocator()

        if not self.locator.validate_engine_path(self.engine_path):
            raise InvalidEnginePathError(f"Invalid engine path: {engine_path}")

        self._version = self.locator.get_engine_version(self.engine_path)

    def setup_environment(
        self,
        project_path: Optional[Union[str, Path]] = None,
    ) -> UEEnvironment:
        """Set up the UE5 environment for building.

        Args:
            project_path: Optional path to the project.

        Returns:
            UEEnvironment with configured paths and variables.
        """
        env = UEEnvironment(
            engine_path=self.engine_path,
            project_path=Path(project_path) if project_path else None,
        )

        # Set up platform SDKs
        env.platform_sdk_paths = self._detect_platform_sdks()

        # Set up additional PATH entries
        env.additional_paths = self._get_tool_paths()

        # Set environment variables
        env.environment_variables = self._get_env_variables()

        return env

    def apply_environment(self, env: UEEnvironment) -> Dict[str, str]:
        """Apply environment configuration to the current process.

        Args:
            env: Environment configuration to apply.

        Returns:
            Dictionary of modified environment variables.
        """
        modified: Dict[str, str] = {}

        # Apply environment variables
        for key, value in env.environment_variables.items():
            os.environ[key] = value
            modified[key] = value

        # Update PATH
        if env.additional_paths:
            current_path = os.environ.get("PATH", "")
            new_paths = [str(p) for p in env.additional_paths if str(p) not in current_path]
            if new_paths:
                os.environ["PATH"] = os.pathsep.join(new_paths + [current_path])
                modified["PATH"] = os.environ["PATH"]

        return modified

    def get_build_version(self) -> Dict[str, Any]:
        """Get the engine build version information.

        Returns:
            Dictionary containing version information.
        """
        version_file = self.engine_path / "Engine" / "Build" / "Build.version"

        if not version_file.exists():
            return {}

        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def get_compatible_changeset(self) -> Optional[str]:
        """Get the compatible Perforce changeset for this engine.

        Returns:
            Changeset string or None if not available.
        """
        version_info = self.get_build_version()
        return version_info.get("CompatibleChangelist")

    def _detect_platform_sdks(self) -> Dict[str, Path]:
        """Detect installed platform SDKs."""
        sdks: Dict[str, Path] = {}
        system = platform.system()

        if system == "Windows":
            # Windows SDK
            sdks["Windows"] = self._find_windows_sdk()
            # Visual Studio
            sdks["VisualStudio"] = self._find_visual_studio()
        elif system == "Darwin":
            # Xcode
            sdks["Xcode"] = self._find_xcode()
        else:  # Linux
            # Linux toolchain
            sdks["Linux"] = self._find_linux_toolchain()

        # Android SDK
        android_sdk = self._find_android_sdk()
        if android_sdk:
            sdks["Android"] = android_sdk

        return sdks

    def _get_tool_paths(self) -> List[Path]:
        """Get additional tool paths for the engine."""
        paths: List[Path] = []

        # Engine binaries
        system = platform.system()
        if system == "Windows":
            paths.append(self.engine_path / "Engine" / "Binaries" / "Win64")
        elif system == "Darwin":
            paths.append(self.engine_path / "Engine" / "Binaries" / "Mac")
        else:
            paths.append(self.engine_path / "Engine" / "Binaries" / "Linux")

        # Build batch files
        paths.append(self.engine_path / "Engine" / "Build" / "BatchFiles")

        return paths

    def _get_env_variables(self) -> Dict[str, str]:
        """Get required environment variables."""
        env: Dict[str, str] = {}

        # UE_ENGINE_PATH
        env["UE_ENGINE_PATH"] = str(self.engine_path)

        # UE_ENGINE_DIR (legacy)
        env["UE_ENGINE_DIR"] = str(self.engine_path / "Engine")

        return env

    def _find_windows_sdk(self) -> Optional[Path]:
        """Find Windows SDK installation."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows Kits\Installed Roots"
            ) as key:
                sdk_path, _ = winreg.QueryValueEx(key, "KitsRoot10")
                return Path(sdk_path) if sdk_path else None
        except (FileNotFoundError, OSError):
            return None

    def _find_visual_studio(self) -> Optional[Path]:
        """Find Visual Studio installation."""
        vs_paths = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Microsoft Visual Studio" / "2022",
            Path(os.environ.get("PROGRAMFILES(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio" / "2019",
        ]

        for base_path in vs_paths:
            if base_path.exists():
                for edition in ["Enterprise", "Professional", "Community", "BuildTools"]:
                    vs_path = base_path / edition
                    if vs_path.exists():
                        return vs_path

        return None

    def _find_xcode(self) -> Optional[Path]:
        """Find Xcode installation on macOS."""
        xcode_path = Path("/Applications/Xcode.app")
        if xcode_path.exists():
            return xcode_path
        return None

    def _find_linux_toolchain(self) -> Optional[Path]:
        """Find Linux toolchain."""
        # Check for common compiler paths
        for path in [Path("/usr/bin/gcc"), Path("/usr/bin/clang")]:
            if path.exists():
                return path.parent
        return None

    def _find_android_sdk(self) -> Optional[Path]:
        """Find Android SDK installation."""
        # Check environment variables
        sdk_path = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK")
        if sdk_path:
            path = Path(sdk_path)
            if path.exists():
                return path

        # Check default locations
        default_paths = [
            Path.home() / "AppData" / "Local" / "Android" / "Sdk",  # Windows
            Path.home() / "Library" / "Android" / "sdk",  # macOS
            Path.home() / "Android" / "Sdk",  # Linux
        ]

        for path in default_paths:
            if path.exists():
                return path

        return None

    @property
    def version(self) -> Optional[str]:
        """Engine version string."""
        return self._version
