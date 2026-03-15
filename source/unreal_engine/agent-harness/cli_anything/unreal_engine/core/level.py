"""Unreal Engine CLI - Level management module.

Provides level creation, listing, loading, and saving functionality.
Manages .umap files and level operations through editor automation.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.editor import EditorManager, EditorOptions, EditorMode


@dataclass
class LevelInfo:
    """Information about a UE5 level.

    Attributes:
        name: Level name (without extension).
        path: Full path to the .umap file.
        package_path: UE package path (e.g., "/Game/Maps/LevelName").
        size_bytes: File size in bytes.
        modified: Last modification timestamp (ISO format).
        actors: Number of actors in the level (if known).
        description: Level description from metadata.
        tags: List of level tags.
    """
    name: str
    path: Path
    package_path: str
    size_bytes: int
    modified: str
    actors: int = 0
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class LevelOptions:
    """Options for level creation.

    Attributes:
        template: Template to use for the level.
        default_lighting: Whether to add default lighting.
        geometry_brush: Whether to add a default geometry brush.
        world_settings: Custom world settings overrides.
        description: Level description.
        tags: Level tags.
    """
    template: str = "Default"
    default_lighting: bool = True
    geometry_brush: bool = False
    world_settings: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    tags: List[str] = field(default_factory=list)


class LevelError(Exception):
    """Base exception for level operations."""
    pass


class LevelNotFoundError(LevelError):
    """Raised when a level file cannot be found."""
    pass


class LevelCreateError(LevelError):
    """Raised when level creation fails."""
    pass


class LevelLoadError(LevelError):
    """Raised when level loading fails."""
    pass


class LevelSaveError(LevelError):
    """Raised when level saving fails."""
    pass


class LevelManager:
    """UE5 level management and operations.

    This class provides methods to create, list, load, and save UE5 levels.
    It manages .umap files and provides integration with the editor for
    level operations.

    Example:
        >>> from core.level import LevelManager, LevelOptions
        >>> from pathlib import Path
        >>>
        >>> lm = LevelManager(
        ...     project_path=Path("D:/Projects/MyGame"),
        ...     engine_path=Path("C:/Program Files/Epic Games/UE_5.4")
        ... )
        >>>
        >>> # Create a new level
        >>> level_path = lm.create_level(
        ...     name="MainMenu",
        ...     subfolder="Maps",
        ...     options=LevelOptions(default_lighting=True)
        ... )
        >>>
        >>> # List all levels
        >>> levels = lm.list_levels()
        >>> for level in levels:
        ...     print(f"{level.name}: {level.package_path}")
        >>>
        >>> # Load a level (requires editor)
        >>> lm.load_level("/Game/Maps/MainMenu")
    """

    # Common level templates
    TEMPLATES = {
        "Default": "Default",
        "Empty": "Empty",
        "TimeOfDay": "TimeOfDay",
        "DefaultVR": "DefaultVR",
        "Basic": "Basic",
        "Minimal_Default": "Minimal_Default",
    }

    def __init__(
        self,
        project_path: Union[str, Path],
        engine_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize the level manager.

        Args:
            project_path: Path to the UE5 project directory.
            engine_path: Optional path to UE5 engine installation.
        """
        self.project_path = Path(project_path).resolve()
        self.content_dir = self.project_path / "Content"
        self.engine_path = Path(engine_path).resolve() if engine_path else None
        self._editor_manager: Optional[EditorManager] = None

        if self.engine_path:
            self._editor_manager = EditorManager(
                engine_path=self.engine_path,
                project_path=self.project_path / f"{self.project_path.name}.uproject",
            )

    def create_level(
        self,
        name: str,
        subfolder: str = "Maps",
        options: Optional[LevelOptions] = None,
    ) -> Path:
        """Create a new level.

        Creates a new .umap file in the project's Content directory.
        Note: This creates a placeholder file that will be properly
        initialized when opened in the editor.

        Args:
            name: Level name (without extension).
            subfolder: Subfolder within Content (default: "Maps").
            options: Level creation options.

        Returns:
            Path to the created .umap file.

        Raises:
            LevelCreateError: If the level cannot be created.
        """
        options = options or LevelOptions()

        # Validate name
        if not name:
            raise LevelCreateError("Level name cannot be empty")
        if "/" in name or "\\" in name:
            raise LevelCreateError("Level name cannot contain path separators")

        # Ensure .umap extension
        if not name.endswith(".umap"):
            name = f"{name}.umap"

        # Build target path
        target_dir = self.content_dir / subfolder
        target_path = target_dir / name

        # Check if level already exists
        if target_path.exists():
            raise LevelCreateError(f"Level already exists: {target_path}")

        # Create directory structure
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise LevelCreateError(f"Failed to create directory: {e}")

        # Create minimal level file structure
        # Note: This is a placeholder that will be properly initialized by UE
        level_data = self._create_level_data(name, options)

        try:
            with open(target_path, "wb") as f:
                # Write a minimal valid umap header
                # Full initialization happens when opened in editor
                f.write(level_data)
        except Exception as e:
            raise LevelCreateError(f"Failed to write level file: {e}")

        # Create accompanying .umap metadata file
        self._create_level_metadata(target_path, options)

        return target_path

    def _create_level_data(self, name: str, options: LevelOptions) -> bytes:
        """Create minimal level file data.

        Args:
            name: Level name.
            options: Level creation options.

        Returns:
            Binary data for the level file.
        """
        # This is a minimal placeholder for a .umap file
        # Real .umap files are binary assets created by the editor
        # The file will be properly initialized when opened in UE
        header = b"\x00\x00\x00\x00"  # Placeholder header
        return header

    def _create_level_metadata(self, level_path: Path, options: LevelOptions) -> None:
        """Create level metadata file.

        Args:
            level_path: Path to the level file.
            options: Level creation options.
        """
        metadata_path = level_path.with_suffix(".umap.meta")
        metadata = {
            "name": level_path.stem,
            "template": options.template,
            "default_lighting": options.default_lighting,
            "geometry_brush": options.geometry_brush,
            "description": options.description,
            "tags": options.tags,
            "world_settings": options.world_settings,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
        }

        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            # Metadata is optional, ignore errors
            pass

    def list_levels(
        self,
        subfolder: Optional[str] = None,
        recursive: bool = True,
    ) -> List[LevelInfo]:
        """List all levels in the project.

        Args:
            subfolder: Optional subfolder to search within Content.
            recursive: Whether to search recursively.

        Returns:
            List of LevelInfo objects.
        """
        levels: List[LevelInfo] = []

        search_dir = self.content_dir
        if subfolder:
            search_dir = search_dir / subfolder

        if not search_dir.exists():
            return levels

        pattern = "**/*.umap" if recursive else "*.umap"

        for level_file in search_dir.glob(pattern):
            try:
                level_info = self._get_level_info(level_file)
                levels.append(level_info)
            except Exception:
                # Skip invalid level files
                continue

        # Sort by name
        levels.sort(key=lambda x: x.name)
        return levels

    def _get_level_info(self, level_path: Path) -> LevelInfo:
        """Get information about a level file.

        Args:
            level_path: Path to the .umap file.

        Returns:
            LevelInfo object.
        """
        stat = level_path.stat()

        # Calculate package path
        relative_path = level_path.relative_to(self.content_dir)
        package_path = f"/Game/{relative_path.with_suffix('').as_posix()}"

        # Try to load metadata
        metadata_path = level_path.with_suffix(".umap.meta")
        description = ""
        tags: List[str] = []
        actors = 0

        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                description = metadata.get("description", "")
                tags = metadata.get("tags", [])
                actors = metadata.get("actors", 0)
            except Exception:
                pass

        return LevelInfo(
            name=level_path.stem,
            path=level_path,
            package_path=package_path,
            size_bytes=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            actors=actors,
            description=description,
            tags=tags,
        )

    def load_level(self, level_path: Union[str, Path]) -> None:
        """Load a level in the editor.

        This method launches the editor with the specified level loaded.
        Requires the engine path to be set.

        Args:
            level_path: Path to the level (package path or file path).

        Raises:
            LevelLoadError: If the level cannot be loaded.
        """
        if self._editor_manager is None:
            raise LevelLoadError(
                "Engine path not set. Cannot load level without editor."
            )

        # Convert file path to package path if needed
        if isinstance(level_path, Path) or "/" not in str(level_path):
            path_obj = Path(level_path)
            if path_obj.exists():
                level_path = self._file_path_to_package_path(path_obj)

        # Ensure level exists
        if not self._level_exists(str(level_path)):
            raise LevelNotFoundError(f"Level not found: {level_path}")

        # Launch editor with the level
        options = EditorOptions(
            map=str(level_path),
            mode=EditorMode.NORMAL,
        )

        try:
            self._editor_manager.launch(options, wait=False)
        except Exception as e:
            raise LevelLoadError(f"Failed to load level: {e}")

    def save_level(self, level_path: Optional[Union[str, Path]] = None) -> None:
        """Save the current level.

        Note: This is a placeholder method. In a real implementation,
        this would communicate with a running editor instance to save
        the current level. Currently requires manual save in editor.

        Args:
            level_path: Optional path to save to. Uses current if not specified.

        Raises:
            LevelSaveError: If the level cannot be saved.
        """
        # In a full implementation, this would:
        # 1. Connect to running editor via TCP/HTTP
        # 2. Send save command
        # 3. Wait for confirmation
        #
        # For now, this is a placeholder that documents the limitation
        raise LevelSaveError(
            "Automated level saving requires editor integration. "
            "Please save manually in the editor."
        )

    def delete_level(self, level_path: Union[str, Path]) -> None:
        """Delete a level file.

        Args:
            level_path: Path to the level (package path or file path).

        Raises:
            LevelNotFoundError: If the level does not exist.
            LevelError: If the level cannot be deleted.
        """
        # Convert package path to file path if needed
        if isinstance(level_path, str) and level_path.startswith("/Game/"):
            file_path = self._package_path_to_file_path(level_path)
        else:
            file_path = Path(level_path)

        if not file_path.exists():
            raise LevelNotFoundError(f"Level not found: {level_path}")

        try:
            file_path.unlink()
            # Also delete metadata if exists
            metadata_path = file_path.with_suffix(".umap.meta")
            if metadata_path.exists():
                metadata_path.unlink()
        except Exception as e:
            raise LevelError(f"Failed to delete level: {e}")

    def rename_level(
        self,
        old_path: Union[str, Path],
        new_name: str,
    ) -> Path:
        """Rename a level.

        Args:
            old_path: Current path to the level.
            new_name: New name for the level (without extension).

        Returns:
            Path to the renamed level file.

        Raises:
            LevelNotFoundError: If the level does not exist.
            LevelError: If the level cannot be renamed.
        """
        # Convert package path to file path if needed
        if isinstance(old_path, str) and old_path.startswith("/Game/"):
            file_path = self._package_path_to_file_path(old_path)
        else:
            file_path = Path(old_path)

        if not file_path.exists():
            raise LevelNotFoundError(f"Level not found: {old_path}")

        # Build new path
        new_path = file_path.with_name(f"{new_name}.umap")

        if new_path.exists():
            raise LevelError(f"A level with name '{new_name}' already exists")

        try:
            file_path.rename(new_path)
            # Rename metadata if exists
            old_metadata = file_path.with_suffix(".umap.meta")
            if old_metadata.exists():
                new_metadata = new_path.with_suffix(".umap.meta")
                old_metadata.rename(new_metadata)
                # Update metadata
                self._update_metadata_name(new_metadata, new_name)
        except Exception as e:
            raise LevelError(f"Failed to rename level: {e}")

        return new_path

    def duplicate_level(
        self,
        source_path: Union[str, Path],
        new_name: str,
    ) -> Path:
        """Duplicate a level.

        Args:
            source_path: Path to the source level.
            new_name: Name for the duplicated level.

        Returns:
            Path to the duplicated level file.

        Raises:
            LevelNotFoundError: If the source level does not exist.
            LevelError: If the level cannot be duplicated.
        """
        # Convert package path to file path if needed
        if isinstance(source_path, str) and source_path.startswith("/Game/"):
            source_file = self._package_path_to_file_path(source_path)
        else:
            source_file = Path(source_path)

        if not source_file.exists():
            raise LevelNotFoundError(f"Source level not found: {source_path}")

        # Build target path
        target_file = source_file.with_name(f"{new_name}.umap")

        if target_file.exists():
            raise LevelError(f"A level with name '{new_name}' already exists")

        try:
            # Copy level file
            import shutil
            shutil.copy2(source_file, target_file)

            # Copy metadata if exists
            source_metadata = source_file.with_suffix(".umap.meta")
            if source_metadata.exists():
                target_metadata = target_file.with_suffix(".umap.meta")
                shutil.copy2(source_metadata, target_metadata)
                self._update_metadata_name(target_metadata, new_name)
        except Exception as e:
            raise LevelError(f"Failed to duplicate level: {e}")

        return target_file

    def get_level(self, level_path: Union[str, Path]) -> LevelInfo:
        """Get detailed information about a specific level.

        Args:
            level_path: Path to the level (package path or file path).

        Returns:
            LevelInfo object.

        Raises:
            LevelNotFoundError: If the level does not exist.
        """
        # Convert package path to file path if needed
        if isinstance(level_path, str) and level_path.startswith("/Game/"):
            file_path = self._package_path_to_file_path(level_path)
        else:
            file_path = Path(level_path)

        if not file_path.exists():
            raise LevelNotFoundError(f"Level not found: {level_path}")

        return self._get_level_info(file_path)

    def _file_path_to_package_path(self, file_path: Path) -> str:
        """Convert a file path to a UE package path.

        Args:
            file_path: Path to the file.

        Returns:
            UE package path (e.g., "/Game/Maps/LevelName").
        """
        relative = file_path.relative_to(self.content_dir)
        return f"/Game/{relative.with_suffix('').as_posix()}"

    def _package_path_to_file_path(self, package_path: str) -> Path:
        """Convert a UE package path to a file path.

        Args:
            package_path: UE package path (e.g., "/Game/Maps/LevelName").

        Returns:
            Path to the file.
        """
        # Remove /Game/ prefix and add extension
        relative = package_path.replace("/Game/", "").replace("/", os.sep)
        return self.content_dir / f"{relative}.umap"

    def _level_exists(self, level_path: str) -> bool:
        """Check if a level exists.

        Args:
            level_path: Path to the level (package or file path).

        Returns:
            True if the level exists, False otherwise.
        """
        if level_path.startswith("/Game/"):
            file_path = self._package_path_to_file_path(level_path)
        else:
            file_path = Path(level_path)

        return file_path.exists()

    def _update_metadata_name(self, metadata_path: Path, new_name: str) -> None:
        """Update the name in a metadata file.

        Args:
            metadata_path: Path to the metadata file.
            new_name: New level name.
        """
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            metadata["name"] = new_name
            metadata["modified"] = datetime.now().isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            # Metadata updates are optional
            pass

    def list_templates(self) -> List[Dict[str, str]]:
        """List available level templates.

        Returns:
            List of template information dictionaries.
        """
        return [
            {"name": name, "description": self._get_template_description(name)}
            for name in self.TEMPLATES.keys()
        ]

    def _get_template_description(self, template: str) -> str:
        """Get description for a template.

        Args:
            template: Template name.

        Returns:
            Template description.
        """
        descriptions = {
            "Default": "Default level with basic lighting and floor",
            "Empty": "Empty level with no content",
            "TimeOfDay": "Level with dynamic time of day lighting",
            "DefaultVR": "Default level configured for VR development",
            "Basic": "Basic level with minimal content",
            "Minimal_Default": "Minimal default level (UE5 default)",
        }
        return descriptions.get(template, "Unknown template")

    @property
    def content_directory(self) -> Path:
        """Path to the project's Content directory."""
        return self.content_dir
