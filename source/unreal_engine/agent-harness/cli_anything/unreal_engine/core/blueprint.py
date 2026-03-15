"""Unreal Engine CLI - Blueprint management module.

Provides blueprint creation, compilation, listing, and duplication
functionality for UE5 projects.

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


class BlueprintType(Enum):
    """UE5 blueprint types."""
    ACTOR = "Actor"
    PAWN = "Pawn"
    CHARACTER = "Character"
    PLAYER_CONTROLLER = "PlayerController"
    GAME_MODE = "GameMode"
    GAME_STATE = "GameState"
    PLAYER_STATE = "PlayerState"
    HUD = "HUD"
    USER_WIDGET = "UserWidget"
    WIDGET = "Widget"
    ANIM_INSTANCE = "AnimInstance"
    DATA_ASSET = "DataAsset"
    PRIMARY_DATA_ASSET = "PrimaryDataAsset"
    SAVE_GAME = "SaveGame"
    STRUCT = "Struct"
    ENUM = "Enum"
    INTERFACE = "Interface"
    FUNCTION_LIBRARY = "FunctionLibrary"
    MACRO_LIBRARY = "MacroLibrary"
    OTHER = "Other"


class BlueprintCompileStatus(Enum):
    """Blueprint compilation status."""
    SUCCESS = auto()
    FAILED = auto()
    UP_TO_DATE = auto()
    ERROR = auto()


class BlueprintVariableType(Enum):
    """Blueprint variable types."""
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    VECTOR = "Vector"
    ROTATOR = "Rotator"
    TRANSFORM = "Transform"
    OBJECT = "Object"
    ACTOR = "Actor"
    CLASS = "Class"
    INTERFACE = "Interface"
    STRUCT = "Struct"
    ENUM = "Enum"
    ARRAY = "Array"
    MAP = "Map"
    SET = "Set"


@dataclass
class BlueprintVariable:
    """Blueprint variable information.

    Attributes:
        name: Variable name.
        type: Variable type.
        default_value: Default value.
        is_editable: Whether the variable is editable.
        is_visible: Whether the variable is visible.
        is_read_only: Whether the variable is read-only.
        category: Variable category.
        tooltip: Variable tooltip.
    """
    name: str
    type: BlueprintVariableType
    default_value: Any = None
    is_editable: bool = True
    is_visible: bool = True
    is_read_only: bool = False
    category: str = "Default"
    tooltip: str = ""


@dataclass
class BlueprintFunction:
    """Blueprint function information.

    Attributes:
        name: Function name.
        return_type: Return type.
        parameters: List of parameter names and types.
        is_pure: Whether the function is pure (no side effects).
        is_const: Whether the function is const.
        is_blueprint_callable: Whether the function is blueprint callable.
        is_blueprint_implementable: Whether the function is blueprint implementable.
        category: Function category.
        tooltip: Function tooltip.
    """
    name: str
    return_type: Optional[BlueprintVariableType] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    is_pure: bool = False
    is_const: bool = False
    is_blueprint_callable: bool = True
    is_blueprint_implementable: bool = False
    category: str = "Default"
    tooltip: str = ""


@dataclass
class BlueprintInfo:
    """Information about a UE5 blueprint.

    Attributes:
        path: Blueprint path in /Game/... format.
        name: Blueprint name.
        type: Blueprint type.
        parent_class: Parent class name.
        is_compiled: Whether the blueprint is compiled.
        compile_status: Compilation status.
        variables: List of blueprint variables.
        functions: List of blueprint functions.
        last_compiled: Last compilation timestamp.
        size_bytes: File size in bytes.
        last_modified: Last modification timestamp.
    """
    path: str
    name: str
    type: BlueprintType
    parent_class: str
    is_compiled: bool = False
    compile_status: BlueprintCompileStatus = BlueprintCompileStatus.UP_TO_DATE
    variables: List[BlueprintVariable] = field(default_factory=list)
    functions: List[BlueprintFunction] = field(default_factory=list)
    last_compiled: Optional[float] = None
    size_bytes: int = 0
    last_modified: float = 0.0


@dataclass
class CreateBlueprintOptions:
    """Options for blueprint creation.

    Attributes:
        parent_class: Parent class for the blueprint.
        add_default_components: Add default components.
        add_default_variables: Add default variables.
        add_default_functions: Add default functions.
        compile_after_create: Compile after creation.
        save_after_create: Save after creation.
    """
    parent_class: str = "Actor"
    add_default_components: bool = True
    add_default_variables: bool = True
    add_default_functions: bool = True
    compile_after_create: bool = True
    save_after_create: bool = True


class BlueprintManagerError(Exception):
    """Base exception for BlueprintManager errors."""
    pass


class BlueprintCreationError(BlueprintManagerError):
    """Exception raised when blueprint creation fails."""
    pass


class BlueprintCompilationError(BlueprintManagerError):
    """Exception raised when blueprint compilation fails."""
    pass


class BlueprintNotFoundError(BlueprintManagerError):
    """Exception raised when blueprint is not found."""
    pass


class BlueprintManager:
    """UE5 blueprint manager.

    Provides blueprint creation, compilation, listing, and duplication
    functionality.

    Attributes:
        project_path: Path to the UE5 project (.uproject file).
        content_dir: Path to the project's Content directory.
        engine_path: Path to the UE5 engine installation.
    """

    def __init__(self, project_path: Path, engine_path: Optional[Path] = None):
        """Initialize the blueprint manager.

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

    def create_blueprint(
        self,
        name: str,
        path: str,
        options: Optional[CreateBlueprintOptions] = None
    ) -> str:
        """Create a new blueprint.

        Args:
            name: Blueprint name.
            path: Blueprint path in /Game/... format.
            options: Creation options. If None, default options are used.

        Returns:
            The created blueprint path.

        Raises:
            BlueprintCreationError: If creation fails.
            ValueError: If name or path is invalid.
        """
        if not name:
            raise ValueError("Blueprint name cannot be empty")
        if not path:
            raise ValueError("Blueprint path cannot be empty")

        if options is None:
            options = CreateBlueprintOptions()

        # Normalize path
        if not path.startswith("/Game/"):
            path = f"/Game/{path.lstrip('/')}"

        # Remove trailing slash
        path = path.rstrip("/")

        # Full blueprint path
        blueprint_path = f"{path}/{name}"

        # Check if blueprint already exists
        fs_path = self._convert_blueprint_path_to_fs(blueprint_path)
        if fs_path.with_suffix(".uasset").exists():
            raise BlueprintCreationError(
                f"Blueprint already exists: {blueprint_path}"
            )

        try:
            # Create directory
            fs_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine blueprint type from parent class
            blueprint_type = self._determine_blueprint_type(options.parent_class)

            # Create blueprint files
            self._create_blueprint_files(
                fs_path,
                name,
                blueprint_type,
                options
            )

            # Compile if requested
            if options.compile_after_create:
                compile_success = self.compile_blueprint(blueprint_path)
                if not compile_success:
                    raise BlueprintCreationError(
                        f"Blueprint created but compilation failed: {blueprint_path}"
                    )

            # Save if requested
            if options.save_after_create:
                self._save_blueprint(fs_path)

            return blueprint_path

        except BlueprintCreationError:
            raise
        except Exception as e:
            raise BlueprintCreationError(f"Failed to create blueprint: {e}") from e

    def compile_blueprint(self, blueprint_path: str) -> bool:
        """Compile a blueprint.

        Args:
            blueprint_path: Blueprint path in /Game/... format.

        Returns:
            True if compilation was successful, False otherwise.

        Raises:
            BlueprintNotFoundError: If blueprint is not found.
            BlueprintCompilationError: If compilation fails.
        """
        # Normalize blueprint path
        if not blueprint_path.startswith("/Game/"):
            blueprint_path = f"/Game/{blueprint_path.lstrip('/')}"

        # Check if blueprint exists
        fs_path = self._convert_blueprint_path_to_fs(blueprint_path)
        if not fs_path.with_suffix(".uasset").exists():
            raise BlueprintNotFoundError(f"Blueprint not found: {blueprint_path}")

        try:
            # For now, simulate compilation
            # In a real implementation, this would call UE5's compilation tools
            
            # Update compilation metadata
            metadata_file = fs_path.with_suffix(".uasset.meta")
            metadata = {}
            
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            
            metadata["last_compiled"] = datetime.now().isoformat()
            metadata["compile_status"] = "success"
            metadata["is_compiled"] = True
            
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Update blueprint file timestamp
            uasset_file = fs_path.with_suffix(".uasset")
            uasset_file.touch()

            return True

        except Exception as e:
            raise BlueprintCompilationError(f"Failed to compile blueprint: {e}") from e

    def list_blueprints(
        self,
        path: str = "/Game",
        recursive: bool = True,
        filter_type: Optional[BlueprintType] = None
    ) -> List[BlueprintInfo]:
        """List blueprints in the specified path.

        Args:
            path: Blueprint path to list (e.g., "/Game", "/Game/Blueprints").
            recursive: Whether to list recursively.
            filter_type: Filter by blueprint type.

        Returns:
            List of BlueprintInfo objects.

        Raises:
            BlueprintManagerError: If listing fails.
        """
        # Normalize path
        if not path.startswith("/Game/"):
            if path == "/Game":
                fs_path = self.content_dir
            else:
                path = f"/Game/{path.lstrip('/')}"
                fs_path = self._convert_blueprint_path_to_fs(path)
        else:
            fs_path = self._convert_blueprint_path_to_fs(path)

        if not fs_path.exists():
            return []

        blueprints: List[BlueprintInfo] = []

        try:
            if recursive:
                pattern = "**/*.uasset"
            else:
                pattern = "*.uasset"

            for uasset_file in fs_path.glob(pattern):
                # Check if this is a blueprint (contains "Blueprint" in metadata or name)
                if "Blueprint" not in uasset_file.stem:
                    continue

                # Skip metadata files
                if uasset_file.name.endswith(".meta"):
                    continue

                # Get blueprint path relative to content directory
                rel_path = uasset_file.relative_to(self.content_dir)
                blueprint_path = f"/Game/{rel_path.with_suffix('').as_posix()}"

                # Get blueprint info
                blueprint_info = self._get_blueprint_info(blueprint_path, uasset_file)
                
                # Apply filter
                if filter_type is None or blueprint_info.type == filter_type:
                    blueprints.append(blueprint_info)

            return sorted(blueprints, key=lambda x: x.path)

        except Exception as e:
            raise BlueprintManagerError(f"Failed to list blueprints: {e}") from e

    def duplicate_blueprint(
        self,
        source_path: str,
        new_name: str,
        target_path: Optional[str] = None
    ) -> str:
        """Duplicate a blueprint.

        Args:
            source_path: Source blueprint path in /Game/... format.
            new_name: New blueprint name.
            target_path: Target path for the duplicate. If None, uses same path as source.

        Returns:
            The duplicated blueprint path.

        Raises:
            BlueprintNotFoundError: If source blueprint is not found.
            BlueprintCreationError: If duplication fails.
        """
        # Normalize source path
        if not source_path.startswith("/Game/"):
            source_path = f"/Game/{source_path.lstrip('/')}"

        # Check if source blueprint exists
        source_fs_path = self._convert_blueprint_path_to_fs(source_path)
        if not source_fs_path.with_suffix(".uasset").exists():
            raise BlueprintNotFoundError(f"Source blueprint not found: {source_path}")

        # Determine target path
        if target_path is None:
            # Use same directory as source
            target_path = "/".join(source_path.split("/")[:-1])
        
        # Normalize target path
        if not target_path.startswith("/Game/"):
            target_path = f"/Game/{target_path.lstrip('/')}"

        # Remove trailing slash
        target_path = target_path.rstrip("/")

        # Full target blueprint path
        target_blueprint_path = f"{target_path}/{new_name}"

        # Check if target already exists
        target_fs_path = self._convert_blueprint_path_to_fs(target_blueprint_path)
        if target_fs_path.with_suffix(".uasset").exists():
            raise BlueprintCreationError(
                f"Target blueprint already exists: {target_blueprint_path}"
            )

        try:
            # Create target directory
            target_fs_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy blueprint files
            for ext in [".uasset", ".uasset.meta", ".uexp", ".ubulk"]:
                source_file = source_fs_path.with_suffix(ext)
                target_file = target_fs_path.with_suffix(ext)
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)

            # Update metadata with new name
            metadata_file = target_fs_path.with_suffix(".uasset.meta")
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                
                metadata["name"] = new_name
                metadata["original_source"] = source_path
                metadata["duplicated_from"] = source_path
                metadata["duplication_time"] = datetime.now().isoformat()
                
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

            # Rename references in the blueprint file (simulated)
            # In a real implementation, this would require parsing and updating the blueprint

            return target_blueprint_path

        except Exception as e:
            raise BlueprintCreationError(f"Failed to duplicate blueprint: {e}") from e

    # Helper methods

    def _convert_blueprint_path_to_fs(self, blueprint_path: str) -> Path:
        """Convert blueprint path (/Game/...) to filesystem path.

        Args:
            blueprint_path: Blueprint path in /Game/... format.

        Returns:
            Filesystem path.
        """
        if not blueprint_path.startswith("/Game/"):
            raise ValueError(f"Invalid blueprint path: {blueprint_path}")

        # Remove /Game/ prefix
        rel_path = blueprint_path[6:]  # Remove "/Game/"
        
        # Convert to filesystem path
        fs_path = self.content_dir / rel_path.replace("/", "\\")
        
        return fs_path

    def _determine_blueprint_type(self, parent_class: str) -> BlueprintType:
        """Determine blueprint type from parent class.

        Args:
            parent_class: Parent class name.

        Returns:
            BlueprintType enum value.
        """
        parent_class_lower = parent_class.lower()
        
        type_map = {
            "actor": BlueprintType.ACTOR,
            "pawn": BlueprintType.PAWN,
            "character": BlueprintType.CHARACTER,
            "playercontroller": BlueprintType.PLAYER_CONTROLLER,
            "gamemode": BlueprintType.GAME_MODE,
            "gamestate": BlueprintType.GAME_STATE,
            "playerstate": BlueprintType.PLAYER_STATE,
            "hud": BlueprintType.HUD,
            "userwidget": BlueprintType.USER_WIDGET,
            "widget": BlueprintType.WIDGET,
            "animinstance": BlueprintType.ANIM_INSTANCE,
            "dataasset": BlueprintType.DATA_ASSET,
            "primarydataasset": BlueprintType.PRIMARY_DATA_ASSET,
            "savegame": BlueprintType.SAVE_GAME,
            "struct": BlueprintType.STRUCT,
            "enum": BlueprintType.ENUM,
            "interface": BlueprintType.INTERFACE,
            "functionlibrary": BlueprintType.FUNCTION_LIBRARY,
            "macrolibrary": BlueprintType.MACRO_LIBRARY,
        }
        
        return type_map.get(parent_class_lower, BlueprintType.OTHER)

    def _create_blueprint_files(
        self,
        fs_path: Path,
        name: str,
        blueprint_type: BlueprintType,
        options: CreateBlueprintOptions
    ) -> None:
        """Create blueprint files.

        Args:
            fs_path: Filesystem path for the blueprint.
            name: Blueprint name.
            blueprint_type: Blueprint type.
            options: Creation options.
        """
        # Create blueprint metadata
        metadata = {
            "name": name,
            "type": blueprint_type.value,
            "parent_class": options.parent_class,
            "created_time": datetime.now().isoformat(),
            "is_compiled": False,
            "compile_status": "not_compiled",
            "variables": [],
            "functions": [],
            "components": [],
            "default_values": {},
        }

        # Add default variables if requested
        if options.add_default_variables:
            metadata["variables"] = self._get_default_variables(blueprint_type)

        # Add default functions if requested
        if options.add_default_functions:
            metadata["functions"] = self._get_default_functions(blueprint_type)

        # Add default components if requested
        if options.add_default_components:
            metadata["components"] = self._get_default_components(blueprint_type)

        # Write metadata file
        metadata_file = fs_path.with_suffix(".uasset.meta")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Create empty blueprint file
        uasset_file = fs_path.with_suffix(".uasset")
        with open(uasset_file, "wb") as f:
            # In a real implementation, this would create actual blueprint binary data
            f.write(b"UE5_BLUEPRINT_FILE")

    def _get_blueprint_info(
        self,
        blueprint_path: str,
        uasset_file: Path
    ) -> BlueprintInfo:
        """Get BlueprintInfo for a blueprint file.

        Args:
            blueprint_path: Blueprint path in /Game/... format.
            uasset_file: Path to the .uasset file.

        Returns:
            BlueprintInfo object.
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

        # Extract blueprint information
        name = metadata.get("name", uasset_file.stem)
        blueprint_type_str = metadata.get("type", "OTHER")
        parent_class = metadata.get("parent_class", "Actor")
        is_compiled = metadata.get("is_compiled", False)
        last_compiled = metadata.get("last_compiled")
        
        # Convert string to enum
        try:
            blueprint_type = BlueprintType(blueprint_type_str)
        except:
            blueprint_type = BlueprintType.OTHER

        # Convert compile status
        compile_status_str = metadata.get("compile_status", "up_to_date")
        compile_status_map = {
            "success": BlueprintCompileStatus.SUCCESS,
            "failed": BlueprintCompileStatus.FAILED,
            "up_to_date": BlueprintCompileStatus.UP_TO_DATE,
            "error": BlueprintCompileStatus.ERROR,
        }
        compile_status = compile_status_map.get(
            compile_status_str,
            BlueprintCompileStatus.UP_TO_DATE
        )

        # Parse variables
        variables = []
        for var_data in metadata.get("variables", []):
            try:
                var_type = BlueprintVariableType(var_data.get("type", "bool"))
                variable = BlueprintVariable(
                    name=var_data.get("name", ""),
                    type=var_type,
                    default_value=var_data.get("default_value"),
                    is_editable=var_data.get("is_editable", True),
                    is_visible=var_data.get("is_visible", True),
                    is_read_only=var_data.get("is_read_only", False),
                    category=var_data.get("category", "Default"),
                    tooltip=var_data.get("tooltip", "")
                )
                variables.append(variable)
            except:
                pass

        # Parse functions
        functions = []
        for func_data in metadata.get("functions", []):
            try:
                return_type_str = func_data.get("return_type")
                return_type = None
                if return_type_str:
                    return_type = BlueprintVariableType(return_type_str)
                
                function = BlueprintFunction(
                    name=func_data.get("name", ""),
                    return_type=return_type,
                    parameters=func_data.get("parameters", []),
                    is_pure=func_data.get("is_pure", False),
                    is_const=func_data.get("is_const", False),
                    is_blueprint_callable=func_data.get("is_blueprint_callable", True),
                    is_blueprint_implementable=func_data.get("is_blueprint_implementable", False),
                    category=func_data.get("category", "Default"),
                    tooltip=func_data.get("tooltip", "")
                )
                functions.append(function)
            except:
                pass

        # Convert last_compiled timestamp
        last_compiled_ts = None
        if last_compiled:
            try:
                dt = datetime.fromisoformat(last_compiled.replace("Z", "+00:00"))
                last_compiled_ts = dt.timestamp()
            except:
                pass

        return BlueprintInfo(
            path=blueprint_path,
            name=name,
            type=blueprint_type,
            parent_class=parent_class,
            is_compiled=is_compiled,
            compile_status=compile_status,
            variables=variables,
            functions=functions,
            last_compiled=last_compiled_ts,
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime
        )

    def _get_default_variables(self, blueprint_type: BlueprintType) -> List[Dict[str, Any]]:
        """Get default variables for a blueprint type.

        Args:
            blueprint_type: Blueprint type.

        Returns:
            List of variable dictionaries.
        """
        defaults = {
            BlueprintType.ACTOR: [
                {
                    "name": "bHidden",
                    "type": "bool",
                    "default_value": False,
                    "is_editable": True,
                    "category": "Actor",
                    "tooltip": "Whether the actor is hidden in game"
                },
                {
                    "name": "bCanBeDamaged",
                    "type": "bool",
                    "default_value": False,
                    "is_editable": True,
                    "category": "Actor",
                    "tooltip": "Whether the actor can be damaged"
                }
            ],
            BlueprintType.CHARACTER: [
                {
                    "name": "WalkSpeed",
                    "type": "float",
                    "default_value": 600.0,
                    "is_editable": True,
                    "category": "Movement",
                    "tooltip": "Character walk speed"
                },
                {
                    "name": "JumpZVelocity",
                    "type": "float",
                    "default_value": 420.0,
                    "is_editable": True,
                    "category": "Movement",
                    "tooltip": "Character jump velocity"
                }
            ],
            BlueprintType.USER_WIDGET: [
                {
                    "name": "bIsFocusable",
                    "type": "bool",
                    "default_value": True,
                    "is_editable": True,
                    "category": "Widget",
                    "tooltip": "Whether the widget can receive focus"
                },
                {
                    "name": "Visibility",
                    "type": "string",
                    "default_value": "Visible",
                    "is_editable": True,
                    "category": "Widget",
                    "tooltip": "Widget visibility state"
                }
            ]
        }
        
        return defaults.get(blueprint_type, [])

    def _get_default_functions(self, blueprint_type: BlueprintType) -> List[Dict[str, Any]]:
        """Get default functions for a blueprint type.

        Args:
            blueprint_type: Blueprint type.

        Returns:
            List of function dictionaries.
        """
        defaults = {
            BlueprintType.ACTOR: [
                {
                    "name": "BeginPlay",
                    "return_type": None,
                    "parameters": [],
                    "is_pure": False,
                    "is_const": False,
                    "is_blueprint_callable": False,
                    "is_blueprint_implementable": True,
                    "category": "Events",
                    "tooltip": "Called when the game starts or when spawned"
                },
                {
                    "name": "Tick",
                    "return_type": None,
                    "parameters": [
                        {"name": "DeltaSeconds", "type": "float"}
                    ],
                    "is_pure": False,
                    "is_const": False,
                    "is_blueprint_callable": False,
                    "is_blueprint_implementable": True,
                    "category": "Events",
                    "tooltip": "Called every frame"
                }
            ],
            BlueprintType.CHARACTER: [
                {
                    "name": "Jump",
                    "return_type": None,
                    "parameters": [],
                    "is_pure": False,
                    "is_const": False,
                    "is_blueprint_callable": True,
                    "is_blueprint_implementable": False,
                    "category": "Movement",
                    "tooltip": "Makes the character jump"
                },
                {
                    "name": "StopJumping",
                    "return_type": None,
                    "parameters": [],
                    "is_pure": False,
                    "is_const": False,
                    "is_blueprint_callable": True,
                    "is_blueprint_implementable": False,
                    "category": "Movement",
                    "tooltip": "Stops the character from jumping"
                }
            ]
        }
        
        return defaults.get(blueprint_type, [])

    def _get_default_components(self, blueprint_type: BlueprintType) -> List[Dict[str, Any]]:
        """Get default components for a blueprint type.

        Args:
            blueprint_type: Blueprint type.

        Returns:
            List of component dictionaries.
        """
        defaults = {
            BlueprintType.ACTOR: [
                {
                    "type": "SceneComponent",
                    "name": "DefaultSceneRoot"
                }
            ],
            BlueprintType.CHARACTER: [
                {
                    "type": "CapsuleComponent",
                    "name": "CapsuleComponent"
                },
                {
                    "type": "SkeletalMeshComponent",
                    "name": "Mesh"
                },
                {
                    "type": "CharacterMovementComponent",
                    "name": "CharacterMovement"
                }
            ],
            BlueprintType.PAWN: [
                {
                    "type": "SceneComponent",
                    "name": "RootComponent"
                }
            ]
        }
        
        return defaults.get(blueprint_type, [])

    def _save_blueprint(self, fs_path: Path) -> None:
        """Save blueprint changes.

        Args:
            fs_path: Filesystem path for the blueprint.
        """
        # For now, just update the timestamp
        # In a real implementation, this would serialize the blueprint
        uasset_file = fs_path.with_suffix(".uasset")
        if uasset_file.exists():
            uasset_file.touch()
