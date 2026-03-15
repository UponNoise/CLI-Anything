"""Unreal Engine CLI - Plugin management module.

Handles plugin discovery, installation, enabling, disabling, and creation.
Supports both project plugins and engine plugins.
"""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from urllib.request import urlopen

# Note: UEEnvironment and EngineInstallation are imported conditionally
# to avoid circular imports. These types are only used for type hints.


class PluginType(Enum):
    """UE5 plugin types."""
    RUNTIME = "Runtime"
    EDITOR = "Editor"
    PROGRAM = "Program"
    THIRDPARTY = "ThirdParty"
    ENTERPRISE = "Enterprise"


class PluginCategory(Enum):
    """UE5 plugin categories."""
    AI = "AI"
    ANIMATION = "Animation"
    AUDIO = "Audio"
    BLUEPRINT = "Blueprint"
    CINEMATICS = "Cinematics"
    EDITOR = "Editor"
    GAMEPLAY = "Gameplay"
    GRAPHICS = "Graphics"
    INPUT = "Input"
    LEVEL_EDITOR = "LevelEditor"
    MATERIAL = "Material"
    NETWORKING = "Networking"
    PHYSICS = "Physics"
    PLATFORM = "Platform"
    RENDERING = "Rendering"
    SCRIPTING = "Scripting"
    UI = "UI"
    UTILITIES = "Utilities"
    VISUALIZATION = "Visualization"
    VR = "VR"
    OTHER = "Other"


class PluginSource(Enum):
    """Plugin source types."""
    MARKETPLACE = "Marketplace"
    GITHUB = "GitHub"
    LOCAL = "Local"
    CUSTOM = "Custom"


class PluginStatus(Enum):
    """Plugin status."""
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    BROKEN = "Broken"
    OUTDATED = "Outdated"


@dataclass
class PluginInfo:
    """UE5 plugin information.

    Attributes:
        name: Plugin name.
        friendly_name: Human-readable plugin name.
        version: Plugin version string.
        version_name: Version name (e.g., "1.0.0").
        description: Plugin description.
        category: Plugin category.
        created_by: Plugin author.
        created_by_url: Author URL.
        marketplace_url: Marketplace URL (if applicable).
        docs_url: Documentation URL.
        support_url: Support URL.
        enabled_by_default: Whether plugin is enabled by default.
        can_contain_content: Whether plugin can contain content.
        is_beta_version: Whether plugin is in beta.
        is_experimental: Whether plugin is experimental.
        installed: Whether plugin is installed.
        enabled: Whether plugin is enabled.
        is_engine_plugin: Whether this is an engine plugin.
        is_project_plugin: Whether this is a project plugin.
        plugin_type: Plugin type.
        modules: List of plugin modules.
        dependencies: List of plugin dependencies.
        supported_target_platforms: List of supported platforms.
        supported_programs: List of supported programs.
    """
    name: str
    friendly_name: str
    version: str
    version_name: str
    description: str
    category: str
    created_by: str
    created_by_url: str = ""
    marketplace_url: str = ""
    docs_url: str = ""
    support_url: str = ""
    enabled_by_default: bool = False
    can_contain_content: bool = False
    is_beta_version: bool = False
    is_experimental: bool = False
    installed: bool = False
    enabled: bool = False
    is_engine_plugin: bool = False
    is_project_plugin: bool = False
    plugin_type: PluginType = PluginType.RUNTIME
    modules: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    supported_target_platforms: List[str] = field(default_factory=list)
    supported_programs: List[str] = field(default_factory=list)


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin is not found."""
    pass


class PluginInstallationError(PluginError):
    """Raised when plugin installation fails."""
    pass


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not met."""
    pass


