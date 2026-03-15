"""Unreal Engine CLI - Path management module for UE projects.

Provides project path resolution, Content directory management, plugin path
management, and virtual path (/Game/...) to physical path conversion.
Supports standard UE directory structures.

Example:
    >>> from utils.path_manager import PathManager
    >>> pm = PathManager(Path("D:/Projects/MyGame/MyGame.uproject"))
    >>> content_path = pm.get_content_path()
    >>> asset_path = pm.virtual_to_physical("/Game/Blueprints/MyBP")
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.ue_backend import UEEngineLocator, EngineNotFoundError


class PathManagerError(Exception):
    """Base exception for path manager operations."""
    pass


class InvalidProjectPathError(PathManagerError):
    """Raised when project path is invalid."""
    pass


class InvalidAssetPathError(PathManagerError):
    """Raised when asset path is invalid."""
    pass


class PathNotFoundError(PathManagerError):
    """Raised when path does not exist."""
    pass


class EnginePathNotFoundError(PathManagerError):
    """Raised when engine path cannot be determined."""
    pass


class PathManager:
    """UE path manager for project and engine path resolution.

    Manages various UE project paths including Content directories, plugin
    directories, config directories, etc. Supports virtual path (e.g., /Game/...)
    to physical path conversion.

    Attributes:
        VIRTUAL_PREFIXES: Mapping of supported virtual path prefixes.

    Example:
        >>> from utils.path_manager import PathManager
        >>> pm = PathManager(Path("D:/Projects/MyGame/MyGame.uproject"))
        >>> content_path = pm.get_content_path()
        >>> asset_path = pm.virtual_to_physical("/Game/Blueprints/MyBP")
    """

    # Virtual path prefix to relative path mapping
    VIRTUAL_PREFIXES: Dict[str, str] = {
        "/Game/": "Content/",
        "/Engine/": "Engine/Content/",
        "/Config/": "Config/",
        "/Saved/": "Saved/",
        "/Plugins/": "Plugins/",
        "/Script/": "Source/",
    }

    # Standard UE directory structure
    STANDARD_DIRECTORIES: List[str] = [
        "Config",
        "Content",
        "Plugins",
        "Source",
        "Saved",
        "Binaries",
        "Intermediate",
    ]

    def __init__(
        self,
        project_path: Union[str, Path],
        engine_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the path manager.

        Args:
            project_path: Path to .uproject file or project root directory.
            engine_path: Optional path to UE engine installation. If not provided,
                        will attempt to auto-detect from project association.

        Raises:
            InvalidProjectPathError: When project path is invalid.
            EnginePathNotFoundError: When engine path cannot be determined.
        """
        self._project_path: Path = Path(project_path).resolve()

        # If .uproject file is passed, get parent directory as project root
        if self._project_path.is_file():
            if self._project_path.suffix != ".uproject":
                raise InvalidProjectPathError(
                    f"Not a valid .uproject file: {self._project_path}"
                )
            self._project_root: Path = self._project_path.parent
        else:
            # Assume directory was passed, try to find .uproject file
            self._project_root = self._project_path
            uproject_files = list(self._project_root.glob("*.uproject"))
            if uproject_files:
                self._project_path = uproject_files[0]

        if not self._project_root.exists():
            raise InvalidProjectPathError(
                f"Project path does not exist: {self._project_root}"
            )

        # Initialize engine path
        self._engine_path: Optional[Path] = None
        if engine_path:
            self._engine_path = Path(engine_path).resolve()
        else:
            self._engine_path = self._detect_engine_path()

        self._cached_content_path: Optional[Path] = None
        self._cached_plugins_path: Optional[Path] = None
        self._cached_engine_plugins_path: Optional[Path] = None

    def _detect_engine_path(self) -> Optional[Path]:
        """Detect engine path from project association.

        Returns:
            Path to engine installation or None if not found.
        """
        try:
            # Try to read engine association from .uproject file
            import json
            with open(self._project_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            engine_assoc = project_data.get("EngineAssociation")
            if engine_assoc:
                locator = UEEngineLocator()
                try:
                    engine = locator.find_engine(association=engine_assoc)
                    return engine.path
                except EngineNotFoundError:
                    # Try by version
                    try:
                        engine = locator.find_engine(version=engine_assoc)
                        return engine.path
                    except EngineNotFoundError:
                        pass
        except (IOError, json.JSONDecodeError):
            pass

        return None

    @property
    def project_root(self) -> Path:
        """Get project root directory.

        Returns:
            Path to project root directory.
        """
        return self._project_root

    @property
    def project_file(self) -> Path:
        """Get project file path (.uproject).

        Returns:
            Path to .uproject file.
        """
        return self._project_path

    @property
    def engine_path(self) -> Optional[Path]:
        """Get engine installation path.

        Returns:
            Path to engine installation or None if not detected.
        """
        return self._engine_path

    def get_content_path(self) -> Path:
        """Get Content directory path.

        Returns:
            Full path to Content directory.
        """
        if self._cached_content_path is None:
            self._cached_content_path = self._project_root / "Content"
        return self._cached_content_path

    def get_config_path(self) -> Path:
        """Get Config directory path.

        Returns:
            Full path to Config directory.
        """
        return self._project_root / "Config"

    def get_source_path(self) -> Path:
        """Get Source directory path.

        Returns:
            Full path to Source directory.
        """
        return self._project_root / "Source"

    def get_plugins_path(self) -> Path:
        """Get project Plugins directory path.

        Returns:
            Full path to project Plugins directory.
        """
        if self._cached_plugins_path is None:
            self._cached_plugins_path = self._project_root / "Plugins"
        return self._cached_plugins_path

    def get_engine_plugins_path(self) -> Optional[Path]:
        """Get engine Plugins directory path.

        Returns:
            Full path to Engine/Plugins directory or None if engine not detected.
        """
        if self._cached_engine_plugins_path is None and self._engine_path:
            self._cached_engine_plugins_path = self._engine_path / "Engine" / "Plugins"
        return self._cached_engine_plugins_path

    def get_saved_path(self) -> Path:
        """Get Saved directory path.

        Returns:
            Full path to Saved directory.
        """
        return self._project_root / "Saved"

    def get_intermediate_path(self) -> Path:
        """Get Intermediate directory path.

        Returns:
            Full path to Intermediate directory.
        """
        return self._project_root / "Intermediate"

    def get_binaries_path(self) -> Path:
        """Get Binaries directory path.

        Returns:
            Full path to Binaries directory.
        """
        return self._project_root / "Binaries"

    def get_logs_path(self) -> Path:
        """Get logs directory path.

        Returns:
            Full path to Saved/Logs directory.
        """
        return self.get_saved_path() / "Logs"

    def get_cooked_path(self, platform: Optional[str] = None) -> Path:
        """Get Cooked content directory path.

        Args:
            platform: Target platform name (e.g., Win64, Android).
                     If None, returns the Cooked directory itself.

        Returns:
            Full path to Cooked content directory.
        """
        cooked = self.get_saved_path() / "Cooked"
        if platform:
            return cooked / platform
        return cooked

    def get_staging_path(self) -> Path:
        """Get Staging directory path.

        Returns:
            Full path to Saved/StagedBuilds directory.
        """
        return self.get_saved_path() / "StagedBuilds"

    def virtual_to_physical(
        self, virtual_path: str, extension: Optional[str] = None
    ) -> Path:
        """Convert virtual path to physical path.

        Supported virtual path prefixes:
        - /Game/ -> Content/
        - /Engine/ -> Engine/Content/ (requires engine_path)
        - /Config/ -> Config/
        - /Plugins/ -> Plugins/
        - /Script/ -> Source/

        Args:
            virtual_path: Virtual path (e.g., /Game/Blueprints/MyBP).
            extension: Optional file extension (e.g., .uasset, .umap).

        Returns:
            Converted physical path.

        Raises:
            InvalidAssetPathError: When virtual path format is invalid.
            EnginePathNotFoundError: When /Engine/ path is used but engine
                                     path is not available.
        """
        if not virtual_path.startswith("/"):
            raise InvalidAssetPathError(
                f"Virtual path must start with '/': {virtual_path}"
            )

        # Handle /Game/ prefix
        if virtual_path.startswith("/Game/"):
            relative_path = virtual_path[6:]  # Remove /Game/
            physical_path = self.get_content_path() / relative_path.replace("/", os.sep)

        # Handle /Engine/ prefix
        elif virtual_path.startswith("/Engine/"):
            if not self._engine_path:
                raise EnginePathNotFoundError(
                    "Engine path not available for /Engine/ virtual path resolution"
                )
            relative_path = virtual_path[8:]  # Remove /Engine/
            engine_content = self._engine_path / "Engine" / "Content"
            physical_path = engine_content / relative_path.replace("/", os.sep)

        # Handle /Config/ prefix
        elif virtual_path.startswith("/Config/"):
            relative_path = virtual_path[8:]  # Remove /Config/
            physical_path = self.get_config_path() / relative_path.replace("/", os.sep)

        # Handle /Plugins/ prefix - check both project and engine plugins
        elif virtual_path.startswith("/Plugins/"):
            relative_path = virtual_path[9:]  # Remove /Plugins/
            # First check project plugins
            project_plugins = self.get_plugins_path()
            physical_path = project_plugins / relative_path.replace("/", os.sep)

        # Handle /Script/ prefix
        elif virtual_path.startswith("/Script/"):
            relative_path = virtual_path[8:]  # Remove /Script/
            physical_path = self.get_source_path() / relative_path.replace("/", os.sep)

        else:
            raise InvalidAssetPathError(f"Unknown virtual path prefix: {virtual_path}")

        # Add extension if provided
        if extension:
            if not extension.startswith("."):
                extension = "." + extension
            physical_path = physical_path.with_suffix(extension)

        return physical_path

    def physical_to_virtual(self, physical_path: Union[str, Path]) -> str:
        """Convert physical path to virtual path.

        Args:
            physical_path: Physical file or directory path.

        Returns:
            Virtual path (e.g., /Game/Blueprints/MyBP).

        Raises:
            InvalidAssetPathError: When path cannot be converted to virtual path.
        """
        path = Path(physical_path).resolve()

        # Try matching content path
        content_path = self.get_content_path()
        if content_path in path.parents or path == content_path:
            relative = path.relative_to(content_path)
            return "/Game/" + str(relative).replace(os.sep, "/")

        # Try matching engine content path
        if self._engine_path:
            engine_content = self._engine_path / "Engine" / "Content"
            if engine_content.exists() and (engine_content in path.parents or path == engine_content):
                relative = path.relative_to(engine_content)
                return "/Engine/" + str(relative).replace(os.sep, "/")

        # Try matching config path
        config_path = self.get_config_path()
        if config_path in path.parents or path == config_path:
            relative = path.relative_to(config_path)
            return "/Config/" + str(relative).replace(os.sep, "/")

        # Try matching project plugins path
        plugins_path = self.get_plugins_path()
        if plugins_path.exists() and (plugins_path in path.parents or path == plugins_path):
            relative = path.relative_to(plugins_path)
            return "/Plugins/" + str(relative).replace(os.sep, "/")

        # Try matching engine plugins path
        engine_plugins = self.get_engine_plugins_path()
        if engine_plugins and engine_plugins.exists():
            if engine_plugins in path.parents or path == engine_plugins:
                relative = path.relative_to(engine_plugins)
                return "/Plugins/" + str(relative).replace(os.sep, "/")

        # Try matching source path
        source_path = self.get_source_path()
        if source_path.exists() and (source_path in path.parents or path == source_path):
            relative = path.relative_to(source_path)
            return "/Script/" + str(relative).replace(os.sep, "/")

        raise InvalidAssetPathError(
            f"Path is not within project directories: {physical_path}"
        )

    def get_plugin_path(self, plugin_name: str) -> Path:
        """Get specific plugin directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to plugin directory.
        """
        return self.get_plugins_path() / plugin_name

    def get_engine_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Get specific engine plugin directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to engine plugin directory or None if engine not available.
        """
        engine_plugins = self.get_engine_plugins_path()
        if engine_plugins:
            return engine_plugins / plugin_name
        return None

    def get_plugin_content_path(self, plugin_name: str) -> Path:
        """Get plugin Content directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to plugin Content directory.
        """
        return self.get_plugin_path(plugin_name) / "Content"

    def get_engine_plugin_content_path(self, plugin_name: str) -> Optional[Path]:
        """Get engine plugin Content directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to engine plugin Content directory or None if not available.
        """
        plugin_path = self.get_engine_plugin_path(plugin_name)
        if plugin_path:
            return plugin_path / "Content"
        return None

    def get_plugin_config_path(self, plugin_name: str) -> Path:
        """Get plugin Config directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to plugin Config directory.
        """
        return self.get_plugin_path(plugin_name) / "Config"

    def get_plugin_source_path(self, plugin_name: str) -> Path:
        """Get plugin Source directory path.

        Args:
            plugin_name: Plugin name.

        Returns:
            Full path to plugin Source directory.
        """
        return self.get_plugin_path(plugin_name) / "Source"

    def list_plugins(self) -> List[str]:
        """List all plugins in the project.

        Returns:
            List of plugin names.
        """
        plugins_path = self.get_plugins_path()
        if not plugins_path.exists():
            return []

        return [
            d.name
            for d in plugins_path.iterdir()
            if d.is_dir() and (d / f"{d.name}.uplugin").exists()
        ]

    def list_engine_plugins(self) -> List[str]:
        """List all plugins in the engine.

        Returns:
            List of engine plugin names.
        """
        engine_plugins = self.get_engine_plugins_path()
        if not engine_plugins or not engine_plugins.exists():
            return []

        return [
            d.name
            for d in engine_plugins.iterdir()
            if d.is_dir() and (d / f"{d.name}.uplugin").exists()
        ]

    def plugin_exists(self, plugin_name: str) -> bool:
        """Check if plugin exists in project.

        Args:
            plugin_name: Plugin name.

        Returns:
            True if plugin exists in project.
        """
        plugin_path = self.get_plugin_path(plugin_name)
        uplugin_file = plugin_path / f"{plugin_name}.uplugin"
        return uplugin_file.exists()

    def engine_plugin_exists(self, plugin_name: str) -> bool:
        """Check if plugin exists in engine.

        Args:
            plugin_name: Plugin name.

        Returns:
            True if plugin exists in engine.
        """
        plugin_path = self.get_engine_plugin_path(plugin_name)
        if plugin_path:
            uplugin_file = plugin_path / f"{plugin_name}.uplugin"
            return uplugin_file.exists()
        return False

    def find_plugin(self, plugin_name: str) -> Optional[Path]:
        """Find plugin in project or engine.

        Args:
            plugin_name: Plugin name.

        Returns:
            Path to plugin directory or None if not found.
        """
        # Check project plugins first
        if self.plugin_exists(plugin_name):
            return self.get_plugin_path(plugin_name)

        # Check engine plugins
        if self.engine_plugin_exists(plugin_name):
            return self.get_engine_plugin_path(plugin_name)

        return None

    def get_module_path(self, module_name: str) -> Path:
        """Get module Source directory path.

        Args:
            module_name: Module name.

        Returns:
            Full path to module Source directory.
        """
        return self.get_source_path() / module_name

    def list_modules(self) -> List[str]:
        """List all modules in the project.

        Returns:
            List of module names (based on subdirectories in Source).
        """
        source_path = self.get_source_path()
        if not source_path.exists():
            return []

        modules = []
        for item in source_path.iterdir():
            if item.is_dir():
                # Check for .Build.cs files
                build_files = list(item.glob("*.Build.cs"))
                if build_files:
                    modules.append(item.name)

        return modules

    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if not.

        Args:
            path: Directory path.

        Returns:
            Full path to directory.
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    def ensure_project_structure(self) -> None:
        """Ensure project has standard UE directory structure.

        Creates missing standard directories (Config, Content, Source).
        """
        for dir_name in ["Config", "Content", "Source"]:
            self.ensure_directory(self._project_root / dir_name)

    def is_valid_asset_path(self, virtual_path: str) -> bool:
        """Check if virtual path is valid.

        Args:
            virtual_path: Virtual path.

        Returns:
            True if path format is valid.
        """
        try:
            self.virtual_to_physical(virtual_path)
            return True
        except (InvalidAssetPathError, EnginePathNotFoundError):
            return False

    def get_relative_to_project(self, path: Union[str, Path]) -> Path:
        """Get path relative to project root.

        Args:
            path: Absolute or relative path.

        Returns:
            Path relative to project root.
        """
        path_obj = Path(path).resolve()
        return path_obj.relative_to(self._project_root)

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path, supporting virtual paths and relative paths.

        Args:
            path: Path string, can be virtual path, relative path, or absolute path.

        Returns:
            Resolved absolute path.

        Raises:
            InvalidAssetPathError: When path cannot be resolved.
        """
        path_str = str(path)

        # Virtual path
        if path_str.startswith("/"):
            return self.virtual_to_physical(path_str)

        # Relative or absolute path
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj.resolve()

        # Relative to project root
        return (self._project_root / path_obj).resolve()

    def get_asset_directory(self, asset_type: str) -> Path:
        """Get recommended directory for specific asset type.

        Args:
            asset_type: Asset type (e.g., Blueprints, Materials, Meshes, Textures).

        Returns:
            Full path to recommended directory.
        """
        return self.get_content_path() / asset_type

    def suggest_asset_path(
        self, asset_name: str, asset_type: str, subfolder: Optional[str] = None
    ) -> str:
        """Suggest asset storage path.

        Args:
            asset_name: Asset name.
            asset_type: Asset type (e.g., Blueprints, Materials).
            subfolder: Optional subfolder.

        Returns:
            Suggested virtual path (e.g., /Game/Blueprints/Subfolder/AssetName).
        """
        if subfolder:
            return f"/Game/{asset_type}/{subfolder}/{asset_name}"
        return f"/Game/{asset_type}/{asset_name}"

    def find_assets(
        self,
        pattern: str = "*.uasset",
        content_path: Optional[Union[str, Path]] = None,
        recursive: bool = True,
    ) -> List[Path]:
        """Find asset files.

        Args:
            pattern: File glob pattern.
            content_path: Starting path for search, defaults to Content directory.
            recursive: Whether to search recursively.

        Returns:
            List of matching asset file paths.
        """
        search_path = Path(content_path) if content_path else self.get_content_path()

        if not search_path.exists():
            return []

        if recursive:
            return list(search_path.rglob(pattern))
        return list(search_path.glob(pattern))

    def get_project_name(self) -> str:
        """Get project name.

        Returns:
            Project name (.uproject filename without extension).
        """
        return self._project_path.stem

    def get_backup_path(self) -> Path:
        """Get backup directory path.

        Returns:
            Full path to Saved/Backups directory.
        """
        return self.get_saved_path() / "Backups"

    def get_crash_dump_path(self) -> Path:
        """Get crash dump directory path.

        Returns:
            Full path to Saved/Crashes directory.
        """
        return self.get_saved_path() / "Crashes"

    def __repr__(self) -> str:
        """Return string representation of object.

        Returns:
            String containing project path.
        """
        return f"PathManager(project_root='{self._project_root}')"
