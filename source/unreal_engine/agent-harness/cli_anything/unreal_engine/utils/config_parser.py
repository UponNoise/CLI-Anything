"""Unreal Engine CLI - Configuration file parser module.

Handles parsing and manipulation of UE5 configuration files:
- .uproject files (JSON-based project configuration)
- .ini files (Unreal Engine configuration files)
- Config file merging and validation
"""

import configparser
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConfigFileType(Enum):
    """Types of UE5 configuration files."""
    UPROJECT = "uproject"
    INI = "ini"
    JSON = "json"
    XML = "xml"


class ConfigSectionType(Enum):
    """Types of configuration sections."""
    ENGINE = "Engine"
    EDITOR = "Editor"
    PROJECT = "Project"
    PLUGIN = "Plugin"
    PLATFORM = "Platform"
    CUSTOM = "Custom"


@dataclass
class ConfigValue:
    """Represents a configuration value with metadata.
    
    Attributes:
        key: Configuration key
        value: Configuration value (can be any type)
        section: Section name
        file_type: Type of configuration file
        source_file: Source file path
        comments: Associated comments
        is_default: Whether this is a default value
        is_overridden: Whether this value overrides a default
    """
    key: str
    value: Any
    section: str
    file_type: ConfigFileType
    source_file: Path
    comments: List[str] = field(default_factory=list)
    is_default: bool = False
    is_overridden: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation
        """
        return {
            "key": self.key,
            "value": self.value,
            "section": self.section,
            "file_type": self.file_type.value,
            "source_file": str(self.source_file),
            "comments": self.comments,
            "is_default": self.is_default,
            "is_overridden": self.is_overridden,
        }


@dataclass
class ConfigSection:
    """Represents a configuration section.
    
    Attributes:
        name: Section name
        type: Section type
        values: Dictionary of key-value pairs
        source_file: Source file path
        comments: Section comments
        is_default: Whether this is a default section
    """
    name: str
    type: ConfigSectionType
    values: Dict[str, ConfigValue]
    source_file: Path
    comments: List[str] = field(default_factory=list)
    is_default: bool = False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value from section.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if key in self.values:
            return self.values[key].value
        return default
    
    def set_value(self, key: str, value: Any, comments: List[str] = None) -> None:
        """Set value in section.
        
        Args:
            key: Configuration key
            value: Configuration value
            comments: Optional comments
        """
        self.values[key] = ConfigValue(
            key=key,
            value=value,
            section=self.name,
            file_type=ConfigFileType.INI,
            source_file=self.source_file,
            comments=comments or [],
            is_default=False,
            is_overridden=True,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "values": {k: v.to_dict() for k, v in self.values.items()},
            "source_file": str(self.source_file),
            "comments": self.comments,
            "is_default": self.is_default,
        }


class UProjectParser:
    """Parser for .uproject files.
    
    Handles parsing, validation, and manipulation of UE5 project files.
    """
    
    REQUIRED_FIELDS = ["FileVersion", "EngineAssociation", "Category", "Description"]
    
    def __init__(self, project_path: Path):
        """Initialize parser.
        
        Args:
            project_path: Path to .uproject file
            
        Raises:
            FileNotFoundError: If project file doesn't exist
            ValueError: If project file is invalid
        """
        self.project_path = project_path
        self._validate_project_path()
        self._data = self._load_project_data()
    
    def _validate_project_path(self) -> None:
        """Validate project file path.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a .uproject file
        """
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project file not found: {self.project_path}")
        
        if self.project_path.suffix != ".uproject":
            raise ValueError(f"Not a .uproject file: {self.project_path}")
    
    def _load_project_data(self) -> Dict[str, Any]:
        """Load project data from file.
        
        Returns:
            Project data as dictionary
            
        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            with open(self.project_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate required fields
            for field in self.REQUIRED_FIELDS:
                if field not in data:
                    raise ValueError(f"Missing required field in .uproject: {field}")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in .uproject file: {e}")
    
    def get_engine_association(self) -> str:
        """Get engine association.
        
        Returns:
            Engine association identifier
        """
        return self._data.get("EngineAssociation", "")
    
    def get_modules(self) -> List[Dict[str, Any]]:
        """Get project modules.
        
        Returns:
            List of module configurations
        """
        return self._data.get("Modules", [])
    
    def get_plugins(self) -> List[Dict[str, Any]]:
        """Get project plugins.
        
        Returns:
            List of plugin configurations
        """
        return self._data.get("Plugins", [])
    
    def get_target_configurations(self) -> Dict[str, Any]:
        """Get target configurations.
        
        Returns:
            Target configurations dictionary
        """
        return self._data.get("TargetConfigurations", {})
    
    def get_custom_fields(self) -> Dict[str, Any]:
        """Get custom fields not covered by standard accessors.
        
        Returns:
            Dictionary of custom fields
        """
        standard_fields = {
            "FileVersion", "EngineAssociation", "Category", "Description",
            "Modules", "Plugins", "TargetConfigurations"
        }
        
        return {
            k: v for k, v in self._data.items()
            if k not in standard_fields
        }
    
    def update_module(self, module_name: str, updates: Dict[str, Any]) -> bool:
        """Update module configuration.
        
        Args:
            module_name: Name of module to update
            updates: Dictionary of updates
            
        Returns:
            True if module was updated, False if not found
        """
        modules = self.get_modules()
        for module in modules:
            if module.get("Name") == module_name:
                module.update(updates)
                return True
        return False
    
    def add_module(self, module_config: Dict[str, Any]) -> None:
        """Add new module to project.
        
        Args:
            module_config: Module configuration dictionary
            
        Raises:
            ValueError: If module configuration is invalid
        """
        required_fields = ["Name", "Type", "LoadingPhase"]
        for field in required_fields:
            if field not in module_config:
                raise ValueError(f"Module missing required field: {field}")
        
        modules = self.get_modules()
        modules.append(module_config)
        self._data["Modules"] = modules
    
    def enable_plugin(self, plugin_name: str, enabled: bool = True) -> bool:
        """Enable or disable plugin.
        
        Args:
            plugin_name: Name of plugin
            enabled: Whether to enable plugin
            
        Returns:
            True if plugin was found and updated, False otherwise
        """
        plugins = self.get_plugins()
        for plugin in plugins:
            if plugin.get("Name") == plugin_name:
                plugin["Enabled"] = enabled
                return True
        return False
    
    def save(self, file_path: Optional[Path] = None) -> None:
        """Save project data to file.
        
        Args:
            file_path: Optional path to save to (defaults to original)
        """
        save_path = file_path or self.project_path
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
    
    def validate(self) -> List[str]:
        """Validate project configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self._data:
                errors.append(f"Missing required field: {field}")
        
        # Check engine association
        engine_assoc = self.get_engine_association()
        if not engine_assoc:
            errors.append("Empty engine association")
        
        # Validate modules
        modules = self.get_modules()
        for i, module in enumerate(modules):
            if "Name" not in module:
                errors.append(f"Module {i} missing 'Name' field")
            if "Type" not in module:
                errors.append(f"Module {module.get('Name', f'#{i}')} missing 'Type' field")
            if "LoadingPhase" not in module:
                errors.append(f"Module {module.get('Name', f'#{i}')} missing 'LoadingPhase' field")
        
        # Validate plugins
        plugins = self.get_plugins()
        for i, plugin in enumerate(plugins):
            if "Name" not in plugin:
                errors.append(f"Plugin {i} missing 'Name' field")
        
        return errors


class IniConfigParser:
    """Parser for UE5 .ini configuration files.
    
    Handles the specific format of Unreal Engine .ini files,
    including section inheritance and special syntax.
    """
    
    def __init__(self):
        """Initialize parser."""
        self._config = configparser.ConfigParser(
            interpolation=None,
            strict=False,
            empty_lines_in_values=False
        )
        self._comments: Dict[str, Dict[str, List[str]]] = {}
        self._source_files: Dict[str, Path] = {}
    
    def load_file(self, file_path: Path) -> None:
        """Load .ini file.
        
        Args:
            file_path: Path to .ini file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            configparser.Error: If parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        # Read file with comments
        content = file_path.read_text(encoding="utf-8")
        self._parse_with_comments(content, file_path)
        
        # Store source file
        for section in self._config.sections():
            self._source_files[section] = file_path
    
    def _parse_with_comments(self, content: str, file_path: Path) -> None:
        """Parse .ini content while preserving comments.
        
        Args:
            content: .ini file content
            file_path: Source file path
        """
        lines = content.splitlines()
        current_section = None
        current_comments = []
        
        for line_num, line in enumerate(lines):
            line = line.rstrip()
            
            # Skip empty lines but preserve comment context
            if not line.strip():
                continue
            
            # Check for comment
            if line.strip().startswith(";"):
                current_comments.append(line.strip())
                continue
            
            # Check for section header
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                current_section = section_name
                
                # Initialize comments storage for this section
                if section_name not in self._comments:
                    self._comments[section_name] = {}
                
                # Store section comments
                if current_comments:
                    self._comments[section_name]["__section__"] = current_comments.copy()
                    current_comments.clear()
                
                # Ensure section exists in config
                if not self._config.has_section(section_name):
                    self._config.add_section(section_name)
                
                continue
            
            # Parse key-value pair
            if "=" in line and current_section:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Set value in config
                self._config.set(current_section, key, value)
                
                # Store comments for this key
                if current_comments:
                    if current_section not in self._comments:
                        self._comments[current_section] = {}
                    self._comments[current_section][key] = current_comments.copy()
                    current_comments.clear()
    
    def get_section(self, section_name: str) -> Optional[ConfigSection]:
        """Get configuration section.
        
        Args:
            section_name: Name of section
            
        Returns:
            ConfigSection object or None if not found
        """
        if not self._config.has_section(section_name):
            return None
        
        # Determine section type
        section_type = self._determine_section_type(section_name)
        
        # Get values
        values = {}
        for key in self._config.options(section_name):
            value = self._config.get(section_name, key)
            
            # Get comments for this key
            comments = []
            if (section_name in self._comments and 
                key in self._comments[section_name]):
                comments = self._comments[section_name][key]
            
            config_value = ConfigValue(
                key=key,
                value=value,
                section=section_name,
                file_type=ConfigFileType.INI,
                source_file=self._source_files.get(section_name, Path(".")),
                comments=comments,
                is_default=False,
                is_overridden=False,
            )
            values[key] = config_value
        
        # Get section comments
        section_comments = []
        if (section_name in self._comments and 
            "__section__" in self._comments[section_name]):
            section_comments = self._comments[section_name]["__section__"]
        
        return ConfigSection(
            name=section_name,
            type=section_type,
            values=values,
            source_file=self._source_files.get(section_name, Path(".")),
            comments=section_comments,
            is_default=False,
        )
    
    def _determine_section_type(self, section_name: str) -> ConfigSectionType:
        """Determine type of configuration section.
        
        Args:
            section_name: Name of section
            
        Returns:
            ConfigSectionType
        """
        section_lower = section_name.lower()
        
        if "engine" in section_lower:
            return ConfigSectionType.ENGINE
        elif "editor" in section_lower:
            return ConfigSectionType.EDITOR
        elif "project" in section_lower:
            return ConfigSectionType.PROJECT
        elif "plugin" in section_lower:
            return ConfigSectionType.PLUGIN
        elif any(platform in section_lower for platform in 
                ["windows", "mac", "linux", "android", "ios", "ps5", "xbox"]):
            return ConfigSectionType.PLATFORM
        else:
            return ConfigSectionType.CUSTOM
    
    def set_value(self, section_name: str, key: str, value: Any, 
                 comments: List[str] = None) -> None:
        """Set configuration value.
        
        Args:
            section_name: Section name
            key: Configuration key
            value: Configuration value
            comments: Optional comments
        """
        # Ensure section exists
        if not self._config.has_section(section_name):
            self._config.add_section(section_name)
        
        # Set value
        self._config.set(section_name, key, str(value))
        
        # Store comments
        if comments:
            if section_name not in self._comments:
                self._comments[section_name] = {}
            self._comments[section_name][key] = comments
    
    def save_file(self, file_path: Path) -> None:
        """Save configuration to .ini file.
        
        Args:
            file_path: Path to save file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            for section_name in self._config.sections():
                # Write section comments
                if (section_name in self._comments and 
                    "__section__" in self._comments[section_name]):
                    for comment in self._comments[section_name]["__section__"]:
                        f.write(f"{comment}\n")
                
                # Write section header
                f.write(f"[{section_name}]\n")
                
                # Write key-value pairs
                for key in self._config.options(section_name):
                    # Write key comments
                    if (section_name in self._comments and 
                        key in self._comments[section_name]):
                        for comment in self._comments[section_name][key]:
                            f.write(f"{comment}\n")
                    
                    # Write key-value pair
                    value = self._config.get(section_name, key)
                    f.write(f"{key}={value}\n")
                
                # Add blank line between sections
                f.write("\n")


class ConfigMerger:
    """Merges multiple configuration files with proper precedence.
    
    Handles UE5 configuration hierarchy:
    1. Base defaults
    2. Engine configurations
    3. Project configurations
    4. User configurations
    5. Command-line overrides
    """
    
    def __init__(self):
        """Initialize merger."""
        self._configs: List[Dict[str, Any]] = []
        self._merged_config: Dict[str, Any] = {}
    
    def add_config(self, config: Dict[str, Any], priority: int = 0) -> None:
        """Add configuration to merge pool.
        
        Args:
            config: Configuration dictionary
            priority: Priority level (higher = overrides lower)
        """
        self._configs.append({
            "config": config,
            "priority": priority,
        })
    
    def merge(self) -> Dict[str, Any]:
        """Merge all configurations.
        
        Returns:
            Merged configuration dictionary
        """
        # Sort by priority (descending)
        sorted_configs = sorted(self._configs, key=lambda x: x["priority"], reverse=True)
        
        # Start with empty config
        merged = {}
        
        # Apply configurations from lowest to highest priority
        for item in reversed(sorted_configs):
            self._deep_merge(merged, item["config"])
        
        self._merged_config = merged
        return merged
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source into target.
        
        Args:
            target: Target dictionary
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._deep_merge(target[key], value)
            else:
                # Overwrite or add value
                target[key] = value
    
    def get_merged_value(self, key_path: str, default: Any = None) -> Any:
        """Get value from merged configuration using dot notation.
        
        Args:
            key_path: Dot-separated key path (e.g., "Engine.SystemSettings")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if not self._merged_config:
            self.merge()
        
        keys = key_path.split(".")
        current = self._merged_config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def validate_merged_config(self) -> List[str]:
        """Validate merged configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required UE5 configuration sections
        required_sections = ["Engine", "Core", "SystemSettings"]
        
        for section in required_sections:
            if section not in self._merged_config:
                errors.append(f"Missing required configuration section: {section}")
        
        # Validate engine version
        engine_config = self._merged_config.get("Engine", {})
        if "Version" not in engine_config:
            errors.append("Missing engine version in configuration")
        
        return errors


class ConfigValidator:
    """Validates UE5 configuration files and values."""
    
    # Common UE5 configuration patterns
    PATTERNS = {
        "engine_version": r"^\d+\.\d+\.\d+$",
        "module_name": r"^[A-Za-z_][A-Za-z0-9_]*$",
        "plugin_name": r"^[A-Za-z_][A-Za-z0-9_]*$",
        "boolean": r"^(true|false|True|False|0|1)$",
        "integer": r"^\d+$",
        "float": r"^\d+(\.\d+)?$",
        "path": r"^[A-Za-z]:\\\\.*$|^/.*$|^\./.*$",
    }
    
    def __init__(self):
        """Initialize validator."""
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    def validate_uproject(self, uproject_data: Dict[str, Any]) -> List[str]:
        """Validate .uproject configuration.
        
        Args:
            uproject_data: .uproject data dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = ["FileVersion", "EngineAssociation", "Category", "Description"]
        for field in required_fields:
            if field not in uproject_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate engine association
        engine_assoc = uproject_data.get("EngineAssociation", "")
        if not engine_assoc:
            errors.append("Empty engine association")
        elif not re.match(self.PATTERNS["engine_version"], engine_assoc):
            errors.append(f"Invalid engine association format: {engine_assoc}")
        
        # Validate modules
        modules = uproject_data.get("Modules", [])
        for i, module in enumerate(modules):
            module_name = module.get("Name", f"#{i}")
            
            if "Name" not in module:
                errors.append(f"Module {i} missing 'Name' field")
            elif not re.match(self.PATTERNS["module_name"], module["Name"]):
                errors.append(f"Invalid module name: {module['Name']}")
            
            if "Type" not in module:
                errors.append(f"Module {module_name} missing 'Type' field")
            else:
                valid_types = ["Runtime", "Editor", "Developer", "Program"]
                if module["Type"] not in valid_types:
                    errors.append(f"Module {module_name} has invalid type: {module['Type']}")
            
            if "LoadingPhase" not in module:
                errors.append(f"Module {module_name} missing 'LoadingPhase' field")
            else:
                valid_phases = ["Default", "PostConfigInit", "PreDefault", "PostEngineInit"]
                if module["LoadingPhase"] not in valid_phases:
                    errors.append(f"Module {module_name} has invalid LoadingPhase: {module['LoadingPhase']}")
        
        # Validate plugins
        plugins = uproject_data.get("Plugins", [])
        for i, plugin in enumerate(plugins):
            plugin_name = plugin.get("Name", f"#{i}")
            
            if "Name" not in plugin:
                errors.append(f"Plugin {i} missing 'Name' field")
            elif not re.match(self.PATTERNS["plugin_name"], plugin["Name"]):
                errors.append(f"Invalid plugin name: {plugin['Name']}")
        
        return errors
    
    def validate_ini_section(self, section: ConfigSection) -> List[str]:
        """Validate .ini configuration section.
        
        Args:
            section: ConfigSection object
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Platform-specific validation
        if section.type == ConfigSectionType.PLATFORM:
            errors.extend(self._validate_platform_section(section))
        
        # Engine-specific validation
        elif section.type == ConfigSectionType.ENGINE:
            errors.extend(self._validate_engine_section(section))
        
        # Editor-specific validation
        elif section.type == ConfigSectionType.EDITOR:
            errors.extend(self._validate_editor_section(section))
        
        return errors
    
    def _validate_platform_section(self, section: ConfigSection) -> List[str]:
        """Validate platform-specific configuration.
        
        Args:
            section: Platform configuration section
            
        Returns:
            List of validation errors
        """
        errors = []
        section_name = section.name.lower()
        
        # Common platform settings
        platform_keys = ["TargetPlatform", "BuildConfiguration", "ShaderModel"]
        
        for key in platform_keys:
            if key in section.values:
                value = section.values[key].value
                if not value:
                    errors.append(f"Platform {section_name}: {key} is empty")
        
        return errors
    
    def _validate_engine_section(self, section: ConfigSection) -> List[str]:
        """Validate engine configuration.
        
        Args:
            section: Engine configuration section
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for required engine settings
        required_keys = ["bUseFixedFrameRate", "MaxFPS", "MinDesiredFrameRate"]
        
        for key in required_keys:
            if key not in section.values:
                errors.append(f"Engine section missing required key: {key}")
            else:
                value = section.values[key].value
                if key in ["bUseFixedFrameRate"]:
                    if not re.match(self.PATTERNS["boolean"], str(value)):
                        errors.append(f"Engine.{key} must be boolean, got: {value}")
                elif key in ["MaxFPS", "MinDesiredFrameRate"]:
                    if not re.match(self.PATTERNS["integer"], str(value)):
                        errors.append(f"Engine.{key} must be integer, got: {value}")
        
        return errors
    
    def _validate_editor_section(self, section: ConfigSection) -> List[str]:
        """Validate editor configuration.
        
        Args:
            section: Editor configuration section
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for common editor settings
        common_keys = ["AutoSave", "AutoSaveInterval", "bEnableAutosave"]
        
        for key in common_keys:
            if key in section.values:
                value = section.values[key].value
                if key in ["AutoSaveInterval"]:
                    if not re.match(self.PATTERNS["integer"], str(value)):
                        errors.append(f"Editor.{key} must be integer, got: {value}")
                elif key in ["bEnableAutosave"]:
                    if not re.match(self.PATTERNS["boolean"], str(value)):
                        errors.append(f"Editor.{key} must be boolean, got: {value}")
        
        return errors
    
    def get_errors(self) -> List[str]:
        """Get all validation errors.
        
        Returns:
            List of error messages
        """
        return self._errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Get all validation warnings.
        
        Returns:
            List of warning messages
        """
        return self._warnings.copy()
    
    def clear(self) -> None:
        """Clear all errors and warnings."""
        self._errors.clear()
        self._warnings.clear()


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ParseError(ConfigError):
    """Exception for configuration parsing errors."""
    pass


class ValidationError(ConfigError):
    """Exception for configuration validation errors."""
    pass


class MergeError(ConfigError):
    """Exception for configuration merge errors."""
    pass