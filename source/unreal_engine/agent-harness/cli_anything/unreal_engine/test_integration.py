#!/usr/bin/env python3
"""Unreal Engine CLI - Integration Tests.

This module provides integration tests for the Unreal Engine CLI,
testing the interaction between different modules and the complete
workflow from project creation to packaging.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, Mock

import pytest
import click
from click.testing import CliRunner

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the CLI and core modules
try:
    from unreal_engine_cli import UE5CLI, OutputFormat
    from core.project import (
        create_project,
        open_project,
        save_project,
        get_project_info,
        ProjectNotFoundError,
    )
    from core.build import BuildSystem
    from core.editor import EditorManager
    from core.asset import AssetManager
    from core.plugin import PluginManager
    from core.blueprint import BlueprintManager
    from core.level import LevelManager
    from core.packaging import PackagingManager
    from core.session import SessionManager
    from core.cook import CookManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Current sys.path:", sys.path)
    raise


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="ue_cli_test_")
        self.project_name = "TestIntegrationProject"
        self.project_path = Path(self.test_dir) / f"{self.project_name}.uproject"
        
        # Create CLI instance
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_project_creation_workflow(self) -> None:
        """Test complete project creation workflow."""
        # Test 1: Create project
        project_config = create_project(
            name=self.project_name,
            engine_version="5.4.0",
            description="Integration test project",
            category="Test",
            created_by="TestSuite"
        )
        
        # Save project file
        with open(self.project_path, "w", encoding="utf-8") as f:
            json.dump(project_config, f, indent=4)
        
        # Verify project file exists
        assert self.project_path.exists()
        
        # Test 2: Open and validate project
        opened_project = open_project(str(self.project_path))
        assert opened_project["Name"] == self.project_name
        assert opened_project["EngineAssociation"] == "5.4.0"
        
        # Test 3: Get project info
        project_info = get_project_info(str(self.project_path))
        assert project_info["name"] == self.project_name
        assert project_info["engine_version"] == "5.4.0"
        assert project_info["description"] == "Integration test project"
    
    def test_cli_project_commands_integration(self) -> None:
        """Test CLI project commands integration."""
        # Mock the project manager to avoid actual file system operations
        with patch.object(self.cli.project_manager, 'create_project') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "project_path": str(self.project_path),
                "project_name": self.project_name
            }
            
            # Test project create command
            result = self.runner.invoke(
                self.cli,
                ["project", "create", self.project_name],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            mock_create.assert_called_once_with(
                name=self.project_name,
                template=None,
                output_dir=None,
                engine_version=None
            )
    
    def test_asset_and_blueprint_integration(self) -> None:
        """Test asset import and blueprint creation integration."""
        # Create a test asset file
        test_asset_dir = Path(self.test_dir) / "Assets"
        test_asset_dir.mkdir(exist_ok=True)
        test_asset_file = test_asset_dir / "test_texture.png"
        test_asset_file.write_bytes(b"fake_png_data")
        
        # Mock asset manager
        with patch.object(self.cli.asset_manager, 'import_asset') as mock_import:
            mock_import.return_value = {
                "status": "success",
                "asset_path": "/Game/Test/TestTexture",
                "imported_files": [str(test_asset_file)]
            }
            
            # Mock blueprint manager
            with patch.object(self.cli.blueprint_manager, 'create_blueprint') as mock_bp:
                mock_bp.return_value = {
                    "status": "success",
                    "blueprint_path": "/Game/Blueprints/TestBlueprint",
                    "blueprint_type": "Actor"
                }
                
                # Test asset import
                result_asset = self.runner.invoke(
                    self.cli,
                    ["asset", "import", str(test_asset_file), "/Game/Test/TestTexture"],
                    obj=self.cli
                )
                
                assert result_asset.exit_code == 0
                mock_import.assert_called_once()
                
                # Test blueprint creation
                result_bp = self.runner.invoke(
                    self.cli,
                    ["blueprint", "create", "TestBlueprint", "--type", "Actor"],
                    obj=self.cli
                )
                
                assert result_bp.exit_code == 0
                mock_bp.assert_called_once()
    
    def test_plugin_installation_and_enablement(self) -> None:
        """Test plugin installation and enablement workflow."""
        # Create a test plugin directory
        test_plugin_dir = Path(self.test_dir) / "TestPlugin"
        test_plugin_dir.mkdir(exist_ok=True)
        
        # Create plugin descriptor
        plugin_descriptor = {
            "FileVersion": 3,
            "Version": 1,
            "VersionName": "1.0",
            "FriendlyName": "Test Plugin",
            "Description": "Test plugin for integration tests",
            "Category": "Other",
            "CreatedBy": "TestSuite",
            "CreatedByURL": "",
            "DocsURL": "",
            "MarketplaceURL": "",
            "SupportURL": "",
            "EnabledByDefault": False,
            "CanContainContent": True,
            "IsBetaVersion": False,
            "Installed": False,
            "Modules": [
                {
                    "Name": "TestPlugin",
                    "Type": "Runtime",
                    "LoadingPhase": "Default"
                }
            ]
        }
        
        plugin_file = test_plugin_dir / "TestPlugin.uplugin"
        with open(plugin_file, "w", encoding="utf-8") as f:
            json.dump(plugin_descriptor, f, indent=4)
        
        # Mock plugin manager
        with patch.object(self.cli.plugin_manager, 'install_plugin') as mock_install:
            mock_install.return_value = {
                "status": "success",
                "plugin_name": "TestPlugin",
                "plugin_path": str(plugin_file)
            }
            
            with patch.object(self.cli.plugin_manager, 'enable_plugin') as mock_enable:
                mock_enable.return_value = {
                    "status": "success",
                    "plugin_name": "TestPlugin",
                    "enabled": True
                }
                
                # Test plugin installation
                result_install = self.runner.invoke(
                    self.cli,
                    ["plugin", "install", str(plugin_file)],
                    obj=self.cli
                )
                
                assert result_install.exit_code == 0
                mock_install.assert_called_once()
                
                # Test plugin enablement
                result_enable = self.runner.invoke(
                    self.cli,
                    ["plugin", "enable", "TestPlugin"],
                    obj=self.cli
                )
                
                assert result_enable.exit_code == 0
                mock_enable.assert_called_once()
    
    def test_build_and_package_workflow(self) -> None:
        """Test build and package workflow integration."""
        # Mock build system
        with patch.object(self.cli.build_system, 'compile') as mock_compile:
            mock_compile.return_value = {
                "status": "success",
                "build_time": 120.5,
                "output_path": str(self.test_dir / "Build"),
                "errors": [],
                "warnings": []
            }
            
            # Mock packaging manager
            with patch.object(self.cli.packaging_manager, 'package_project') as mock_package:
                mock_package.return_value = {
                    "status": "success",
                    "package_path": str(self.test_dir / "Package"),
                    "package_size": 1024 * 1024 * 100,  # 100MB
                    "platform": "Win64",
                    "configuration": "Shipping"
                }
                
                # Test build compilation
                result_build = self.runner.invoke(
                    self.cli,
                    ["build", "compile", "--target", "Editor", "--platform", "Win64"],
                    obj=self.cli
                )
                
                assert result_build.exit_code == 0
                mock_compile.assert_called_once()
                
                # Test packaging
                result_package = self.runner.invoke(
                    self.cli,
                    ["package", "build", "--platform", "Win64", "--configuration", "Shipping"],
                    obj=self.cli
                )
                
                assert result_package.exit_code == 0
                mock_package.assert_called_once()
    
    def test_editor_session_management(self) -> None:
        """Test editor session management integration."""
        # Mock editor manager
        with patch.object(self.cli.editor_manager, 'launch') as mock_launch:
            mock_launch.return_value = {
                "status": "success",
                "editor_pid": 12345,
                "session_id": "test_session_001"
            }
            
            # Mock session manager
            with patch.object(self.cli.session_manager, 'start_session') as mock_start:
                mock_start.return_value = {
                    "status": "success",
                    "session_id": "test_session_001",
                    "start_time": time.time()
                }
                
                # Test editor launch
                result_launch = self.runner.invoke(
                    self.cli,
                    ["editor", "launch", "--headless"],
                    obj=self.cli
                )
                
                assert result_launch.exit_code == 0
                mock_launch.assert_called_once()
                
                # Test session start
                result_session = self.runner.invoke(
                    self.cli,
                    ["session", "--start"],
                    obj=self.cli
                )
                
                assert result_session.exit_code == 0
                mock_start.assert_called_once()
    
    def test_level_creation_and_management(self) -> None:
        """Test level creation and management integration."""
        # Mock level manager
        with patch.object(self.cli.level_manager, 'create_level') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "level_name": "TestLevel",
                "level_path": "/Game/Maps/TestLevel",
                "template": "Default"
            }
            
            with patch.object(self.cli.level_manager, 'list_levels') as mock_list:
                mock_list.return_value = {
                    "status": "success",
                    "levels": [
                        {"name": "TestLevel", "path": "/Game/Maps/TestLevel"},
                        {"name": "PersistentLevel", "path": "/Game/Maps/PersistentLevel"}
                    ]
                }
                
                # Test level creation
                result_create = self.runner.invoke(
                    self.cli,
                    ["level", "create", "TestLevel"],
                    obj=self.cli
                )
                
                assert result_create.exit_code == 0
                mock_create.assert_called_once()
                
                # Test level listing
                result_list = self.runner.invoke(
                    self.cli,
                    ["level", "list"],
                    obj=self.cli
                )
                
                assert result_list.exit_code == 0
                mock_list.assert_called_once()
    
    def test_cooking_workflow(self) -> None:
        """Test content cooking workflow."""
        # Mock cook manager
        with patch.object(self.cli.cook_manager, 'cook_content') as mock_cook:
            mock_cook.return_value = {
                "status": "success",
                "cooked_content_path": str(self.test_dir / "Cooked"),
                "platform": "Win64",
                "cooking_time": 300.5,
                "cooked_assets": 1500
            }
            
            # Test cooking
            result = self.runner.invoke(
                self.cli,
                ["cook", "content", "--platform", "Win64", "--maps", "TestLevel,PersistentLevel"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            mock_cook.assert_called_once()


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def test_project_not_found_error(self) -> None:
        """Test error handling when project is not found."""
        non_existent_path = "/non/existent/project.uproject"
        
        with patch.object(self.cli.project_manager, 'open_project') as mock_open:
            mock_open.side_effect = ProjectNotFoundError(f"Project not found: {non_existent_path}")
            
            result = self.runner.invoke(
                self.cli,
                ["project", "open", non_existent_path],
                obj=self.cli
            )
            
            assert result.exit_code == 1
            assert "Error opening project" in result.output
    
    def test_build_failure_error(self) -> None:
        """Test error handling when build fails."""
        with patch.object(self.cli.build_system, 'compile') as mock_compile:
            mock_compile.side_effect = Exception("Build failed: Compilation errors")
            
            result = self.runner.invoke(
                self.cli,
                ["build", "compile"],
                obj=self.cli
            )
            
            assert result.exit_code == 1
            assert "Error compiling project" in result.output
    
    def test_asset_import_error(self) -> None:
        """Test error handling when asset import fails."""
        non_existent_asset = "/non/existent/asset.png"
        
        with patch.object(self.cli.asset_manager, 'import_asset') as mock_import:
            mock_import.side_effect = Exception(f"Asset not found: {non_existent_asset}")
            
            result = self.runner.invoke(
                self.cli,
                ["asset", "import", non_existent_asset, "/Game/Test/Asset"],
                obj=self.cli
            )
            
            assert result.exit_code == 1
            assert "Error importing asset" in result.output


class TestConfigurationIntegration:
    """Integration tests for configuration management."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def test_config_show_and_update(self) -> None:
        """Test configuration show and update commands."""
        # Test config show
        result_show = self.runner.invoke(
            self.cli,
            ["config", "show"],
            obj=self.cli
        )
        
        assert result_show.exit_code == 0
        assert "default_engine_path" in result_show.output
        assert "output_format" in result_show.output
        
        # Test config update
        result_update = self.runner.invoke(
            self.cli,
            ["config", "update", "--output-format", "json"],
            obj=self.cli
        )
        
        assert result_update.exit_code == 0
        assert "Configuration updated" in result_update.output


class TestREPLIntegration:
    """Integration tests for REPL mode."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def test_repl_mode_launch(self) -> None:
        """Test REPL mode launch."""
        # Mock REPL skin to avoid actual REPL launch
        with patch('unreal_engine_cli.REPLSkin') as mock_repl:
            mock_instance = MagicMock()
            mock_instance.run.return_value = None
            mock_repl.return_value = mock_instance
            
            result = self.runner.invoke(
                self.cli,
                ["repl"],
                obj=self.cli,
                input="exit\n"  # Exit immediately
            )
            
            assert result.exit_code == 0
            mock_repl.assert_called_once()


if __name__ == "__main__":
    """Run integration tests directly."""
    pytest.main([__file__, "-v"])