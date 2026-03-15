"""Unit tests for asset.py module.

Tests asset management, import, export, migration, and deletion functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from core.asset import (
    AssetManager,
    AssetInfo,
    AssetType,
    ImportOptions,
    AssetImportStatus,
    AssetManagerError,
    AssetImportError,
    AssetExportError,
    AssetMigrationError,
    AssetNotFoundError,
)


class TestAssetType:
    """Tests for AssetType enum."""

    def test_asset_type_values(self) -> None:
        """Test AssetType enum values."""
        assert AssetType.STATIC_MESH.value == "StaticMesh"
        assert AssetType.SKELETAL_MESH.value == "SkeletalMesh"
        assert AssetType.TEXTURE.value == "Texture"
        assert AssetType.MATERIAL.value == "Material"
        assert AssetType.BLUEPRINT.value == "Blueprint"


class TestImportOptions:
    """Tests for ImportOptions class."""

    def test_import_options_defaults(self) -> None:
        """Test ImportOptions with default values."""
        options = ImportOptions()
        
        assert options.replace_existing is False
        assert options.automated is True
        assert options.save is True
        assert options.suppress_dialogs is True
        assert options.import_materials is True
        assert options.import_textures is True
        assert options.import_skeleton is True
        assert options.import_animations is True
        assert options.import_physics is True
        assert options.import_lods is True
        assert options.import_vertex_colors is True
        assert options.import_vertex_normals is True
        assert options.import_tangents is True
        assert options.import_morph_targets is True
        assert options.import_cloth is True
        assert options.create_physics_asset is True
        assert options.import_as_skeletal is False
        assert options.import_rigid_mesh is False
        assert options.uniform_scale == 1.0
        assert options.convert_scene is False
        assert options.force_front_x_axis is False
        assert options.convert_scene_unit is False
        assert options.use_t0_ref_pose is False
        assert options.preserve_smoothing_groups is True
        assert options.keep_overlapping_vertices is False
        assert options.combine_meshes is False
        assert options.one_convex_hull_per_ucx is False
        assert options.auto_compute_lod_distances is True
        assert options.auto_generate_collision is True
        assert options.vertex_override_color is False
        assert options.remove_degenerates is True
        assert options.build_adjacency_buffer is False
        assert options.build_reversed_index_buffer is False
        assert options.use_full_precision_uvs is False
        assert options.generate_lightmap_uvs is True
        assert options.one_lightmap_uvs is False
        assert options.transform_vertex_to_absolute is False
        assert options.bake_animation is False
        assert options.import_custom_attribute is False
        assert options.import_attribute_data is False
        assert options.import_skin_weights is True
        assert options.import_vertex_speed is False
        assert options.import_vertex_animation is False

    def test_import_options_custom_values(self) -> None:
        """Test ImportOptions with custom values."""
        options = ImportOptions(
            replace_existing=True,
            automated=False,
            save=False,
            suppress_dialogs=False,
            import_materials=False,
            import_textures=False,
            uniform_scale=2.0,
            auto_generate_collision=False,
        )
        
        assert options.replace_existing is True
        assert options.automated is False
        assert options.save is False
        assert options.suppress_dialogs is False
        assert options.import_materials is False
        assert options.import_textures is False
        assert options.uniform_scale == 2.0
        assert options.auto_generate_collision is False


class TestAssetInfo:
    """Tests for AssetInfo class."""

    def test_asset_info_defaults(self) -> None:
        """Test AssetInfo with default values."""
        asset_info = AssetInfo(
            path="/Game/Test/Asset",
            name="Asset",
            type=AssetType.STATIC_MESH,
        )
        
        assert asset_info.path == "/Game/Test/Asset"
        assert asset_info.name == "Asset"
        assert asset_info.type == AssetType.STATIC_MESH
        assert asset_info.size_bytes == 0
        assert asset_info.last_modified == 0.0
        assert asset_info.references == []
        assert asset_info.dependencies == []
        assert asset_info.is_loaded is False
        assert asset_info.is_cooked is False
        assert asset_info.is_redirector is False

    def test_asset_info_custom_values(self) -> None:
        """Test AssetInfo with custom values."""
        asset_info = AssetInfo(
            path="/Game/Test/Mesh",
            name="Mesh",
            type=AssetType.SKELETAL_MESH,
            size_bytes=1024,
            last_modified=1234567890.0,
            references=["/Game/Test/Other"],
            dependencies=["/Game/Test/Base"],
            is_loaded=True,
            is_cooked=True,
            is_redirector=False,
        )
        
        assert asset_info.path == "/Game/Test/Mesh"
        assert asset_info.name == "Mesh"
        assert asset_info.type == AssetType.SKELETAL_MESH
        assert asset_info.size_bytes == 1024
        assert asset_info.last_modified == 1234567890.0
        assert asset_info.references == ["/Game/Test/Other"]
        assert asset_info.dependencies == ["/Game/Test/Base"]
        assert asset_info.is_loaded is True
        assert asset_info.is_cooked is True
        assert asset_info.is_redirector is False


class TestAssetManager:
    """Tests for AssetManager class."""

    @pytest.fixture
    def temp_project(self) -> Path:
        """Create a temporary UE5 project for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "TestProject"
            project_dir.mkdir(parents=True)
            
            # Create .uproject file
            uproject_file = project_dir / "TestProject.uproject"
            uproject_content = {
                "FileVersion": 3,
                "EngineAssociation": "5.3",
                "Category": "",
                "Description": "",
                "Modules": [
                    {
                        "Name": "TestProject",
                        "Type": "Runtime",
                        "LoadingPhase": "Default"
                    }
                ]
            }
            with open(uproject_file, "w") as f:
                json.dump(uproject_content, f)
            
            # Create Content directory
            content_dir = project_dir / "Content"
            content_dir.mkdir()
            
            yield uproject_file

    @pytest.fixture
    def asset_manager(self, temp_project: Path) -> AssetManager:
        """Create an AssetManager instance for testing."""
        return AssetManager(temp_project)

    def test_init_valid_project(self, temp_project: Path) -> None:
        """Test AssetManager initialization with valid project."""
        manager = AssetManager(temp_project)
        
        assert manager.project_path == temp_project
        assert manager.content_dir == temp_project.parent / "Content"
        assert manager.engine_path is None
        assert manager.content_dir.exists()

    def test_init_project_not_found(self) -> None:
        """Test AssetManager initialization with non-existent project."""
        with pytest.raises(FileNotFoundError):
            AssetManager(Path("/nonexistent/project.uproject"))

    def test_init_not_uproject_file(self, temp_project: Path) -> None:
        """Test AssetManager initialization with non-.uproject file."""
        not_uproject = temp_project.parent / "not_a_project.txt"
        not_uproject.touch()
        
        with pytest.raises(ValueError):
            AssetManager(not_uproject)

    def test_import_asset_success(self, asset_manager: AssetManager) -> None:
        """Test successful asset import."""
        with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as tmp:
            tmp.write(b"FBX content")
            source_path = Path(tmp.name)
        
        try:
            destination_path = "/Game/Test/Mesh"
            
            with patch.object(asset_manager, '_detect_asset_type', return_value=AssetType.STATIC_MESH):
                with patch('shutil.copy2') as mock_copy:
                    with patch('json.dump') as mock_json_dump:
                        result = asset_manager.import_asset(source_path, destination_path)
                        
                        assert result == destination_path
                        mock_copy.assert_called_once()
                        mock_json_dump.assert_called_once()
        finally:
            source_path.unlink(missing_ok=True)

    def test_import_asset_source_not_found(self, asset_manager: AssetManager) -> None:
        """Test asset import with non-existent source file."""
        source_path = Path("/nonexistent/file.fbx")
        
        with pytest.raises(FileNotFoundError):
            asset_manager.import_asset(source_path, "/Game/Test/Mesh")

    def test_import_asset_with_options(self, asset_manager: AssetManager) -> None:
        """Test asset import with custom options."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"PNG content")
            source_path = Path(tmp.name)
        
        try:
            options = ImportOptions(
                replace_existing=True,
                automated=False,
                uniform_scale=2.0,
            )
            
            with patch.object(asset_manager, '_detect_asset_type', return_value=AssetType.TEXTURE):
                with patch('shutil.copy2'):
                    with patch('json.dump'):
                        result = asset_manager.import_asset(
                            source_path,
                            "/Game/Test/Texture",
                            options
                        )
                        
                        assert result == "/Game/Test/Texture"
        finally:
            source_path.unlink(missing_ok=True)

    def test_export_asset_success(self, asset_manager: AssetManager) -> None:
        """Test successful asset export."""
        asset_path = "/Game/Test/Mesh"
        output_path = Path("/tmp/exported.fbx")
        
        # Mock the asset files
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        with patch('shutil.copy2') as mock_copy:
            result = asset_manager.export_asset(asset_path, output_path, "FBX")
            
            assert result == output_path
            mock_copy.assert_called_once()
        
        # Cleanup
        uasset_file.unlink(missing_ok=True)

    def test_export_asset_not_found(self, asset_manager: AssetManager) -> None:
        """Test asset export with non-existent asset."""
        with pytest.raises(AssetNotFoundError):
            asset_manager.export_asset("/Game/Nonexistent", Path("/tmp/output.fbx"))

    def test_list_assets_empty(self, asset_manager: AssetManager) -> None:
        """Test listing assets in empty directory."""
        assets = asset_manager.list_assets("/Game")
        
        assert assets == []

    def test_list_assets_with_files(self, asset_manager: AssetManager) -> None:
        """Test listing assets with existing files."""
        # Create test asset files
        asset_dir = asset_manager.content_dir / "Test"
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        uasset_file = asset_dir / "TestMesh.uasset"
        uasset_file.touch()
        
        meta_file = asset_dir / "TestMesh.uasset.meta"
        with open(meta_file, "w") as f:
            json.dump({
                "asset_type": "StaticMesh",
                "dependencies": ["/Game/Test/Base"]
            }, f)
        
        try:
            assets = asset_manager.list_assets("/Game/Test")
            
            assert len(assets) == 1
            asset = assets[0]
            assert asset.path == "/Game/Test/TestMesh"
            assert asset.name == "TestMesh"
            assert asset.type == AssetType.STATIC_MESH
            assert asset.dependencies == ["/Game/Test/Base"]
        finally:
            uasset_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)

    def test_list_assets_recursive(self, asset_manager: AssetManager) -> None:
        """Test recursive asset listing."""
        # Create nested asset files
        subdir = asset_manager.content_dir / "Test" / "Subdir"
        subdir.mkdir(parents=True, exist_ok=True)
        
        uasset1 = asset_manager.content_dir / "Test" / "Asset1.uasset"
        uasset1.touch()
        
        uasset2 = subdir / "Asset2.uasset"
        uasset2.touch()
        
        try:
            # Non-recursive
            assets_nonrecursive = asset_manager.list_assets("/Game/Test", recursive=False)
            assert len(assets_nonrecursive) == 1
            
            # Recursive
            assets_recursive = asset_manager.list_assets("/Game/Test", recursive=True)
            assert len(assets_recursive) == 2
        finally:
            uasset1.unlink(missing_ok=True)
            uasset2.unlink(missing_ok=True)

    def test_list_assets_filter_type(self, asset_manager: AssetManager) -> None:
        """Test listing assets with type filter."""
        # Create different type assets
        asset_dir = asset_manager.content_dir / "Test"
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        mesh_file = asset_dir / "Mesh.uasset"
        mesh_file.touch()
        
        texture_file = asset_dir / "Texture.uasset"
        texture_file.touch()
        
        # Create metadata files
        with open(asset_dir / "Mesh.uasset.meta", "w") as f:
            json.dump({"asset_type": "StaticMesh"}, f)
        
        with open(asset_dir / "Texture.uasset.meta", "w") as f:
            json.dump({"asset_type": "Texture"}, f)
        
        try:
            # Filter for StaticMesh
            mesh_assets = asset_manager.list_assets(
                "/Game/Test",
                filter_type=AssetType.STATIC_MESH
            )
            assert len(mesh_assets) == 1
            assert mesh_assets[0].type == AssetType.STATIC_MESH
            
            # Filter for Texture
            texture_assets = asset_manager.list_assets(
                "/Game/Test",
                filter_type=AssetType.TEXTURE
            )
            assert len(texture_assets) == 1
            assert texture_assets[0].type == AssetType.TEXTURE
        finally:
            mesh_file.unlink(missing_ok=True)
            texture_file.unlink(missing_ok=True)
            (asset_dir / "Mesh.uasset.meta").unlink(missing_ok=True)
            (asset_dir / "Texture.uasset.meta").unlink(missing_ok=True)

    def test_find_references(self, asset_manager: AssetManager) -> None:
        """Test finding asset references."""
        asset_path = "/Game/Test/Mesh"
        
        # Mock the asset
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        # Mock list_assets to return assets with dependencies
        mock_assets = [
            AssetInfo(
                path="/Game/Test/Asset1",
                name="Asset1",
                type=AssetType.MATERIAL,
                dependencies=[asset_path]
            ),
            AssetInfo(
                path="/Game/Test/Asset2",
                name="Asset2",
                type=AssetType.BLUEPRINT,
                dependencies=[]
            ),
        ]
        
        with patch.object(asset_manager, 'list_assets', return_value=mock_assets):
            references = asset_manager.find_references(asset_path)
            
            assert references == ["/Game/Test/Asset1"]
        
        uasset_file.unlink(missing_ok=True)

    def test_find_references_asset_not_found(self, asset_manager: AssetManager) -> None:
        """Test finding references for non-existent asset."""
        with pytest.raises(AssetNotFoundError):
            asset_manager.find_references("/Game/Nonexistent")

    def test_delete_asset_success(self, asset_manager: AssetManager) -> None:
        """Test successful asset deletion."""
        asset_path = "/Game/Test/Mesh"
        
        # Create asset files
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        meta_file = fs_path.with_suffix(".uasset.meta")
        meta_file.touch()
        
        # Mock find_references to return empty list
        with patch.object(asset_manager, 'find_references', return_value=[]):
            result = asset_manager.delete_asset(asset_path)
            
            assert result is True
            assert not uasset_file.exists()
            assert not meta_file.exists()

    def test_delete_asset_with_references(self, asset_manager: AssetManager) -> None:
        """Test asset deletion when asset has references."""
        asset_path = "/Game/Test/Mesh"
        
        # Create asset file
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        # Mock find_references to return references
        with patch.object(asset_manager, 'find_references', return_value=["/Game/Test/Other"]):
            with pytest.raises(AssetManagerError):
                asset_manager.delete_asset(asset_path)
            
            # Asset should still exist
            assert uasset_file.exists()
        
        # Cleanup
        uasset_file.unlink(missing_ok=True)

    def test_delete_asset_force(self, asset_manager: AssetManager) -> None:
        """Test forced asset deletion with references."""
        asset_path = "/Game/Test/Mesh"
        
        # Create asset files
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        meta_file = fs_path.with_suffix(".uasset.meta")
        meta_file.touch()
        
        # Mock find_references to return references
        with patch.object(asset_manager, 'find_references', return_value=["/Game/Test/Other"]):
            result = asset_manager.delete_asset(asset_path, force=True)
            
            assert result is True
            assert not uasset_file.exists()
            assert not meta_file.exists()

    def test_delete_asset_not_found(self, asset_manager: AssetManager) -> None:
        """Test deleting non-existent asset."""
        with pytest.raises(AssetNotFoundError):
            asset_manager.delete_asset("/Game/Nonexistent")

    def test_migrate_assets_success(self, asset_manager: AssetManager) -> None:
        """Test successful asset migration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target project
            target_project_dir = Path(temp_dir) / "TargetProject"
            target_project_dir.mkdir()
            
            target_uproject = target_project_dir / "TargetProject.uproject"
            with open(target_uproject, "w") as f:
                json.dump({
                    "FileVersion": 3,
                    "EngineAssociation": "5.3"
                }, f)
            
            # Create source asset
            asset_path = "/Game/Test/Mesh"
            fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
            fs_path.parent.mkdir(parents=True, exist_ok=True)
            uasset_file = fs_path.with_suffix(".uasset")
            uasset_file.touch()
            
            # Mock import_asset on target manager
            with patch('core.asset.AssetManager') as MockAssetManager:
                mock_target_manager = MagicMock()
                mock_target_manager.import_asset.return_value = asset_path
                MockAssetManager.return_value = mock_target_manager
                
                results = asset_manager.migrate_assets(
                    [asset_path],
                    target_uproject
                )
                
                assert results == {asset_path: AssetImportStatus.SUCCESS}
                mock_target_manager.import_asset.assert_called_once()
            
            # Cleanup
            uasset_file.unlink(missing_ok=True)

    def test_migrate_assets_partial_failure(self, asset_manager: AssetManager) -> None:
        """Test asset migration with partial failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target project
            target_project_dir = Path(temp_dir) / "TargetProject"
            target_project_dir.mkdir()
            
            target_uproject = target_project_dir / "TargetProject.uproject"
            with open(target_uproject, "w") as f:
                json.dump({
                    "FileVersion": 3,
                    "EngineAssociation": "5.3"
                }, f)
            
            # Create one existing asset and one non-existent
            existing_path = "/Game/Test/Existing"
            fs_path = asset_manager._convert_asset_path_to_fs(existing_path)
            fs_path.parent.mkdir(parents=True, exist_ok=True)
            uasset_file = fs_path.with_suffix(".uasset")
            uasset_file.touch()
            
            non_existent_path = "/Game/Test/Nonexistent"
            
            # Mock import_asset on target manager
            with patch('core.asset.AssetManager') as MockAssetManager:
                mock_target_manager = MagicMock()
                mock_target_manager.import_asset.return_value = existing_path
                MockAssetManager.return_value = mock_target_manager
                
                results = asset_manager.migrate_assets(
                    [existing_path, non_existent_path],
                    target_uproject
                )
                
                assert results[existing_path] == AssetImportStatus.SUCCESS
                assert results[non_existent_path] == AssetImportStatus.FAILED
                mock_target_manager.import_asset.assert_called_once()
            
            # Cleanup
            uasset_file.unlink(missing_ok=True)

    def test_migrate_assets_target_not_found(self, asset_manager: AssetManager) -> None:
        """Test migration to non-existent target project."""
        with pytest.raises(FileNotFoundError):
            asset_manager.migrate_assets(
                ["/Game/Test/Mesh"],
                Path("/nonexistent/project.uproject")
            )

    def test_migrate_assets_target_not_uproject(self, asset_manager: AssetManager) -> None:
        """Test migration to non-.uproject file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            target_file = Path(tmp.name)
        
        try:
            with pytest.raises(ValueError):
                asset_manager.migrate_assets(
                    ["/Game/Test/Mesh"],
                    target_file
                )
        finally:
            target_file.unlink(missing_ok=True)

    def test_convert_asset_path_to_fs(self, asset_manager: AssetManager) -> None:
        """Test asset path to filesystem path conversion."""
        fs_path = asset_manager._convert_asset_path_to_fs("/Game/Test/Mesh")
        
        expected_path = asset_manager.content_dir / "Test" / "Mesh"
        assert fs_path == expected_path

    def test_convert_asset_path_to_fs_invalid(self, asset_manager: AssetManager) -> None:
        """Test invalid asset path conversion."""
        with pytest.raises(ValueError):
            asset_manager._convert_asset_path_to_fs("Invalid/Path")

    def test_detect_asset_type(self, asset_manager: AssetManager) -> None:
        """Test asset type detection from file extension."""
        test_cases = [
            (".fbx", AssetType.STATIC_MESH),
            (".png", AssetType.TEXTURE),
            (".wav", AssetType.SOUND),
            (".uasset", AssetType.OTHER),
            (".unknown", AssetType.OTHER),
        ]
        
        for extension, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
                file_path = Path(tmp.name)
            
            try:
                detected_type = asset_manager._detect_asset_type(file_path)
                assert detected_type == expected_type
            finally:
                file_path.unlink(missing_ok=True)

    def test_options_to_dict(self, asset_manager: AssetManager) -> None:
        """Test ImportOptions to dictionary conversion."""
        options = ImportOptions(
            replace_existing=True,
            automated=False,
            uniform_scale=2.0,
        )
        
        options_dict = asset_manager._options_to_dict(options)
        
        assert options_dict["replace_existing"] is True
        assert options_dict["automated"] is False
        assert options_dict["uniform_scale"] == 2.0
        assert "import_materials" in options_dict  # Default value

    def test_get_asset_info(self, asset_manager: AssetManager) -> None:
        """Test getting asset information."""
        # Create asset with metadata
        asset_path = "/Game/Test/Mesh"
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        meta_file = fs_path.with_suffix(".uasset.meta")
        with open(meta_file, "w") as f:
            json.dump({
                "asset_type": "StaticMesh",
                "dependencies": ["/Game/Test/Base"]
            }, f)
        
        try:
            asset_info = asset_manager._get_asset_info(asset_path, uasset_file)
            
            assert asset_info.path == asset_path
            assert asset_info.name == "Mesh"
            assert asset_info.type == AssetType.STATIC_MESH
            assert asset_info.dependencies == ["/Game/Test/Base"]
            # File size might be 0 for empty file, that's okay
            assert asset_info.size_bytes >= 0
            assert asset_info.last_modified > 0
        finally:
            uasset_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)

    def test_get_asset_info_no_metadata(self, asset_manager: AssetManager) -> None:
        """Test getting asset information without metadata."""
        # Create asset without metadata
        asset_path = "/Game/Test/Material"
        fs_path = asset_manager._convert_asset_path_to_fs(asset_path)
        fs_path.parent.mkdir(parents=True, exist_ok=True)
        
        uasset_file = fs_path.with_suffix(".uasset")
        uasset_file.touch()
        
        try:
            asset_info = asset_manager._get_asset_info(asset_path, uasset_file)
            
            assert asset_info.path == asset_path
            assert asset_info.name == "Material"
            # When no metadata, type should be detected from name
            # "Material" in the name suggests it's a material
            assert asset_info.type == AssetType.MATERIAL
            assert asset_info.dependencies == []
        finally:
            uasset_file.unlink(missing_ok=True)

    def test_cleanup_empty_directories(self, asset_manager: AssetManager) -> None:
        """Test cleanup of empty directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "Test" / "Nested"
            test_dir.mkdir(parents=True)
            
            # Directory should be removed when empty
            asset_manager._cleanup_empty_directories(test_dir.parent)
            
            assert not test_dir.exists()
            assert not test_dir.parent.exists()
            
            # Directory with file should not be removed
            test_dir2 = Path(temp_dir) / "Test2" / "Nested2"
            test_dir2.mkdir(parents=True)
            (test_dir2 / "file.txt").touch()
            
            asset_manager._cleanup_empty_directories(test_dir2.parent)
            
            assert test_dir2.exists()
            assert test_dir2.parent.exists()

    def test_asset_manager_error_hierarchy(self) -> None:
        """Test asset manager exception hierarchy."""
        # Test that specific exceptions inherit from base exception
        assert issubclass(AssetImportError, AssetManagerError)
        assert issubclass(AssetExportError, AssetManagerError)
        assert issubclass(AssetMigrationError, AssetManagerError)
        assert issubclass(AssetNotFoundError, AssetManagerError)
        
        # Test exception instantiation
        base_msg = "Base error"
        specific_msg = "Specific error"
        
        base_exception = AssetManagerError(base_msg)
        assert str(base_exception) == base_msg
        
        import_exception = AssetImportError(specific_msg)
        assert str(import_exception) == specific_msg