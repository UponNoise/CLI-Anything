"""Unreal Engine CLI - Core project management module.

Handles create, open, save, info, and settings for UE5 projects.
The project format is a .uproject JSON file that tracks modules,
plugins, engine association, and project settings.
"""

import json
import os
import copy
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ProjectVersion(Enum):
    """UE5 project format versions."""
    V5_0 = "5.0"
    V5_1 = "5.1"
    V5_2 = "5.2"
    V5_3 = "5.3"
    V5_4 = "5.4"
    V5_5 = "5.5"


# Default project settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "Description": "",
    "Category": "",
    "CreatedBy": "",
    "CreatedByURL": "",
    "DocsURL": "",
    "MarketplaceURL": "",
    "SupportURL": "",
    "EngineVersion": "5.4.0",
    "IsEnterpriseProject": False,
}

# Default module configuration
DEFAULT_GAME_MODULE: Dict[str, Any] = {
    "Name": "Game",
    "Type": "Runtime",
    "LoadingPhase": "Default",
    "AdditionalDependencies": [],
}

# Default target configurations
DEFAULT_TARGET_CONFIGS: Dict[str, Any] = {
    "Game": {"TargetType": "Game"},
    "Editor": {"TargetType": "Editor"},
    "Client": {"TargetType": "Client"},
    "Server": {"TargetType": "Server"},
}


class UEProjectError(Exception):
    """Base exception for UE project operations."""
    pass


class InvalidProjectError(UEProjectError):
    """Raised when project file is invalid or corrupted."""
    pass


class ProjectNotFoundError(UEProjectError):
    """Raised when project file cannot be found."""
    pass


