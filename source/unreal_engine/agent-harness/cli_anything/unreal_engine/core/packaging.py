"""Unreal Engine CLI - Packaging and deployment configuration module.

Handles packaging configurations, deployment options, and platform-specific settings
for UE5 project distribution. Supports multiple packaging formats and deployment targets.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class PackagingFormat(Enum):
    """UE5 packaging formats."""
    ZIP = "zip"
    INSTALLER = "installer"
    APP_BUNDLE = "appbundle"
    APK = "apk"
    IPA = "ipa"
    PKG = "pkg"
    DMG = "dmg"


class PackagingPlatform(Enum):
    """UE5 packaging platforms."""
    WINDOWS = "Windows"
    WINDOWS_SERVER = "WindowsServer"
    MAC = "Mac"
    LINUX = "Linux"
    ANDROID = "Android"
    IOS = "IOS"
    TVOS = "TVOS"
    PS5 = "PS5"
    XBOX_SERIES_X = "XboxSeriesX"


class CompressionLevel(Enum):
    """Compression levels for packaging."""
    NONE = "none"
    FAST = "fast"
    NORMAL = "normal"
    MAXIMUM = "maximum"


class DeploymentTarget(Enum):
    """Deployment targets for packaged builds."""
    LOCAL = "local"
    STEAM = "steam"
    EPIC_GAMES_STORE = "epic"
    ITCH_IO = "itch"
    GOOGLE_PLAY = "google_play"
    APP_STORE = "app_store"
    MICROSOFT_STORE = "microsoft_store"
    SELF_HOSTED = "self_hosted"


@dataclass
class PackagingConfig:
    """Configuration for UE5 project packaging.
    
    Attributes:
        project_path: Path to the .uproject file
        output_dir: Directory where packaged builds will be placed
        platform: Target platform for packaging
        configuration: Build configuration (Debug, Development, Shipping, etc.)
        format: Packaging format (zip, installer, etc.)
        compression: Compression level for packaged files
        include_debug_symbols: Whether to include debug symbols
        include_editor_content: Whether to include editor-only content
        strip_debug_info: Whether to strip debug information
        create_installer: Whether to create an installer
        installer_config: Configuration for installer creation
        deployment_targets: List of deployment targets
        custom_settings: Custom packaging settings
    """
    project_path: Path
    output_dir: Path = field(default_factory=lambda: Path("./Packaged"))
    platform: PackagingPlatform = PackagingPlatform.WINDOWS
    configuration: str = "Development"
    format: PackagingFormat = PackagingFormat.ZIP
    compression: CompressionLevel = CompressionLevel.NORMAL
    include_debug_symbols: bool = False
    include_editor_content: bool = False
    strip_debug_info: bool = False
    create_installer: bool = False
    installer_config: Optional[Dict[str, Any]] = None
    deployment_targets: List[DeploymentTarget] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "project_path": str(self.project_path),
            "output_dir": str(self.output_dir),
            "platform": self.platform.value,
            "configuration": self.configuration,
            "format": self.format.value,
            "compression": self.compression.value,
            "include_debug_symbols": self.include_debug_symbols,
            "include_editor_content": self.include_editor_content,
            "strip_debug_info": self.strip_debug_info,
            "create_installer": self.create_installer,
            "installer_config": self.installer_config or {},
            "deployment_targets": [target.value for target in self.deployment_targets],
            "custom_settings": self.custom_settings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PackagingConfig":
        """Create configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            PackagingConfig instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        required_fields = ["project_path"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Create configuration
        config = cls(
            project_path=Path(data["project_path"]),
            output_dir=Path(data.get("output_dir", "./Packaged")),
            platform=PackagingPlatform(data.get("platform", "Windows")),
            configuration=data.get("configuration", "Development"),
            format=PackagingFormat(data.get("format", "zip")),
            compression=CompressionLevel(data.get("compression", "normal")),
            include_debug_symbols=data.get("include_debug_symbols", False),
            include_editor_content=data.get("include_editor_content", False),
            strip_debug_info=data.get("strip_debug_info", False),
            create_installer=data.get("create_installer", False),
            installer_config=data.get("installer_config"),
            deployment_targets=[
                DeploymentTarget(target) for target in data.get("deployment_targets", [])
            ],
            custom_settings=data.get("custom_settings", {}),
        )
        
        return config
    
    def save(self, file_path: Path) -> None:
        """Save configuration to JSON file.
        
        Args:
            file_path: Path to save configuration file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: Path) -> "PackagingConfig":
        """Load configuration from JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            PackagingConfig instance
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration file is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls.from_dict(data)


class PlatformSpecificConfig:
    """Platform-specific packaging configuration.
    
    Provides platform-specific settings and validation for packaging.
    """
    
    # Platform-specific default settings
    PLATFORM_DEFAULTS: Dict[str, Dict[str, Any]] = {
        "Windows": {
            "executable_name": "{ProjectName}.exe",
            "icon_path": None,
            "require_admin": False,
            "create_shortcut": True,
        },
        "Mac": {
            "app_name": "{ProjectName}.app",
            "icon_path": None,
            "codesign": False,
            "notarize": False,
        },
        "Linux": {
            "executable_name": "{ProjectName}",
            "icon_path": None,
            "create_desktop_file": True,
            "install_prefix": "/usr/local",
        },
        "Android": {
            "package_name": "com.example.{project_name}",
            "version_code": 1,
            "version_name": "1.0.0",
            "orientation": "landscape",
            "permissions": [],
        },
        "IOS": {
            "bundle_identifier": "com.example.{ProjectName}",
            "version": "1.0.0",
            "build_number": 1,
            "orientation": "landscape",
            "provisioning_profile": None,
        },
    }
    
    @classmethod
    def get_defaults(cls, platform: PackagingPlatform) -> Dict[str, Any]:
        """Get default settings for a platform.
        
        Args:
            platform: Target platform
            
        Returns:
            Dictionary of default settings for the platform
        """
        return cls.PLATFORM_DEFAULTS.get(platform.value, {}).copy()
    
    @classmethod
    def validate_config(cls, platform: PackagingPlatform, config: Dict[str, Any]) -> List[str]:
        """Validate platform-specific configuration.
        
        Args:
            platform: Target platform
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if platform == PackagingPlatform.ANDROID:
            # Android-specific validation
            if "package_name" not in config:
                errors.append("Android packaging requires 'package_name'")
            if "version_code" not in config:
                errors.append("Android packaging requires 'version_code'")
            if "version_name" not in config:
                errors.append("Android packaging requires 'version_name'")
        
        elif platform == PackagingPlatform.IOS:
            # iOS-specific validation
            if "bundle_identifier" not in config:
                errors.append("iOS packaging requires 'bundle_identifier'")
            if "version" not in config:
                errors.append("iOS packaging requires 'version'")
            if "build_number" not in config:
                errors.append("iOS packaging requires 'build_number'")
        
        return errors


class PackagingManager:
    """Manager for UE5 project packaging operations.
    
    Handles packaging configuration, validation, and execution.
    """
    
    def __init__(self, engine_path: Path, project_path: Path):
        """Initialize packaging manager.
        
        Args:
            engine_path: Path to UE5 engine installation
            project_path: Path to .uproject file
        """
        self.engine_path = engine_path
        self.project_path = project_path
        self._uat_path = self._find_uat()
    
    def _find_uat(self) -> Path:
        """Find UAT (Unreal Automation Tool) executable.
        
        Returns:
            Path to UAT executable
            
        Raises:
            FileNotFoundError: If UAT executable not found
        """
        # Look for UAT in standard locations
        uat_paths = [
            self.engine_path / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat",
            self.engine_path / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh",
        ]
        
        for path in uat_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError(f"UAT executable not found in engine path: {self.engine_path}")
    
    def create_packaging_config(
        self,
        platform: PackagingPlatform,
        configuration: str = "Development",
        **kwargs
    ) -> PackagingConfig:
        """Create a packaging configuration.
        
        Args:
            platform: Target platform
            configuration: Build configuration
            **kwargs: Additional configuration options
            
        Returns:
            PackagingConfig instance
        """
        # Get platform-specific defaults
        platform_defaults = PlatformSpecificConfig.get_defaults(platform)
        
        # Merge defaults with provided kwargs
        custom_settings = platform_defaults.copy()
        custom_settings.update(kwargs.get("custom_settings", {}))
        
        # Create configuration
        config = PackagingConfig(
            project_path=self.project_path,
            platform=platform,
            configuration=configuration,
            custom_settings=custom_settings,
            **{k: v for k, v in kwargs.items() if k != "custom_settings"}
        )
        
        return config
    
    def validate_config(self, config: PackagingConfig) -> List[str]:
        """Validate packaging configuration.
        
        Args:
            config: Packaging configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate project file exists
        if not config.project_path.exists():
            errors.append(f"Project file not found: {config.project_path}")
        
        # Validate platform-specific configuration
        platform_errors = PlatformSpecificConfig.validate_config(
            config.platform, config.custom_settings
        )
        errors.extend(platform_errors)
        
        # Validate output directory can be created
        try:
            config.output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            errors.append(f"Cannot create output directory: {e}")
        
        # Validate configuration
        valid_configurations = ["Debug", "DebugGame", "Development", "Test", "Shipping"]
        if config.configuration not in valid_configurations:
            errors.append(f"Invalid configuration: {config.configuration}. "
                         f"Must be one of: {', '.join(valid_configurations)}")
        
        return errors
    
    def package_project(self, config: PackagingConfig) -> Path:
        """Package UE5 project using UAT.
        
        Args:
            config: Packaging configuration
            
        Returns:
            Path to packaged output
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If packaging fails
        """
        # Validate configuration
        errors = self.validate_config(config)
        if errors:
            raise ValueError(f"Invalid packaging configuration: {', '.join(errors)}")
        
        # Prepare UAT command
        cmd = self._build_uat_command(config)
        
        try:
            # Execute UAT command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.engine_path.parent if os.name == "nt" else self.engine_path
            )
            
            # Find packaged output
            output_path = self._find_packaged_output(config)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Packaging failed: {e.stderr}")
    
    def _build_uat_command(self, config: PackagingConfig) -> List[str]:
        """Build UAT command for packaging.
        
        Args:
            config: Packaging configuration
            
        Returns:
            List of command arguments
        """
        cmd = [str(self._uat_path)]
        
        # Add packaging command
        cmd.append("BuildCookRun")
        
        # Add project parameters
        cmd.extend([
            f"-project={config.project_path}",
            f"-platform={config.platform.value}",
            f"-clientconfig={config.configuration}",
            f"-cook",
            f"-stage",
            f"-package",
            f"-pak",
            f"-prereqs",
            f"-archive",
            f"-archivedirectory={config.output_dir}",
        ])
        
        # Add compression
        if config.compression != CompressionLevel.NONE:
            cmd.append(f"-compressed")
        
        # Add debug symbols
        if config.include_debug_symbols:
            cmd.append("-debuginfo")
        
        # Add editor content
        if config.include_editor_content:
            cmd.append("-includeeditorcontent")
        
        # Add strip debug info
        if config.strip_debug_info:
            cmd.append("-nodebuginfo")
        
        # Add custom settings
        for key, value in config.custom_settings.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"-{key}")
            elif isinstance(value, list):
                for item in value:
                    cmd.append(f"-{key}={item}")
            else:
                cmd.append(f"-{key}={value}")
        
        return cmd
    
    def _find_packaged_output(self, config: PackagingConfig) -> Path:
        """Find packaged output directory.
        
        Args:
            config: Packaging configuration
            
        Returns:
            Path to packaged output
            
        Raises:
            FileNotFoundError: If packaged output not found
        """
        # Look for packaged output in expected locations
        project_name = config.project_path.stem
        
        # Check for platform-specific output directories
        possible_paths = [
            config.output_dir / f"{project_name}" / config.platform.value,
            config.output_dir / config.platform.value / project_name,
            config.output_dir / f"{project_name}-{config.platform.value}",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Check for any directory in output directory
        for item in config.output_dir.iterdir():
            if item.is_dir() and project_name in item.name:
                return item
        
        raise FileNotFoundError(f"Packaged output not found in: {config.output_dir}")
    
    def create_installer(self, config: PackagingConfig, installer_config: Dict[str, Any]) -> Path:
        """Create installer for packaged build.
        
        Args:
            config: Packaging configuration
            installer_config: Installer-specific configuration
            
        Returns:
            Path to installer file
            
        Raises:
            NotImplementedError: If installer creation not supported for platform
        """
        if not config.create_installer:
            raise ValueError("Installer creation not enabled in configuration")
        
        # Platform-specific installer creation
        if config.platform == PackagingPlatform.WINDOWS:
            return self._create_windows_installer(config, installer_config)
        elif config.platform == PackagingPlatform.MAC:
            return self._create_mac_installer(config, installer_config)
        elif config.platform == PackagingPlatform.LINUX:
            return self._create_linux_installer(config, installer_config)
        else:
            raise NotImplementedError(
                f"Installer creation not supported for platform: {config.platform}"
            )
    
    def _create_windows_installer(self, config: PackagingConfig, installer_config: Dict[str, Any]) -> Path:
        """Create Windows installer.
        
        Args:
            config: Packaging configuration
            installer_config: Installer-specific configuration
            
        Returns:
            Path to installer file
        """
        # This is a placeholder - actual implementation would use NSIS, Inno Setup, etc.
        project_name = config.project_path.stem
        installer_path = config.output_dir / f"{project_name}-Setup.exe"
        
        # Create a simple batch file as placeholder
        batch_content = f"""@echo off
echo Installing {project_name}...
echo This is a placeholder installer.
pause
"""
        
        with open(installer_path, "w") as f:
            f.write(batch_content)
        
        return installer_path
    
    def _create_mac_installer(self, config: PackagingConfig, installer_config: Dict[str, Any]) -> Path:
        """Create macOS installer.
        
        Args:
            config: Packaging configuration
            installer_config: Installer-specific configuration
            
        Returns:
            Path to installer file
        """
        # This is a placeholder - actual implementation would use pkgbuild/productbuild
        project_name = config.project_path.stem
        installer_path = config.output_dir / f"{project_name}.pkg"
        
        # Create a simple script as placeholder
        script_content = f"""#!/bin/bash
echo "Installing {project_name}..."
echo "This is a placeholder installer."
"""
        
        with open(installer_path, "w") as f:
            f.write(script_content)
        
        # Make script executable
        installer_path.chmod(0o755)
        
        return installer_path
    
    def _create_linux_installer(self, config: PackagingConfig, installer_config: Dict[str, Any]) -> Path:
        """Create Linux installer.
        
        Args:
            config: Packaging configuration
            installer_config: Installer-specific configuration
            
        Returns:
            Path to installer file
        """
        # This is a placeholder - actual implementation would use makeself, dpkg, etc.
        project_name = config.project_path.stem
        installer_path = config.output_dir / f"{project_name}.sh"
        
        # Create a simple self-extracting script as placeholder
        script_content = f"""#!/bin/bash
echo "Installing {project_name}..."
echo "This is a placeholder installer."
"""
        
        with open(installer_path, "w") as f:
            f.write(script_content)
        
        # Make script executable
        installer_path.chmod(0o755)
        
        return installer_path
    
    def deploy_package(self, config: PackagingConfig, target: DeploymentTarget) -> bool:
        """Deploy packaged build to target.
        
        Args:
            config: Packaging configuration
            target: Deployment target
            
        Returns:
            True if deployment successful, False otherwise
        """
        if target not in config.deployment_targets:
            raise ValueError(f"Target {target} not in deployment targets")
        
        try:
            # Find packaged output
            packaged_path = self._find_packaged_output(config)
            
            # Platform-specific deployment
            if target == DeploymentTarget.LOCAL:
                return self._deploy_local(packaged_path)
            elif target == DeploymentTarget.STEAM:
                return self._deploy_steam(packaged_path, config)
            elif target == DeploymentTarget.EPIC_GAMES_STORE:
                return self._deploy_epic(packaged_path, config)
            elif target == DeploymentTarget.ITCH_IO:
                return self._deploy_itch(packaged_path, config)
            elif target == DeploymentTarget.GOOGLE_PLAY:
                return self._deploy_google_play(packaged_path, config)
            elif target == DeploymentTarget.APP_STORE:
                return self._deploy_app_store(packaged_path, config)
            elif target == DeploymentTarget.MICROSOFT_STORE:
                return self._deploy_microsoft_store(packaged_path, config)
            elif target == DeploymentTarget.SELF_HOSTED:
                return self._deploy_self_hosted(packaged_path, config)
            else:
                raise NotImplementedError(f"Deployment target not implemented: {target}")
                
        except Exception as e:
            print(f"Deployment failed: {e}")
            return False
    
    def _deploy_local(self, packaged_path: Path) -> bool:
        """Deploy to local directory.
        
        Args:
            packaged_path: Path to packaged build
            
        Returns:
            True if successful
        """
        # Local deployment just verifies the package exists
        return packaged_path.exists()
    
    def _deploy_steam(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to Steam.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use Steamworks SDK
        print(f"Would deploy to Steam: {packaged_path}")
        return True
    
    def _deploy_epic(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to Epic Games Store.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use Epic Games Store tools
        print(f"Would deploy to Epic Games Store: {packaged_path}")
        return True
    
    def _deploy_itch(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to itch.io.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use itch.io butler
        print(f"Would deploy to itch.io: {packaged_path}")
        return True
    
    def _deploy_google_play(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to Google Play.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use Google Play Developer API
        print(f"Would deploy to Google Play: {packaged_path}")
        return True
    
    def _deploy_app_store(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to Apple App Store.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use Apple Transporter
        print(f"Would deploy to App Store: {packaged_path}")
        return True
    
    def _deploy_microsoft_store(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to Microsoft Store.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use Microsoft Partner Center
        print(f"Would deploy to Microsoft Store: {packaged_path}")
        return True
    
    def _deploy_self_hosted(self, packaged_path: Path, config: PackagingConfig) -> bool:
        """Deploy to self-hosted server.
        
        Args:
            packaged_path: Path to packaged build
            config: Packaging configuration
            
        Returns:
            True if successful
        """
        # Placeholder - actual implementation would use FTP, SCP, etc.
        print(f"Would deploy to self-hosted server: {packaged_path}")
        return True


class PackagingError(Exception):
    """Base exception for packaging errors."""
    pass


class ConfigurationError(PackagingError):
    """Exception for configuration errors."""
    pass


class PackagingFailedError(PackagingError):
    """Exception for packaging process failures."""
    pass


class DeploymentError(PackagingError):
    """Exception for deployment failures."""
    pass