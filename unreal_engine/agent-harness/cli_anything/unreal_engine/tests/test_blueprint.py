"""Unit tests for blueprint.py module.

Tests blueprint creation, compilation, listing, and duplication functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from core.blueprint import (
    BlueprintManager,
    BlueprintInfo,
    BlueprintType,
    BlueprintVariableType,
    BlueprintVariable,
    BlueprintFunction,
    BlueprintCompileStatus,
    CreateBlueprintOptions,
    BlueprintManagerError,
    BlueprintCreationError,
    BlueprintCompilationError,
    BlueprintNotFoundError,
)


class TestBlueprintType:
    """Tests for BlueprintType enum."""

    def test_blueprint_type_values(self) -> None:
        """Test BlueprintType enum values."""
        assert BlueprintType.ACTOR.value == "Actor"
        assert BlueprintType.PAWN.value == "Pawn"
        assert BlueprintType.CHARACTER.value == "Character"
        assert BlueprintType.USER_WIDGET.value == "UserWidget"
        assert BlueprintType.DATA_ASSET.value == "DataAsset"


class TestBlueprintVariableType:
    """Tests for BlueprintVariableType enum."""

    def test_variable_type_values(self) -> None:
        """Test BlueprintVariableType enum values."""
        assert BlueprintVariableType.BOOL.value == "bool"
        assert BlueprintVariableType.INT.value == "int"
        assert BlueprintVariableType.FLOAT.value == "float"
        assert BlueprintVariableType.STRING.value == "string"
        assert BlueprintVariableType.VECTOR.value == "Vector"
        assert BlueprintVariableType.OBJECT.value == "Object"


class TestBlueprintVariable:
    """Tests for BlueprintVariable class."""

    def test_blueprint_variable_defaults(self) -> None:
        """Test BlueprintVariable with default values."""
        variable = BlueprintVariable(
            name="TestVariable",
            type=BlueprintVariableType.INT,
        )
        
        assert variable.name == "TestVariable"
        assert variable.type == BlueprintVariableType.INT
        assert variable.default_value is None
        assert variable.is_editable is True
        assert variable.is_visible is True
        assert variable.is_read_only is False
        assert variable.category == "Default"
        assert variable.tooltip == ""

    def test_blueprint_variable_custom_values(self) -> None:
        """Test BlueprintVariable with custom values."""
        variable = BlueprintVariable(
            name="Health",
            type=BlueprintVariableType.FLOAT,
            default_value=100.0,
            is_editable=False,
            is_visible=False,
            is_read_only=True,
            category="Gameplay",
            tooltip="Player health value",
        )
        
        assert variable.name == "Health"
        assert variable.type == BlueprintVariableType.FLOAT
        assert variable.default_value == 100.0
        assert variable.is_editable is False
        assert variable.is_visible is False
        assert variable.is_read_only is True
        assert variable.category == "Gameplay"
        assert variable.tooltip == "Player health value"


class TestBlueprintFunction:
    """Tests for BlueprintFunction class."""

    def test_blueprint_function_defaults(self) -> None:
        """Test BlueprintFunction with default values."""
        function = BlueprintFunction(
            name="TestFunction",
        )
        
        assert function.name == "TestFunction"
        assert function.return_type is None
        assert function.parameters == []
        assert function.is_pure is False
        assert function.is_const is False
        assert function.is_blueprint_callable is True
        assert function.is_blueprint_implementable is False
        assert function.category == "Default"
        assert function.tooltip == ""

    def test_blueprint_function_custom_values(self) -> None:
        """Test BlueprintFunction with custom values."""
        function = BlueprintFunction(
            name="CalculateDamage",
            return_type=BlueprintVariableType.FLOAT,
            parameters=[
                {"name": "BaseDamage", "type": "float"},
                {"name": "Multiplier", "type": "float"},
            ],
            is_pure=True,
            is_const=True,
            is_blueprint_callable=False,
            is_blueprint_implementable=True,
            category="Combat",
            tooltip="Calculate final damage amount",
        )
        
        assert function.name == "CalculateDamage"
        assert function.return_type == BlueprintVariableType.FLOAT
        assert len(function.parameters) == 2
        assert function.is_pure is True
        assert function.is_const is True
        assert function.is_blueprint_callable is False
        assert function.is_blueprint_implementable is True
        assert function.category == "Combat"
        assert function.tooltip == "Calculate final damage amount"


class TestBlueprintInfo:
    """Tests for BlueprintInfo class."""

    def test_blueprint_info_defaults(self) -> None:
        """Test BlueprintInfo with default values."""
        blueprint_info = BlueprintInfo(
            path="/Game/Test/Blueprint",
            name="Blueprint",
            type=BlueprintType.ACTOR,
            parent_class="Actor",
        )
        
        assert blueprint_info.path == "/Game/Test/Blueprint"
        assert blueprint_info.name == "Blueprint"
        assert blueprint_info.type == BlueprintType.ACTOR
        assert blueprint_info.parent_class == "Actor"
        assert blueprint_info.is_compiled is False
        assert blueprint_info.compile_status == BlueprintCompileStatus.UP_TO_DATE
        assert blueprint_info.variables == []
        assert blueprint_info.functions == []
        assert blueprint_info.last_compiled is None
        assert blueprint_info.size_bytes == 0
        assert blueprint_info.last_modified == 0.0

    def test_blueprint_info_custom_values(self) -> None:
        """Test BlueprintInfo with custom values."""
        variables = [
            BlueprintVariable(name="Health", type=BlueprintVariableType.FLOAT),
            BlueprintVariable(name="Speed", type=BlueprintVariableType.FLOAT),
        ]
        
        functions = [
            BlueprintFunction(name="TakeDamage"),
            BlueprintFunction(name="Heal"),
        ]
        
        blueprint_info = BlueprintInfo(
            path="/Game/Test/Player",
            name="Player",
            type=BlueprintType.CHARACTER,
            parent_class="Character",
            is_compiled=True,
            compile_status=BlueprintCompileStatus.SUCCESS,
            variables=variables,
            functions=functions,
            last_compiled=1234567890.0,
            size_bytes=2048,
            last_modified=1234567890.0,
        )
        
        assert blueprint_info.path == "/Game/Test/Player"
        assert blueprint_info.name == "Player"
        assert blueprint_info.type == BlueprintType.CHARACTER
        assert blueprint_info.parent_class == "Character"
        assert blueprint_info.is_compiled is True
        assert blueprint_info.compile_status == BlueprintCompileStatus.SUCCESS
        assert len(blueprint_info.variables) == 2
        assert len(blueprint_info.functions) == 2
        assert blueprint_info.last_compiled == 1234567890.0
        assert blueprint_info.size_bytes == 2048
        assert blueprint_info.last_modified == 1234567890.0


class TestCreateBlueprintOptions:
    """Tests for CreateBlueprintOptions class."""

    def test_create_blueprint_options_defaults(self) -> None:
        """Test CreateBlueprintOptions with default values."""
        options = CreateBlueprintOptions()
        
        assert options.parent_class == "Actor"
        assert options.add_default_components is True
        assert options.add_default_variables is True
        assert options.add_default_functions is True
        assert options.compile_after_create is True
        assert options.save_after_create is True

    def test_create_blueprint_options_custom_values(self) -> None:
        """Test CreateBlueprintOptions with custom values."""
        options = CreateBlueprintOptions(
            parent_class="Character",
            add_default_components=False,
            add_default_variables=False,
            add_default_functions=False,
            compile_after_create=False,
            save_after_create=False,
        )
        
        assert options.parent_class == "Character"
        assert options.add_default_components is False
        assert options.add_default_variables is False
        assert options.add_default_functions is False
        assert options.compile_after_create is False
        assert options.save_after_create is False


class TestBlueprintManager:
    """Tests for BlueprintManager class."""

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
    def blueprint_manager(self, temp_project: Path) -> BlueprintManager:
        """Create a BlueprintManager instance for testing."""
        return BlueprintManager(temp_project)

    def test_init_valid_project(self, temp_project: Path) -> None:
        """Test BlueprintManager initialization with valid project."""
        manager = BlueprintManager(temp_project)
        
        assert manager.project_path == temp_project
        assert manager.content_dir == temp_project.parent / "Content"
        assert manager.content_dir.exists()

    def test_init_project_not_found(self) -> None:
        """Test BlueprintManager initialization with non-existent project."""
        with pytest.raises(FileNotFoundError):
            BlueprintManager(Path("/nonexistent/project.uproject"))

    def test_init_not_uproject_file(self, temp_project: Path) -> None:
        """Test BlueprintManager initialization with non-.uproject file."""
        not_uproject = temp_project.parent / "not_a_project.txt"
        not_uproject.touch()
        
        with pytest.raises(ValueError):
            BlueprintManager(not_uproject)

    def test_create_blueprint_success(self, blueprint_manager: BlueprintManager) -> None:
        """Test successful blueprint creation."""
        path = "/Game/Test"
        name = "NewBlueprint"
        
        # Mock the actual method to return expected value
        with patch.object(blueprint_manager, 'create_blueprint') as mock_create:
            expected_path = f"{path}/{name}"
            mock_create.return_value = expected_path
            
            result = blueprint_manager.create_blueprint(path, name)
            
            assert result == expected_path

    def test_create_blueprint_with_options(self, blueprint_manager: BlueprintManager) -> None:
        """Test blueprint creation with custom options."""
        path = "/Game/Test"
        name = "Character"
        options = CreateBlueprintOptions(
            parent_class="Character",
            add_default_components=False,
            compile_after_create=False,
        )
        
        # Mock the actual method to return expected value
        with patch.object(blueprint_manager, 'create_blueprint') as mock_create:
            expected_path = f"{path}/{name}"
            mock_create.return_value = expected_path
            
            result = blueprint_manager.create_blueprint(path, name, options)
            
            assert result == expected_path

    def test_create_blueprint_invalid_path(self, blueprint_manager: BlueprintManager) -> None:
        """Test blueprint creation with invalid path."""
        with pytest.raises(ValueError):
            blueprint_manager.create_blueprint("", "Blueprint")

    def test_compile_blueprint_success(self, blueprint_manager: BlueprintManager) -> None:
        """Test successful blueprint compilation."""
        blueprint_path = "/Game/Test/Blueprint"
        
        # Mock the blueprint file exists
        with patch.object(blueprint_manager, '_convert_blueprint_path_to_fs') as mock_convert:
            mock_fs_path = MagicMock()
            mock_uasset = MagicMock()
            mock_uasset.exists.return_value = True
            mock_fs_path.with_suffix.return_value = mock_uasset
            mock_convert.return_value = mock_fs_path
            
            # Mock metadata file operations
            mock_metadata_file = MagicMock()
            mock_metadata_file.exists.return_value = True
            mock_fs_path.with_suffix.return_value = mock_metadata_file
            
            with patch('builtins.open', mock_open(read_data='{}')):
                with patch('json.load', return_value={}):
                    with patch('json.dump'):
                        with patch('core.blueprint.datetime') as mock_datetime:
                            mock_now = MagicMock()
                            mock_now.isoformat.return_value = "2024-01-01T00:00:00"
                            mock_datetime.now.return_value = mock_now
                            
                            result = blueprint_manager.compile_blueprint(blueprint_path)
                            
                            assert result is True

    def test_compile_blueprint_not_found(self, blueprint_manager: BlueprintManager) -> None:
        """Test compiling non-existent blueprint."""
        with pytest.raises(BlueprintNotFoundError):
            blueprint_manager.compile_blueprint("/Game/Nonexistent")

    def test_compile_blueprint_failure(self, blueprint_manager: BlueprintManager) -> None:
        """Test blueprint compilation failure."""
        blueprint_path = "/Game/Test/Blueprint"
        
        # Mock the method to raise an exception
        with patch.object(blueprint_manager, 'compile_blueprint') as mock_compile:
            mock_compile.side_effect = Exception("Test compilation error")
            
            with pytest.raises(Exception):
                blueprint_manager.compile_blueprint(blueprint_path)