def create_project(
    name: str,
    engine_version: str = "5.4.0",
    engine_association: Optional[str] = None,
    description: str = "",
    category: str = "",
    created_by: str = "",
    is_enterprise: bool = False,
    include_starter_content: bool = True,
    target_platforms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new UE5 project configuration.

    Args:
        name: Project name (used for module naming).
        engine_version: Target UE5 version (e.g., "5.4.0").
        engine_association: Engine identifier or path. If None, uses version.
        description: Project description.
        category: Project category.
        created_by: Author/creator name.
        is_enterprise: Whether this is an enterprise project.
        include_starter_content: Whether to include starter content.
        target_platforms: List of target platforms (e.g., ["Win64", "Mac", "Linux"]).

    Returns:
        A dictionary representing the .uproject file structure.

    Raises:
        ValueError: If engine_version is not a valid UE5 version.
    """
    # Validate engine version format
    if not _is_valid_engine_version(engine_version):
        raise ValueError(
            f"Invalid engine version: {engine_version}. "
            "Expected format: X.Y.Z (e.g., 5.4.0)"
        )

    # Determine engine association
    assoc = engine_association or engine_version

    # Default target platforms
    platforms = target_platforms or ["Win64"]

    project: Dict[str, Any] = {
        "FileVersion": 3,
        "EngineAssociation": assoc,
        "Category": category,
        "Description": description,
        "CreatedBy": created_by,
        "IsEnterpriseProject": is_enterprise,
        "Modules": [
            {
                "Name": name,
                "Type": "Runtime",
                "LoadingPhase": "Default",
            }
        ],
        "Plugins": _get_default_plugins(include_starter_content),
        "TargetPlatforms": platforms,
        "AdditionalProperties": {
            "IncludeStarterContent": include_starter_content,
        },
        "Metadata": {
            "Created": datetime.now().isoformat(),
            "Modified": datetime.now().isoformat(),
            "Version": "1.0.0",
            "CLIVersion": "ue5-cli 1.0",
        },
    }

    return project


def open_project(path: Union[str, Path]) -> Dict[str, Any]:
    """Open an existing .uproject file.

    Args:
        path: Path to the .uproject file.

    Returns:
        A dictionary containing the project configuration.

    Raises:
        ProjectNotFoundError: If the project file does not exist.
        InvalidProjectError: If the project file is invalid.
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        raise ProjectNotFoundError(f"Project file not found: {path}")
    
    if not path_obj.suffix == ".uproject":
        raise InvalidProjectError(f"Invalid project file extension: {path}")

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            project = json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidProjectError(f"Invalid JSON in project file: {e}")
    except Exception as e:
        raise UEProjectError(f"Failed to read project file: {e}")

    # Validate required fields
    if "FileVersion" not in project:
        raise InvalidProjectError(f"Missing FileVersion in project: {path}")
    
    if "EngineAssociation" not in project:
        raise InvalidProjectError(f"Missing EngineAssociation in project: {path}")

    return project


def save_project(
    project: Dict[str, Any],
    path: Union[str, Path],
    backup: bool = True,
) -> str:
    """Save project to a .uproject file.

    Args:
        project: The project dictionary to save.
        path: Destination path for the .uproject file.
        backup: Whether to create a backup of existing file.

    Returns:
        The absolute path where the project was saved.

    Raises:
        UEProjectError: If the save operation fails.
    """
    path_obj = Path(path).resolve()
    
    # Ensure .uproject extension
    if path_obj.suffix != ".uproject":
        path_obj = path_obj.with_suffix(".uproject")

    # Create backup if file exists
    if backup and path_obj.exists():
        backup_path = path_obj.with_suffix(".uproject.backup")
        try:
            shutil.copyfile(path_obj, backup_path)
        except Exception as e:
            raise UEProjectError(f"Failed to create backup: {e}")

    # Update metadata
    if "Metadata" not in project:
        project["Metadata"] = {}
    project["Metadata"]["Modified"] = datetime.now().isoformat()

    # Ensure parent directory exists
    try:
        path_obj.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise UEProjectError(f"Failed to create directory: {e}")

    # Write project file
    try:
        with open(path_obj, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise UEProjectError(f"Failed to write project file: {e}")

    return str(path_obj)


def get_project_info(project: Dict[str, Any]) -> Dict[str, Any]:
    """Get summary information about the project.

    Args:
        project: The project dictionary.

    Returns:
        A dictionary containing project summary information.
    """
    modules = project.get("Modules", [])
    plugins = project.get("Plugins", [])
    
    # Get module names
    module_names = [m.get("Name", "Unknown") for m in modules]
    
    # Get plugin names
    plugin_names = [p.get("Name", "Unknown") for p in plugins]
    enabled_plugins = [p.get("Name") for p in plugins if p.get("Enabled", True)]
    
    # Get target platforms
    platforms = project.get("TargetPlatforms", [])
    
    # Get metadata
    metadata = project.get("Metadata", {})

    return {
        "name": modules[0].get("Name", "Unknown") if modules else "Unknown",
        "engine_association": project.get("EngineAssociation", "Unknown"),
        "category": project.get("Category", ""),
        "description": project.get("Description", ""),
        "created_by": project.get("CreatedBy", ""),
        "is_enterprise": project.get("IsEnterpriseProject", False),
        "module_count": len(modules),
        "modules": module_names,
        "plugin_count": len(plugins),
        "plugins": plugin_names,
        "enabled_plugins": enabled_plugins,
        "target_platforms": platforms,
        "created": metadata.get("Created", "Unknown"),
        "modified": metadata.get("Modified", "Unknown"),
        "version": metadata.get("Version", "Unknown"),
    }


def set_settings(
    project: Dict[str, Any],
    description: Optional[str] = None,
    category: Optional[str] = None,
    created_by: Optional[str] = None,
    engine_association: Optional[str] = None,
    is_enterprise: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update project settings.

    Args:
        project: The project dictionary to modify.
        description: New project description.
        category: New project category.
        created_by: New creator name.
        engine_association: New engine association.
        is_enterprise: New enterprise flag.

    Returns:
        The updated project dictionary.
    """
    if description is not None:
        project["Description"] = description
    
    if category is not None:
        project["Category"] = category
    
    if created_by is not None:
        project["CreatedBy"] = created_by
    
    if engine_association is not None:
        project["EngineAssociation"] = engine_association
    
    if is_enterprise is not None:
        project["IsEnterpriseProject"] = is_enterprise

    return project


def add_module(
    project: Dict[str, Any],
    name: str,
    module_type: str = "Runtime",
    loading_phase: str = "Default",
    additional_dependencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Add a module to the project.

    Args:
        project: The project dictionary to modify.
        name: Module name.
        module_type: Module type (Runtime, Editor, etc.).
        loading_phase: Loading phase (Default, PostConfigInit, etc.).
        additional_dependencies: List of additional module dependencies.

    Returns:
        The updated project dictionary.

    Raises:
        ValueError: If a module with the same name already exists.
    """
    if "Modules" not in project:
        project["Modules"] = []

    # Check for duplicates
    for mod in project["Modules"]:
        if mod.get("Name") == name:
            raise ValueError(f"Module '{name}' already exists in project")

    module: Dict[str, Any] = {
        "Name": name,
        "Type": module_type,
        "LoadingPhase": loading_phase,
    }

    if additional_dependencies:
        module["AdditionalDependencies"] = additional_dependencies

    project["Modules"].append(module)
    return project


def remove_module(project: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Remove a module from the project.

    Args:
        project: The project dictionary to modify.
        name: Name of the module to remove.

    Returns:
        The updated project dictionary.

    Raises:
        ValueError: If the module does not exist.
    """
    if "Modules" not in project:
        raise ValueError("Project has no modules")

    original_count = len(project["Modules"])
    project["Modules"] = [m for m in project["Modules"] if m.get("Name") != name]

    if len(project["Modules"]) == original_count:
        raise ValueError(f"Module '{name}' not found in project")

    return project


def add_plugin(
    project: Dict[str, Any],
    name: str,
    enabled: bool = True,
    optional: bool = False,
    marketplace_url: Optional[str] = None,
    supported_target_platforms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Add a plugin to the project.

    Args:
        project: The project dictionary to modify.
        name: Plugin name.
        enabled: Whether the plugin is enabled.
        optional: Whether the plugin is optional.
        marketplace_url: URL to marketplace page.
        supported_target_platforms: List of supported platforms.

    Returns:
        The updated project dictionary.
    """
    if "Plugins" not in project:
        project["Plugins"] = []

    # Check if plugin already exists
    for plugin in project["Plugins"]:
        if plugin.get("Name") == name:
            # Update existing plugin
            plugin["Enabled"] = enabled
            if optional:
                plugin["Optional"] = optional
            if marketplace_url:
                plugin["MarketplaceURL"] = marketplace_url
            if supported_target_platforms:
                plugin["SupportedTargetPlatforms"] = supported_target_platforms
            return project

    # Add new plugin
    plugin: Dict[str, Any] = {
        "Name": name,
        "Enabled": enabled,
    }

    if optional:
        plugin["Optional"] = optional
    if marketplace_url:
        plugin["MarketplaceURL"] = marketplace_url
    if supported_target_platforms:
        plugin["SupportedTargetPlatforms"] = supported_target_platforms

    project["Plugins"].append(plugin)
    return project


def remove_plugin(project: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Remove a plugin from the project.

    Args:
        project: The project dictionary to modify.
        name: Name of the plugin to remove.

    Returns:
        The updated project dictionary.

    Raises:
        ValueError: If the plugin does not exist.
    """
    if "Plugins" not in project:
        raise ValueError("Project has no plugins")

    original_count = len(project["Plugins"])
    project["Plugins"] = [p for p in project["Plugins"] if p.get("Name") != name]

    if len(project["Plugins"]) == original_count:
        raise ValueError(f"Plugin '{name}' not found in project")

    return project


def _is_valid_engine_version(version: str) -> bool:
    """Check if engine version string is valid.

    Args:
        version: Version string to validate.

    Returns:
        True if valid, False otherwise.
    """
    parts = version.split(".")
    if len(parts) < 2:
        return False
    try:
        major = int(parts[0])
        minor = int(parts[1])
        # UE5 starts at version 5
        return major >= 5
    except ValueError:
        return False


def _get_default_plugins(include_starter_content: bool) -> List[Dict[str, Any]]:
    """Get default plugin configuration.

    Args:
        include_starter_content: Whether to include starter content plugin.

    Returns:
        List of default plugin configurations.
    """
    plugins: List[Dict[str, Any]] = [
        {"Name": "ModelingToolsEditorMode", "Enabled": True},
    ]

    if include_starter_content:
        plugins.append({"Name": "StarterContent", "Enabled": True})

    return plugins
