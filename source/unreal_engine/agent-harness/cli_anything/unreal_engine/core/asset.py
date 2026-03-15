"""Unreal Engine CLI - Asset management module.

Provides asset import, export, migration, listing, reference finding,
and deletion functionality for UE5 projects.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class AssetType(Enum):
    """UE5 asset types."""
    STATIC_MESH = "StaticMesh"
    SKELETAL_MESH = "SkeletalMesh"
    TEXTURE = "Texture"
    MATERIAL = "Material"
    MATERIAL_INSTANCE = "MaterialInstance"
    BLUEPRINT = "Blueprint"
    SOUND = "Sound"
    ANIMATION = "Animation"
    ANIMATION_BLUEPRINT = "AnimationBlueprint"
    PHYSICS_ASSET = "PhysicsAsset"
    SKELETON = "Skeleton"
    LEVEL = "Level"
    WIDGET_BLUEPRINT = "WidgetBlueprint"
    DATA_ASSET = "DataAsset"
    DATA_TABLE = "DataTable"
    CURVE = "Curve"
    CURVE_TABLE = "CurveTable"
    STRUCT = "Struct"
    ENUM = "Enum"
    INTERFACE = "Interface"
    FUNCTION = "Function"
    MACRO = "Macro"
    OTHER = "Other"


class AssetImportStatus(Enum):
    """Asset import status."""
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    PARTIAL = auto()


@dataclass
class AssetInfo:
    """Information about a UE5 asset.

    Attributes:
        path: Asset path in /Game/... format.
        name: Asset name.
        type: Asset type.
        size_bytes: File size in bytes.
        last_modified: Last modification timestamp.
        references: List of assets that reference this asset.
        dependencies: List of assets this asset depends on.
        is_loaded: Whether the asset is currently loaded in memory.
        is_cooked: Whether the asset has been cooked.
        is_redirector: Whether this is a redirector asset.
    """
    path: str
    name: str
    type: AssetType
    size_bytes: int = 0
    last_modified: float = 0.0
    references: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_loaded: bool = False
    is_cooked: bool = False
    is_redirector: bool = False


@dataclass
class ImportOptions:
    """Options for asset import.

    Attributes:
        replace_existing: Replace existing assets.
        automated: Run import in automated mode.
        save: Save package after import.
        suppress_dialogs: Suppress all import dialogs.
        import_materials: Import materials for meshes.
        import_textures: Import textures for meshes.
        import_skeleton: Import skeleton for skeletal meshes.
        import_animations: Import animations for skeletal meshes.
        import_physics: Import physics for meshes.
        import_lods: Import LODs for meshes.
        import_vertex_colors: Import vertex colors.
        import_vertex_normals: Import vertex normals.
        import_tangents: Import tangents.
        import_morph_targets: Import morph targets.
        import_cloth: Import cloth data.
        create_physics_asset: Create physics asset for meshes.
        import_as_skeletal: Import as skeletal mesh.
        import_rigid_mesh: Import as rigid mesh.
        uniform_scale: Uniform scale factor.
        convert_scene: Convert scene units.
        force_front_x_axis: Force front X axis.
        convert_scene_unit: Convert scene unit.
        use_t0_ref_pose: Use T0 as reference pose.
        preserve_smoothing_groups: Preserve smoothing groups.
        keep_overlapping_vertices: Keep overlapping vertices.
        combine_meshes: Combine meshes.
        one_convex_hull_per_ucx: One convex hull per UCX.
        auto_compute_lod_distances: Auto compute LOD distances.
        auto_generate_collision: Auto generate collision.
        vertex_override_color: Vertex override color.
        remove_degenerates: Remove degenerate triangles.
        build_adjacency_buffer: Build adjacency buffer.
        build_reversed_index_buffer: Build reversed index buffer.
        use_full_precision_uvs: Use full precision UVs.
        generate_lightmap_uvs: Generate lightmap UVs.
        one_lightmap_uvs: One lightmap UVs.
        transform_vertex_to_absolute: Transform vertex to absolute.
        bake_animation: Bake animation.
        import_custom_attribute: Import custom attribute.
        import_morph_targets: Import morph targets.
        import_attribute_data: Import attribute data.
        import_skin_weights: Import skin weights.
        import_vertex_speed: Import vertex speed.
        import_vertex_animation: Import vertex animation.
    """
    replace_existing: bool = False
    automated: bool = True
    save: bool = True
    suppress_dialogs: bool = True
    import_materials: bool = True
    import_textures: bool = True
    import_skeleton: bool = True
    import_animations: bool = True
    import_physics: bool = True
    import_lods: bool = True
    import_vertex_colors: bool = True
    import_vertex_normals: bool = True
    import_tangents: bool = True
    import_morph_targets: bool = True
    import_cloth: bool = True
    create_physics_asset: bool = True
    import_as_skeletal: bool = False
    import_rigid_mesh: bool = False
    uniform_scale: float = 1.0
    convert_scene: bool = False
    force_front_x_axis: bool = False
    convert_scene_unit: bool = False
    use_t0_ref_pose: bool = False
    preserve_smoothing_groups: bool = True
    keep_overlapping_vertices: bool = False
    combine_meshes: bool = False
    one_convex_hull_per_ucx: bool = False
    auto_compute_lod_distances: bool = True
    auto_generate_collision: bool = True
    vertex_override_color: bool = False
    remove_degenerates: bool = True
    build_adjacency_buffer: bool = False
    build_reversed_index_buffer: bool = False
    use_full_precision_uvs: bool = False
    generate_lightmap_uvs: bool = True
    one_lightmap_uvs: bool = False
    transform_vertex_to_absolute: bool = False
    bake_animation: bool = False
    import_custom_attribute: bool = False
    import_attribute_data: bool = False
    import_skin_weights: bool = True
    import_vertex_speed: bool = False
    import_vertex_animation: bool = False


class AssetManagerError(Exception):
    """Base exception for AssetManager errors."""
    pass


class AssetImportError(AssetManagerError):
    """Exception raised when asset import fails."""
    pass


class AssetExportError(AssetManagerError):
    """Exception raised when asset export fails."""
    pass


class AssetMigrationError(AssetManagerError):
    """Exception raised when asset migration fails."""
    pass


class AssetNotFoundError(AssetManagerError):
    """Exception raised when asset is not found."""
    pass


class AssetManager:
    """UE5 asset manager.

    Provides asset import, export, migration, listing, reference finding,
    and deletion functionality.

    Attributes:
        project_path: Path to the UE5 project (.uproject file).
        content_dir: Path to the project's Content directory.
        engine_path: Path to the UE5 engine installation.
    """

    def __init__(self, project_path: Path, engine_path: Optional[Path] = None):
        """Initialize the asset manager.

        Args:
            project_path: Path to the UE5 project (.uproject file).
            engine_path: Path to the UE5 engine installation. If None,
                will attempt to auto-detect.

        Raises:
            FileNotFoundError: If project_path does not exist.
            ValueError: If project_path is not a .uproject file.
        """
        if not project_path.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")
        if project_path.suffix != ".uproject":
            raise ValueError(f"Not a .uproject file: {project_path}")

        self.project_path = project_path
        self.content_dir = project_path.parent / "Content"
        self.engine_path = engine_path

        # Ensure content directory exists
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def import_asset(
        self,
        source_path: Path,
        destination_path: str,
        options: Optional[ImportOptions] = None
    ) -> str:
        """Import an asset into the project.

        Args:
            source_path: Path to the source file to import.
            destination_path: Destination path in /Game/... format.
            options: Import options. If None, default options are used.

        Returns:
            The imported asset path.

        Raises:
            AssetImportError: If import fails.
            FileNotFoundError: If source_path does not exist.
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if options is None:
            options = ImportOptions()

        # Normalize destination path
        if not destination_path.startswith("/Game/"):
            destination_path = f"/Game/{destination_path.lstrip('/')}"

        # Remove file extension from destination path
        if destination_path.endswith(".uasset"):
            destination_path = destination_path[:-7]

        # Create destination directory in filesystem
        fs_dest_dir = self._convert_asset_path_to_fs(destination_path).parent
        fs_dest_dir.mkdir(parents=True, exist_ok=True)

        # Determine asset type based on file extension
        asset_type = self._detect_asset_type(source_path)

        try:
            # For now, simulate import by copying the file
            # In a real implementation, this would call UE5's import tools
            dest_file = self._convert_asset_path_to_fs(destination_path)
            
            # Copy the file
            shutil.copy2(source_path, dest_file.with_suffix(".uasset"))
            
            # Create metadata file
            metadata = {
                "asset_type": asset_type.value,
                "source_path": str(source_path),
                "import_options": self._options_to_dict(options),
                "import_time": str(datetime.now())
            }
            
            metadata_file = dest_file.with_suffix(".uasset.meta")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return destination_path

        except Exception as e:
            raise AssetImportError(f"Failed to import asset: {e}") from e

    def export_asset(
        self,
        asset_path: str,
        output_path: Path,
        format: str = "FBX"
    ) -> Path:
        """Export an asset from the project.

        Args:
            asset_path: Asset path in /Game/... format.
            output_path: Output directory or file path.
            format: Export format (FBX, OBJ, etc.).

        Returns:
            Path to the exported file.

        Raises:
            AssetExportError: If export fails.
            AssetNotFoundError: If asset is not found.
        """
        # Normalize asset path
        if not asset_path.startswith("/Game/"):
            asset_path = f"/Game/{asset_path.lstrip('/')}"

        # Check if asset exists
        fs_path = self._convert_asset_path_to_fs(asset_path)
        if not fs_path.with_suffix(".uasset").exists():
            raise AssetNotFoundError(f"Asset not found: {asset_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # For now, simulate export by copying the file
            # In a real implementation, this would call UE5's export tools
            if output_path.is_dir():
                output_file = output_path / f"{fs_path.stem}.{format.lower()}"
            else:
                output_file = output_path

            # Copy the asset file (simulated export)
            source_file = fs_path.with_suffix(".uasset")
            if source_file.exists():
                shutil.copy2(source_file, output_file)

            return output_file

        except Exception as e:
            raise AssetExportError(f"Failed to export asset: {e}") from e

    def migrate_assets(
        self,
        asset_paths: List[str],
        target_project: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, AssetImportStatus]:
        """Migrate assets to another project.

        Args:
            asset_paths: List of asset paths to migrate.
            target_project: Path to target project (.uproject file).
            options: Migration options.

        Returns:
            Dictionary mapping asset paths to migration status.

        Raises:
            AssetMigrationError: If migration fails.
            FileNotFoundError: If target_project does not exist.
        """
        if not target_project.exists():
            raise FileNotFoundError(f"Target project not found: {target_project}")
        if target_project.suffix != ".uproject":
            raise ValueError(f"Not a .uproject file: {target_project}")

        if options is None:
            options = {}

        results: Dict[str, AssetImportStatus] = {}

        try:
            # Create target asset manager
            target_manager = AssetManager(target_project)

            for asset_path in asset_paths:
                try:
                    # Normalize asset path
                    if not asset_path.startswith("/Game/"):
                        normalized_path = f"/Game/{asset_path.lstrip('/')}"
                    else:
                        normalized_path = asset_path

                    # Get source file path
                    source_fs_path = self._convert_asset_path_to_fs(normalized_path)
                    source_file = source_fs_path.with_suffix(".uasset")

                    if not source_file.exists():
                        results[asset_path] = AssetImportStatus.FAILED
                        continue

                    # Import into target project
                    target_path = normalized_path  # Keep same path
                    target_manager.import_asset(
                        source_file,
                        target_path,
                        ImportOptions()
                    )

                    results[asset_path] = AssetImportStatus.SUCCESS

                except Exception as e:
                    results[asset_path] = AssetImportStatus.FAILED
                    # Log error but continue with other assets

            return results

        except Exception as e:
            raise AssetMigrationError(f"Migration failed: {e}") from e

    def list_assets(
        self,
        path: str = "/Game",
        recursive: bool = True,
        filter_type: Optional[AssetType] = None
    ) -> List[AssetInfo]:
        """List assets in the specified path.

        Args:
            path: Asset path to list (e.g., "/Game", "/Game/Meshes").
            recursive: Whether to list recursively.
            filter_type: Filter by asset type.

        Returns:
            List of AssetInfo objects.

        Raises:
            AssetManagerError: If listing fails.
        """
        # Normalize path
        if not path.startswith("/Game/"):
            if path == "/Game":
                fs_path = self.content_dir
            else:
                path = f"/Game/{path.lstrip('/')}"
                fs_path = self._convert_asset_path_to_fs(path)
        else:
            fs_path = self._convert_asset_path_to_fs(path)

        if not fs_path.exists():
            return []

        assets: List[AssetInfo] = []

        try:
            if recursive:
                pattern = "**/*.uasset"
            else:
                pattern = "*.uasset"

            for uasset_file in fs_path.glob(pattern):
                # Skip metadata files
                if uasset_file.name.endswith(".meta"):
                    continue

                # Get asset path relative to content directory
                rel_path = uasset_file.relative_to(self.content_dir)
                asset_path = f"/Game/{rel_path.with_suffix('').as_posix()}"

                # Get asset info
                asset_info = self._get_asset_info(asset_path, uasset_file)
                
                # Apply filter
                if filter_type is None or asset_info.type == filter_type:
                    assets.append(asset_info)

            return sorted(assets, key=lambda x: x.path)

        except Exception as e:
            raise AssetManagerError(f"Failed to list assets: {e}") from e

    def find_references(self, asset_path: str) -> List[str]:
        """Find all assets that reference the specified asset.

        Args:
            asset_path: Asset path in /Game/... format.

        Returns:
            List of asset paths that reference the specified asset.

        Raises:
            AssetNotFoundError: If asset is not found.
            AssetManagerError: If reference search fails.
        """
        # Normalize asset path
        if not asset_path.startswith("/Game/"):
            asset_path = f"/Game/{asset_path.lstrip('/')}"

        # Check if asset exists
        fs_path = self._convert_asset_path_to_fs(asset_path)
        if not fs_path.with_suffix(".uasset").exists():
            raise AssetNotFoundError(f"Asset not found: {asset_path}")

        references: List[str] = []

        try:
            # For now, simulate reference finding
            # In a real implementation, this would parse asset metadata
            # or use UE5's reference finding tools
            
            # Get all assets
            all_assets = self.list_assets("/Game", recursive=True)
            
            for asset in all_assets:
                # Simulate reference checking
                # In reality, this would check asset dependencies
                if asset_path in asset.dependencies:
                    references.append(asset.path)

            return references

        except Exception as e:
            raise AssetManagerError(f"Failed to find references: {e}") from e

    def delete_asset(self, asset_path: str, force: bool = False) -> bool:
        """Delete an asset from the project.

        Args:
            asset_path: Asset path in /Game/... format.
            force: Force deletion even if asset has references.

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            AssetNotFoundError: If asset is not found.
            AssetManagerError: If deletion fails due to references and not forced.
        """
        # Normalize asset path
        if not asset_path.startswith("/Game/"):
            asset_path = f"/Game/{asset_path.lstrip('/')}"

        # Check if asset exists
        fs_path = self._convert_asset_path_to_fs(asset_path)
        uasset_file = fs_path.with_suffix(".uasset")
        meta_file = fs_path.with_suffix(".uasset.meta")

        if not uasset_file.exists():
            raise AssetNotFoundError(f"Asset not found: {asset_path}")

        try:
            # Check for references if not forced
            if not force:
                references = self.find_references(asset_path)
                if references:
                    raise AssetManagerError(
                        f"Cannot delete {asset_path}: "
                        f"referenced by {len(references)} assets. "
                        f"Use force=True to delete anyway."
                    )

            # Delete asset files
            uasset_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)

            # Also delete any related files
            for ext in [".uexp", ".ubulk", ".uptnl"]:
                related_file = fs_path.with_suffix(ext)
                related_file.unlink(missing_ok=True)

            # Remove empty directories
            self._cleanup_empty_directories(fs_path.parent)

            return True

        except AssetManagerError:
            raise
        except Exception as e:
            raise AssetManagerError(f"Failed to delete asset: {e}") from e

    # Helper methods

    def _convert_asset_path_to_fs(self, asset_path: str) -> Path:
        """Convert asset path (/Game/...) to filesystem path.

        Args:
            asset_path: Asset path in /Game/... format.

        Returns:
            Filesystem path.
        """
        if not asset_path.startswith("/Game/"):
            raise ValueError(f"Invalid asset path: {asset_path}")

        # Remove /Game/ prefix
        rel_path = asset_path[6:]  # Remove "/Game/"
        
        # Convert to filesystem path
        fs_path = self.content_dir / rel_path.replace("/", "\\")
        
        return fs_path

    def _detect_asset_type(self, file_path: Path) -> AssetType:
        """Detect asset type from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            AssetType enum value.
        """
        extension = file_path.suffix.lower()

        type_map = {
            ".fbx": AssetType.STATIC_MESH,
            ".obj": AssetType.STATIC_MESH,
            ".dae": AssetType.STATIC_MESH,
            ".abc": AssetType.STATIC_MESH,
            ".blend": AssetType.STATIC_MESH,
            ".ma": AssetType.STATIC_MESH,
            ".mb": AssetType.STATIC_MESH,
            ".max": AssetType.STATIC_MESH,
            ".png": AssetType.TEXTURE,
            ".jpg": AssetType.TEXTURE,
            ".jpeg": AssetType.TEXTURE,
            ".tga": AssetType.TEXTURE,
            ".bmp": AssetType.TEXTURE,
            ".exr": AssetType.TEXTURE,
            ".hdr": AssetType.TEXTURE,
            ".dds": AssetType.TEXTURE,
            ".ktx": AssetType.TEXTURE,
            ".wav": AssetType.SOUND,
            ".mp3": AssetType.SOUND,
            ".ogg": AssetType.SOUND,
            ".flac": AssetType.SOUND,
            ".uasset": AssetType.OTHER,
            ".umap": AssetType.LEVEL,
        }

        return type_map.get(extension, AssetType.OTHER)

    def _options_to_dict(self, options: ImportOptions) -> Dict[str, Any]:
        """Convert ImportOptions to dictionary.

        Args:
            options: ImportOptions instance.

        Returns:
            Dictionary representation.
        """
        return {
            k: v for k, v in options.__dict__.items()
            if not k.startswith("_")
        }

    def _get_asset_info(self, asset_path: str, uasset_file: Path) -> AssetInfo:
        """Get AssetInfo for a uasset file.

        Args:
            asset_path: Asset path in /Game/... format.
            uasset_file: Path to the .uasset file.

        Returns:
            AssetInfo object.
        """
        # Get basic file info
        stat = uasset_file.stat()
        
        # Try to read metadata
        metadata = {}
        meta_file = uasset_file.with_suffix(".uasset.meta")
        if meta_file.exists():
            try:
                with open(meta_file, "r") as f:
                    metadata = json.load(f)
            except:
                pass

        # Determine asset type from metadata or file name
        asset_type = AssetType.OTHER
        if "asset_type" in metadata:
            try:
                asset_type = AssetType(metadata["asset_type"])
            except:
                pass
        else:
            # Guess from file name
            if "Material" in uasset_file.stem:
                asset_type = AssetType.MATERIAL
            elif "Blueprint" in uasset_file.stem:
                asset_type = AssetType.BLUEPRINT
            elif "Texture" in uasset_file.stem:
                asset_type = AssetType.TEXTURE

        # Get dependencies (simulated)
        dependencies = []
        if "dependencies" in metadata:
            dependencies = metadata.get("dependencies", [])

        return AssetInfo(
            path=asset_path,
            name=uasset_file.stem,
            type=asset_type,
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
            dependencies=dependencies,
            is_loaded=False,  # Would require editor connection
            is_cooked=False,  # Would require checking cooked content
            is_redirector="Redirector" in uasset_file.stem
        )

    def _cleanup_empty_directories(self, directory: Path) -> None:
        """Recursively remove empty directories.

        Args:
            directory: Directory to clean up.
        """
        try:
            # Check if directory is empty
            if directory.exists() and directory.is_dir():
                # Check if directory has any files (excluding .gitignore, etc.)
                has_files = False
                for item in directory.iterdir():
                    if item.is_file() and not item.name.startswith("."):
                        has_files = True
                        break
                    elif item.is_dir():
                        # Recursively clean subdirectories
                        self._cleanup_empty_directories(item)
                        # Check again if subdirectory was removed
                        if item.exists():
                            has_files = True

                # Remove directory if empty
                if not has_files and directory != self.content_dir:
                    try:
                        directory.rmdir()
                    except:
                        pass  # Directory not empty or permission error

        except Exception:
            pass  # Silently ignore cleanup errors