class PluginManager:
    """UE5 plugin manager.

    Provides methods for managing UE5 plugins, including listing,
    enabling, disabling, installing, and creating plugins.

    Attributes:
        engine_path: Path to UE5 engine installation.
        project_path: Path to UE5 project.
        environment: UE5 environment configuration.
    """

    def __init__(
        self,
        engine_path: Optional[Path] = None,
        project_path: Optional[Path] = None,
        environment: Optional[Any] = None  # UEEnvironment type
    ) -> None:
        """Initialize plugin manager.

        Args:
            engine_path: Path to UE5 engine installation.
            project_path: Path to UE5 project.
            environment: UE5 environment configuration.
        """
        self.engine_path = engine_path
        self.project_path = project_path
        # Create a simple environment object if none provided
        if environment is None:
            # Create a minimal environment object
            class SimpleEnvironment:
                def __init__(self):
                    self.engine_path = None
                    self.project_path = None
                    self.platform_sdk_paths = {}
                    self.additional_paths = []
                    self.environment_variables = {}
            
            self.environment = SimpleEnvironment()
        else:
            self.environment = environment

        if engine_path:
            self.environment.engine_path = engine_path
        if project_path:
            self.environment.project_path = project_path

    def list_plugins(self, include_engine: bool = True) -> List[PluginInfo]:
        """List all available plugins.

        Args:
            include_engine: Whether to include engine plugins.

        Returns:
            List of PluginInfo objects.

        Raises:
            PluginError: If plugin discovery fails.
        """
        plugins: List[PluginInfo] = []

        # List project plugins
        if self.project_path:
            project_plugins_dir = self.project_path / "Plugins"
            if project_plugins_dir.exists():
                plugins.extend(self._scan_plugin_directory(project_plugins_dir, is_engine=False))

        # List engine plugins
        if include_engine and self.engine_path:
            engine_plugins_dir = self.engine_path / "Engine" / "Plugins"
            if engine_plugins_dir.exists():
                plugins.extend(self._scan_plugin_directory(engine_plugins_dir, is_engine=True))

        return plugins

    def _scan_plugin_directory(
        self,
        plugins_dir: Path,
        is_engine: bool = False
    ) -> List[PluginInfo]:
        """Scan a plugin directory for plugins.

        Args:
            plugins_dir: Directory to scan.
            is_engine: Whether these are engine plugins.

        Returns:
            List of PluginInfo objects.
        """
        plugins: List[PluginInfo] = []

        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Check for plugin descriptor file
            descriptor_file = plugin_dir / f"{plugin_dir.name}.uplugin"
            if not descriptor_file.exists():
                # Check for subdirectories (marketplace plugins)
                for subdir in plugin_dir.iterdir():
                    if subdir.is_dir():
                        sub_descriptor = subdir / f"{subdir.name}.uplugin"
                        if sub_descriptor.exists():
                            plugin_info = self._parse_plugin_descriptor(
                                sub_descriptor, is_engine, is_project=not is_engine
                            )
                            plugins.append(plugin_info)
                continue

            plugin_info = self._parse_plugin_descriptor(
                descriptor_file, is_engine, is_project=not is_engine
            )
            plugins.append(plugin_info)

        return plugins

    def _parse_plugin_descriptor(
        self,
        descriptor_path: Path,
        is_engine: bool,
        is_project: bool
    ) -> PluginInfo:
        """Parse a plugin descriptor file.

        Args:
            descriptor_path: Path to .uplugin file.
            is_engine: Whether this is an engine plugin.
            is_project: Whether this is a project plugin.

        Returns:
            PluginInfo object.

        Raises:
            PluginValidationError: If descriptor is invalid.
        """
        try:
            with open(descriptor_path, 'r', encoding='utf-8') as f:
                descriptor = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise PluginValidationError(
                f"Failed to parse plugin descriptor {descriptor_path}: {e}"
            )

        # Extract plugin information
        name = descriptor.get("FriendlyName", descriptor.get("Name", descriptor_path.parent.name))
        version = descriptor.get("Version", 1)
        version_name = descriptor.get("VersionName", "1.0.0")
        description = descriptor.get("Description", "")
        category = descriptor.get("Category", "Other")
        created_by = descriptor.get("CreatedBy", "")
        created_by_url = descriptor.get("CreatedByURL", "")
        marketplace_url = descriptor.get("MarketplaceURL", "")
        docs_url = descriptor.get("DocsURL", "")
        support_url = descriptor.get("SupportURL", "")
        enabled_by_default = descriptor.get("EnabledByDefault", False)
        can_contain_content = descriptor.get("CanContainContent", False)
        is_beta_version = descriptor.get("IsBetaVersion", False)
        is_experimental = descriptor.get("IsExperimental", False)

        # Determine plugin type
        plugin_type_str = descriptor.get("Type", "Runtime")
        try:
            plugin_type = PluginType(plugin_type_str)
        except ValueError:
            plugin_type = PluginType.RUNTIME

        # Get modules
        modules = descriptor.get("Modules", [])

        # Get dependencies
        dependencies = descriptor.get("Plugins", [])

        # Get supported platforms
        supported_target_platforms = descriptor.get("SupportedTargetPlatforms", [])

        # Get supported programs
        supported_programs = descriptor.get("SupportedPrograms", [])

        # Check if plugin is enabled
        enabled = self._is_plugin_enabled(descriptor_path.parent)

        return PluginInfo(
            name=descriptor_path.parent.name,
            friendly_name=name,
            version=str(version),
            version_name=version_name,
            description=description,
            category=category,
            created_by=created_by,
            created_by_url=created_by_url,
            marketplace_url=marketplace_url,
            docs_url=docs_url,
            support_url=support_url,
            enabled_by_default=enabled_by_default,
            can_contain_content=can_contain_content,
            is_beta_version=is_beta_version,
            is_experimental=is_experimental,
            installed=True,
            enabled=enabled,
            is_engine_plugin=is_engine,
            is_project_plugin=is_project,
            plugin_type=plugin_type,
            modules=modules,
            dependencies=dependencies,
            supported_target_platforms=supported_target_platforms,
            supported_programs=supported_programs,
        )

    def _is_plugin_enabled(self, plugin_dir: Path) -> bool:
        """Check if a plugin is enabled.

        Args:
            plugin_dir: Plugin directory.

        Returns:
            True if plugin is enabled, False otherwise.
        """
        # Check project plugins configuration
        if self.project_path:
            project_config = self.project_path / "Config"
            if project_config.exists():
                # Check DefaultGame.ini
                default_game_ini = project_config / "DefaultGame.ini"
                if default_game_ini.exists():
                    try:
                        with open(default_game_ini, 'r', encoding='utf-8') as f:
                            content = f.read()
                            plugin_name = plugin_dir.name
                            # Look for plugin enable/disable configuration
                            if f"+Plugins={plugin_name}" in content:
                                return True
                            elif f"-Plugins={plugin_name}" in content:
                                return False
                    except OSError:
                        pass

        # Check plugin descriptor
        descriptor_file = plugin_dir / f"{plugin_dir.name}.uplugin"
        if descriptor_file.exists():
            try:
                with open(descriptor_file, 'r', encoding='utf-8') as f:
                    descriptor = json.load(f)
                return descriptor.get("EnabledByDefault", False)
            except (json.JSONDecodeError, OSError):
                pass

        return False

    def enable_plugin(self, plugin_name: str, enable: bool = True) -> bool:
        """Enable or disable a plugin.

        Args:
            plugin_name: Name of the plugin to enable/disable.
            enable: True to enable, False to disable.

        Returns:
            True if operation succeeded, False otherwise.

        Raises:
            PluginNotFoundError: If plugin is not found.
            PluginError: If plugin operation fails.
        """
        # Find the plugin
        plugin_info = self._find_plugin(plugin_name)
        if not plugin_info:
            raise PluginNotFoundError(f"Plugin '{plugin_name}' not found")

        # Update project configuration
        if self.project_path:
            success = self._update_project_plugin_config(plugin_name, enable)
            if success:
                # Also update the plugin descriptor if it's a project plugin
                if plugin_info.is_project_plugin:
                    self._update_plugin_descriptor(plugin_info, enable)
                return True

        return False

    def _find_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Find a plugin by name.

        Args:
            plugin_name: Name of the plugin to find.

        Returns:
            PluginInfo if found, None otherwise.
        """
        plugins = self.list_plugins(include_engine=True)
        for plugin in plugins:
            if plugin.name == plugin_name:
                return plugin
        return None

    def _update_project_plugin_config(
        self,
        plugin_name: str,
        enable: bool
    ) -> bool:
        """Update project plugin configuration.

        Args:
            plugin_name: Plugin name.
            enable: True to enable, False to disable.

        Returns:
            True if update succeeded, False otherwise.
        """
        if not self.project_path:
            return False

        config_dir = self.project_path / "Config"
        config_dir.mkdir(exist_ok=True)

        default_game_ini = config_dir / "DefaultGame.ini"
        try:
            # Read existing configuration
            lines = []
            if default_game_ini.exists():
                with open(default_game_ini, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            # Update plugin configuration
            updated = False
            new_lines = []
            plugin_section = False

            for line in lines:
                stripped = line.strip()

                # Check if we're in the plugins section
                if stripped.startswith('[/Script/Engine.ProjectPackagingSettings]'):
                    plugin_section = True
                elif stripped.startswith('[') and plugin_section:
                    plugin_section = False

                # Update plugin entry
                if plugin_section and stripped.startswith(('+Plugins=', '-Plugins=')):
                    if plugin_name in stripped:
                        # Replace existing entry
                        new_lines.append(f"{'+' if enable else '-'}Plugins={plugin_name}\n")
                        updated = True
                        continue

                new_lines.append(line)

            # Add new entry if not found
            if not updated:
                # Find the plugins section or add it
                if not plugin_section:
                    new_lines.append('\n[/Script/Engine.ProjectPackagingSettings]\n')
                new_lines.append(f"{'+' if enable else '-'}Plugins={plugin_name}\n")

            # Write updated configuration
            with open(default_game_ini, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return True

        except OSError as e:
            raise PluginError(f"Failed to update project configuration: {e}")

    def _update_plugin_descriptor(
        self,
        plugin_info: PluginInfo,
        enable: bool
    ) -> bool:
        """Update plugin descriptor file.

        Args:
            plugin_info: Plugin information.
            enable: True to enable, False to disable.

        Returns:
            True if update succeeded, False otherwise.
        """
        # Find plugin directory
        plugin_dir = None
        if plugin_info.is_project_plugin and self.project_path:
            plugin_dir = self.project_path / "Plugins" / plugin_info.name
        elif plugin_info.is_engine_plugin and self.engine_path:
            plugin_dir = self.engine_path / "Engine" / "Plugins" / plugin_info.name

        if not plugin_dir or not plugin_dir.exists():
            return False

        descriptor_file = plugin_dir / f"{plugin_info.name}.uplugin"
        if not descriptor_file.exists():
            return False

        try:
            with open(descriptor_file, 'r', encoding='utf-8') as f:
                descriptor = json.load(f)

            # Update EnabledByDefault
            descriptor["EnabledByDefault"] = enable

            # Write updated descriptor
            with open(descriptor_file, 'w', encoding='utf-8') as f:
                json.dump(descriptor, f, indent=2)

            return True

        except (json.JSONDecodeError, OSError) as e:
            raise PluginError(f"Failed to update plugin descriptor: {e}")

    def install_plugin(
        self,
        source: str,
        plugin_name: Optional[str] = None,
        destination: Optional[Path] = None
    ) -> PluginInfo:
        """Install a plugin from various sources.

        Args:
            source: Plugin source (URL, local path, or marketplace ID).
            plugin_name: Optional plugin name (for marketplace plugins).
            destination: Optional installation directory.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
            PluginValidationError: If plugin validation fails.
        """
        # Determine installation directory
        if destination is None:
            if self.project_path:
                destination = self.project_path / "Plugins"
            else:
                raise PluginInstallationError(
                    "No project path specified and no destination provided"
                )

        # Create destination directory if it doesn't exist
        destination.mkdir(parents=True, exist_ok=True)

        # Determine source type and install
        if source.startswith(('http://', 'https://')):
            return self._install_from_url(source, destination, plugin_name)
        elif Path(source).exists():
            return self._install_from_local(Path(source), destination, plugin_name)
        else:
            # Assume marketplace ID
            return self._install_from_marketplace(source, destination, plugin_name)

    def _install_from_url(
        self,
        url: str,
        destination: Path,
        plugin_name: Optional[str] = None
    ) -> PluginInfo:
        """Install plugin from URL.

        Args:
            url: Plugin download URL.
            destination: Installation directory.
            plugin_name: Optional plugin name.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
        """
        try:
            # Download plugin
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "plugin.zip"
                
                # Download file
                with urlopen(url) as response:
                    with open(temp_path, 'wb') as f:
                        f.write(response.read())

                # Extract and install
                return self._install_from_archive(temp_path, destination, plugin_name)

        except Exception as e:
            raise PluginInstallationError(f"Failed to install plugin from URL {url}: {e}")

    def _install_from_local(
        self,
        source_path: Path,
        destination: Path,
        plugin_name: Optional[str] = None
    ) -> PluginInfo:
        """Install plugin from local path.

        Args:
            source_path: Local plugin path (directory or archive).
            destination: Installation directory.
            plugin_name: Optional plugin name.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
        """
        try:
            if source_path.is_dir():
                # Directory installation
                return self._install_from_directory(source_path, destination, plugin_name)
            elif source_path.suffix.lower() in ['.zip', '.7z', '.rar']:
                # Archive installation
                return self._install_from_archive(source_path, destination, plugin_name)
            else:
                raise PluginInstallationError(
                    f"Unsupported file type: {source_path.suffix}"
                )

        except Exception as e:
            raise PluginInstallationError(f"Failed to install plugin from local path: {e}")

    def _install_from_marketplace(
        self,
        marketplace_id: str,
        destination: Path,
        plugin_name: Optional[str] = None
    ) -> PluginInfo:
        """Install plugin from Epic Marketplace.

        Args:
            marketplace_id: Marketplace plugin ID.
            destination: Installation directory.
            plugin_name: Optional plugin name.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
        """
        # Note: Marketplace integration would require authentication
        # and API access. This is a placeholder implementation.
        raise PluginInstallationError(
            "Marketplace installation not yet implemented. "
            "Please download the plugin manually and use local installation."
        )

    def _install_from_archive(
        self,
        archive_path: Path,
        destination: Path,
        plugin_name: Optional[str] = None
    ) -> PluginInfo:
        """Install plugin from archive file.

        Args:
            archive_path: Path to archive file.
            destination: Installation directory.
            plugin_name: Optional plugin name.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract archive
                if archive_path.suffix.lower() == '.zip':
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                else:
                    # For other archive types, we would need additional libraries
                    raise PluginInstallationError(
                        f"Unsupported archive type: {archive_path.suffix}"
                    )

                # Find plugin directory
                plugin_dir = self._find_plugin_in_directory(temp_path, plugin_name)
                if not plugin_dir:
                    raise PluginInstallationError(
                        "Could not find plugin in archive"
                    )

                # Install from directory
                return self._install_from_directory(plugin_dir, destination, plugin_name)

        except Exception as e:
            raise PluginInstallationError(f"Failed to install plugin from archive: {e}")

    def _install_from_directory(
        self,
        source_dir: Path,
        destination: Path,
        plugin_name: Optional[str] = None
    ) -> PluginInfo:
        """Install plugin from directory.

        Args:
            source_dir: Source plugin directory.
            destination: Installation directory.
            plugin_name: Optional plugin name.

        Returns:
            PluginInfo for the installed plugin.

        Raises:
            PluginInstallationError: If installation fails.
        """
        try:
            # Find plugin descriptor
            descriptor_file = None
            for file in source_dir.iterdir():
                if file.suffix == '.uplugin':
                    descriptor_file = file
                    break

            if not descriptor_file:
                # Check subdirectories
                for subdir in source_dir.iterdir():
                    if subdir.is_dir():
                        for file in subdir.iterdir():
                            if file.suffix == '.uplugin':
                                descriptor_file = file
                                source_dir = subdir
                                break
                        if descriptor_file:
                            break

            if not descriptor_file:
                raise PluginValidationError("No .uplugin file found in plugin directory")

            # Determine plugin name
            if plugin_name is None:
                plugin_name = descriptor_file.stem

            # Validate plugin
            self._validate_plugin(source_dir)

            # Copy plugin to destination
            dest_dir = destination / plugin_name
            if dest_dir.exists():
                # Backup existing plugin
                backup_dir = dest_dir.with_suffix('.backup')
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(dest_dir, backup_dir)

            shutil.copytree(source_dir, dest_dir)

            # Parse plugin info
            plugin_info = self._parse_plugin_descriptor(
                descriptor_file,
                is_engine=False,
                is_project=True
            )

            # Enable plugin by default
            self.enable_plugin(plugin_name, plugin_info.enabled_by_default)

            return plugin_info

        except Exception as e:
            raise PluginInstallationError(f"Failed to install plugin from directory: {e}")

    def _find_plugin_in_directory(
        self,
        directory: Path,
        plugin_name: Optional[str] = None
    ) -> Optional[Path]:
        """Find plugin directory in extracted archive.

        Args:
            directory: Directory to search.
            plugin_name: Optional plugin name to look for.

        Returns:
            Path to plugin directory if found, None otherwise.
        """
        # Check for .uplugin files
        for item in directory.rglob("*.uplugin"):
            if plugin_name is None or item.stem == plugin_name:
                return item.parent

        # Check for directories with .uplugin files
        for subdir in directory.iterdir():
            if subdir.is_dir():
                for file in subdir.iterdir():
                    if file.suffix == '.uplugin':
                        if plugin_name is None or file.stem == plugin_name:
                            return subdir

        return None

    def _validate_plugin(self, plugin_dir: Path) -> None:
        """Validate plugin directory structure.

        Args:
            plugin_dir: Plugin directory to validate.

        Raises:
            PluginValidationError: If plugin is invalid.
        """
        # Check for .uplugin file
        descriptor_files = list(plugin_dir.glob("*.uplugin"))
        if not descriptor_files:
            raise PluginValidationError("No .uplugin file found")

        # Check descriptor file
        descriptor_file = descriptor_files[0]
        try:
            with open(descriptor_file, 'r', encoding='utf-8') as f:
                descriptor = json.load(f)

            # Validate required fields
            required_fields = ["FriendlyName", "Version", "VersionName"]
            for field in required_fields:
                if field not in descriptor:
                    raise PluginValidationError(f"Missing required field: {field}")

            # Validate version
            version = descriptor.get("Version", 1)
            if not isinstance(version, int) or version < 1:
                raise PluginValidationError("Invalid version number")

        except json.JSONDecodeError as e:
            raise PluginValidationError(f"Invalid JSON in descriptor: {e}")
        except OSError as e:
            raise PluginValidationError(f"Failed to read descriptor: {e}")

    def create_plugin(
        self,
        name: str,
        template: str = "Blank",
        output_dir: Optional[Path] = None,
        plugin_type: PluginType = PluginType.RUNTIME,
        category: str = "Other",
        description: str = "",
        version: str = "1.0.0"
    ) -> PluginInfo:
        """Create a new plugin.

        Args:
            name: Plugin name.
            template: Plugin template (Blank, ContentOnly, EditorToolbar, etc.).
            output_dir: Output directory (defaults to project Plugins directory).
            plugin_type: Plugin type.
            category: Plugin category.
            description: Plugin description.
            version: Plugin version.

        Returns:
            PluginInfo for the created plugin.

        Raises:
            PluginError: If plugin creation fails.
        """
        # Determine output directory
        if output_dir is None:
            if self.project_path:
                output_dir = self.project_path / "Plugins"
            else:
                raise PluginError("No project path specified and no output directory provided")

        # Create plugin directory
        plugin_dir = output_dir / name
        if plugin_dir.exists():
            raise PluginError(f"Plugin directory already exists: {plugin_dir}")

        try:
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Create plugin descriptor
            descriptor = self._create_plugin_descriptor(
                name=name,
                template=template,
                plugin_type=plugin_type,
                category=category,
                description=description,
                version=version
            )

            descriptor_file = plugin_dir / f"{name}.uplugin"
            with open(descriptor_file, 'w', encoding='utf-8') as f:
                json.dump(descriptor, f, indent=2)

            # Create template-specific files
            self._create_plugin_template_files(plugin_dir, template, name)

            # Parse and return plugin info
            plugin_info = self._parse_plugin_descriptor(
                descriptor_file,
                is_engine=False,
                is_project=True
            )

            return plugin_info

        except Exception as e:
            # Clean up on failure
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            raise PluginError(f"Failed to create plugin: {e}")

    def _create_plugin_descriptor(
        self,
        name: str,
        template: str,
        plugin_type: PluginType,
        category: str,
        description: str,
        version: str
    ) -> Dict[str, Any]:
        """Create plugin descriptor dictionary.

        Args:
            name: Plugin name.
            template: Plugin template.
            plugin_type: Plugin type.
            category: Plugin category.
            description: Plugin description.
            version: Plugin version.

        Returns:
            Plugin descriptor dictionary.
        """
        descriptor: Dict[str, Any] = {
            "FileVersion": 3,
            "Version": 1,
            "VersionName": version,
            "FriendlyName": name,
            "Description": description,
            "Category": category,
            "CreatedBy": "",
            "CreatedByURL": "",
            "DocsURL": "",
            "MarketplaceURL": "",
            "SupportURL": "",
            "EnabledByDefault": True,
            "CanContainContent": template != "Blank",
            "IsBetaVersion": False,
            "IsExperimental": False,
            "Installed": True,
            "Modules": [],
            "Plugins": []
        }

        # Add template-specific configuration
        if template == "Blank":
            descriptor["Modules"] = []
        elif template == "ContentOnly":
            descriptor["CanContainContent"] = True
            descriptor["Modules"] = []
        elif template == "EditorToolbar":
            descriptor["Modules"] = [{
                "Name": f"{name}Editor",
                "Type": "Editor",
                "LoadingPhase": "PostEngineInit"
            }]
        elif template == "Runtime":
            descriptor["Modules"] = [{
                "Name": name,
                "Type": "Runtime",
                "LoadingPhase": "Default"
            }]
        elif template == "Editor":
            descriptor["Modules"] = [{
                "Name": f"{name}Editor",
                "Type": "Editor",
                "LoadingPhase": "PostEngineInit"
            }]

        # Set plugin type
        descriptor["Type"] = plugin_type.value

        return descriptor

    def _create_plugin_template_files(
        self,
        plugin_dir: Path,
        template: str,
        plugin_name: str
    ) -> None:
        """Create template-specific plugin files.

        Args:
            plugin_dir: Plugin directory.
            template: Plugin template.
            plugin_name: Plugin name.
        """
        # Create Source directory for templates that need it
        if template in ["EditorToolbar", "Runtime", "Editor"]:
            source_dir = plugin_dir / "Source"
            source_dir.mkdir(exist_ok=True)

            # Create module directory
            module_name = plugin_name if template == "Runtime" else f"{plugin_name}Editor"
            module_dir = source_dir / module_name
            module_dir.mkdir(exist_ok=True)

            # Create .Build.cs file
            build_cs = module_dir / f"{module_name}.Build.cs"
            build_cs_content = self._generate_build_cs_content(module_name, template)
            build_cs.write_text(build_cs_content)

            # Create module header and source files
            if template in ["Runtime", "Editor"]:
                # Create Public and Private directories
                public_dir = module_dir / "Public"
                private_dir = module_dir / "Private"
                public_dir.mkdir(exist_ok=True)
                private_dir.mkdir(exist_ok=True)

                # Create module header
                module_header = public_dir / f"{module_name}.h"
                module_header_content = self._generate_module_header_content(module_name)
                module_header.write_text(module_header_content)

                # Create module source
                module_source = private_dir / f"{module_name}.cpp"
                module_source_content = self._generate_module_source_content(module_name)
                module_source.write_text(module_source_content)

        # Create Content directory for content templates
        if template == "ContentOnly":
            content_dir = plugin_dir / "Content"
            content_dir.mkdir(exist_ok=True)

    def _generate_build_cs_content(self, module_name: str, template: str) -> str:
        """Generate .Build.cs file content.

        Args:
            module_name: Module name.
            template: Plugin template.

        Returns:
            .Build.cs file content.
        """
        is_editor = template in ["Editor", "EditorToolbar"]
        
        content = f"""using UnrealBuildTool;

public class {module_name} : ModuleRules
{{
    public {module_name}(ReadOnlyTargetRules Target) : base(Target)
    {{
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
        
        PublicDependencyModuleNames.AddRange(
            new string[]
            {{
                "Core",
                "CoreUObject",
                "Engine",
            }}
        );
        
        """
        
        if is_editor:
            content += """        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(
                new string[]
                {
                    "UnrealEd",
                }
            );
        }
        """
        
        content += """    }
}
"""
        return content

    def _generate_module_header_content(self, module_name: str) -> str:
        """Generate module header file content.

        Args:
            module_name: Module name.

        Returns:
            Module header file content.
        """
        return f"""#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class F{module_name}Module : public IModuleInterface
{{
public:
    /** IModuleInterface implementation */
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
}};
"""

    def _generate_module_source_content(self, module_name: str) -> str:
        """Generate module source file content.

        Args:
            module_name: Module name.

        Returns:
            Module source file content.
        """
        return f"""#include "{module_name}.h"

#define LOCTEXT_NAMESPACE "F{module_name}Module"

void F{module_name}Module::StartupModule()
{{
    // This code will execute after your module is loaded into memory;
    // the exact timing is specified in the .uplugin file per-module
}}

void F{module_name}Module::ShutdownModule()
{{
    // This function may be called during shutdown to clean up your module.
}}

#undef LOCTEXT_NAMESPACE
    
IMPLEMENT_MODULE(F{module_name}Module, {module_name})
"""

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Name of the plugin to disable.

        Returns:
            True if operation succeeded, False otherwise.

        Raises:
            PluginNotFoundError: If plugin is not found.
        """
        return self.enable_plugin(plugin_name, enable=False)