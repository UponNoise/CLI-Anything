#!/usr/bin/env python3
"""Unreal Engine CLI - End-to-End Tests.

This module provides end-to-end tests for the Unreal Engine CLI,
simulating real user scenarios and complete workflows.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
import sys
import tempfile
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, Mock, call

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


class TestCompleteUserWorkflow:
    """End-to-end tests simulating complete user workflows."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="ue_cli_e2e_")
        self.project_name = "TestE2EProject"
        self.project_path = Path(self.test_dir) / f"{self.project_name}.uproject"
        
        # Create CLI instance
        self.cli = UE5CLI()
        self.runner = CliRunner()
        
        # Create a mock project file for testing
        self._create_mock_project()
    
    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_mock_project(self) -> None:
        """Create a mock project file for testing."""
        project_config = {
            "FileVersion": 3,
            "EngineAssociation": "5.4.0",
            "Category": "",
            "Description": "End-to-end test project",
            "Modules": [
                {
                    "Name": self.project_name,
                    "Type": "Runtime",
                    "LoadingPhase": "Default",
                    "AdditionalDependencies": []
                }
            ],
            "Plugins": [],
            "TargetPlatforms": ["Win64"],
            "EpicSampleBaseHash": "",
            "ProjectId": "{00000000-0000-0000-0000-000000000000}",
            "EngineDirectory": "",
            "ProjectDirectory": str(self.test_dir),
            "Name": self.project_name
        }
        
        with open(self.project_path, "w", encoding="utf-8") as f:
            json.dump(project_config, f, indent=4)
    
    def test_complete_project_lifecycle(self) -> None:
        """Test complete project lifecycle from creation to packaging."""
        print("\n=== Testing Complete Project Lifecycle ===")
        
        # Step 1: Create project
        print("Step 1: Creating project...")
        with patch.object(self.cli.project_manager, 'create_project') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "project_path": str(self.project_path),
                "project_name": self.project_name,
                "engine_version": "5.4.0"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["project", "create", self.project_name, "--engine-version", "5.4.0"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            assert "success" in result.output.lower()
            print("✓ Project creation successful")
        
        # Step 2: Open project
        print("Step 2: Opening project...")
        with patch.object(self.cli.project_manager, 'open_project') as mock_open:
            mock_open.return_value = {
                "status": "success",
                "project_info": {
                    "name": self.project_name,
                    "path": str(self.project_path),
                    "engine_version": "5.4.0"
                }
            }
            
            result = self.runner.invoke(
                self.cli,
                ["project", "open", str(self.project_path)],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Project opening successful")
        
        # Step 3: Import assets
        print("Step 3: Importing assets...")
        test_asset = Path(self.test_dir) / "test_asset.fbx"
        test_asset.write_bytes(b"fake_fbx_data")
        
        with patch.object(self.cli.asset_manager, 'import_asset') as mock_import:
            mock_import.return_value = {
                "status": "success",
                "imported_assets": [str(test_asset)],
                "destination_path": "/Game/Assets/TestAsset"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["asset", "import", str(test_asset), "/Game/Assets/TestAsset"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Asset import successful")
        
        # Step 4: Create blueprint
        print("Step 4: Creating blueprint...")
        with patch.object(self.cli.blueprint_manager, 'create_blueprint') as mock_bp:
            mock_bp.return_value = {
                "status": "success",
                "blueprint_path": "/Game/Blueprints/TestActor",
                "blueprint_type": "Actor"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["blueprint", "create", "TestActor", "--type", "Actor"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Blueprint creation successful")
        
        # Step 5: Create level
        print("Step 5: Creating level...")
        with patch.object(self.cli.level_manager, 'create_level') as mock_level:
            mock_level.return_value = {
                "status": "success",
                "level_path": "/Game/Maps/TestLevel",
                "level_name": "TestLevel"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["level", "create", "TestLevel"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Level creation successful")
        
        # Step 6: Build project
        print("Step 6: Building project...")
        with patch.object(self.cli.build_system, 'compile') as mock_build:
            mock_build.return_value = {
                "status": "success",
                "build_time": 180.5,
                "output_directory": str(Path(self.test_dir) / "Build"),
                "errors": [],
                "warnings": []
            }
            
            result = self.runner.invoke(
                self.cli,
                ["build", "compile", "--target", "Editor", "--platform", "Win64"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Build successful")
        
        # Step 7: Cook content
        print("Step 7: Cooking content...")
        with patch.object(self.cli.cook_manager, 'cook_content') as mock_cook:
            mock_cook.return_value = {
                "status": "success",
                "cooking_time": 300.2,
                "cooked_assets": 1250,
                "output_directory": str(Path(self.test_dir) / "Cooked")
            }
            
            result = self.runner.invoke(
                self.cli,
                ["cook", "content", "--platform", "Win64", "--maps", "TestLevel"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Cooking successful")
        
        # Step 8: Package project
        print("Step 8: Packaging project...")
        with patch.object(self.cli.packaging_manager, 'package_project') as mock_package:
            mock_package.return_value = {
                "status": "success",
                "package_path": str(Path(self.test_dir) / "Package" / f"{self.project_name}.zip"),
                "package_size": 1024 * 1024 * 250,  # 250MB
                "platform": "Win64",
                "configuration": "Shipping"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["package", "build", "--platform", "Win64", "--configuration", "Shipping"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Packaging successful")
        
        print("✓ Complete project lifecycle test passed!")
    
    def test_user_interactive_scenario(self) -> None:
        """Test interactive user scenario with multiple commands."""
        print("\n=== Testing Interactive User Scenario ===")
        
        # Simulate a user session with multiple commands
        commands = [
            # Check CLI version
            ["version"],
            
            # Show status
            ["status"],
            
            # Create a project
            ["project", "create", "MyGame", "--engine-version", "5.4.0"],
            
            # List projects
            ["project", "list"],
            
            # Import some assets
            ["asset", "import", "/path/to/model.fbx", "/Game/Models/Character"],
            
            # Create a blueprint
            ["blueprint", "create", "PlayerCharacter", "--type", "Character"],
            
            # Create a level
            ["level", "create", "MainLevel"],
            
            # Build the project
            ["build", "compile"],
            
            # Show build status
            ["build", "status"],
            
            # Package the project
            ["package", "build"],
            
            # Show configuration
            ["config", "show"],
        ]
        
        # Mock all the managers
        with patch.multiple(
            self.cli,
            project_manager=Mock(),
            asset_manager=Mock(),
            blueprint_manager=Mock(),
            level_manager=Mock(),
            build_system=Mock(),
            packaging_manager=Mock()
        ):
            # Set up mock returns
            self.cli.project_manager.create_project.return_value = {
                "status": "success",
                "project_name": "MyGame"
            }
            self.cli.project_manager.list_projects.return_value = {
                "projects": ["MyGame", "TestProject"]
            }
            self.cli.asset_manager.import_asset.return_value = {
                "status": "success",
                "imported_asset": "Character"
            }
            self.cli.blueprint_manager.create_blueprint.return_value = {
                "status": "success",
                "blueprint_name": "PlayerCharacter"
            }
            self.cli.level_manager.create_level.return_value = {
                "status": "success",
                "level_name": "MainLevel"
            }
            self.cli.build_system.compile.return_value = {
                "status": "success",
                "build_time": 150.5
            }
            self.cli.build_system.get_build_status.return_value = {
                "status": "completed",
                "last_build_time": "2026-03-15 10:30:00"
            }
            self.cli.packaging_manager.package_project.return_value = {
                "status": "success",
                "package_size": "250MB"
            }
            
            # Execute all commands
            for cmd in commands:
                print(f"Executing: {' '.join(cmd)}")
                result = self.runner.invoke(
                    self.cli,
                    cmd,
                    obj=self.cli
                )
                
                assert result.exit_code == 0, f"Command failed: {' '.join(cmd)}\n{result.output}"
                print(f"✓ Command successful")
        
        print("✓ Interactive user scenario test passed!")
    
    def test_error_recovery_scenario(self) -> None:
        """Test error handling and recovery scenarios."""
        print("\n=== Testing Error Recovery Scenario ===")
        
        # Scenario: User tries to open non-existent project, then creates it
        
        # Step 1: Try to open non-existent project (should fail)
        print("Step 1: Attempting to open non-existent project...")
        non_existent_path = "/non/existent/project.uproject"
        
        with patch.object(self.cli.project_manager, 'open_project') as mock_open:
            mock_open.side_effect = ProjectNotFoundError("Project not found")
            
            result = self.runner.invoke(
                self.cli,
                ["project", "open", non_existent_path],
                obj=self.cli
            )
            
            assert result.exit_code == 1
            assert "Error opening project" in result.output
            print("✓ Correctly failed to open non-existent project")
        
        # Step 2: Create the project
        print("Step 2: Creating the project...")
        with patch.object(self.cli.project_manager, 'create_project') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "project_path": str(self.project_path)
            }
            
            result = self.runner.invoke(
                self.cli,
                ["project", "create", "RecoveryTest"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Project creation successful after error")
        
        # Step 3: Try to import non-existent asset (should fail)
        print("Step 3: Attempting to import non-existent asset...")
        non_existent_asset = "/non/existent/asset.fbx"
        
        with patch.object(self.cli.asset_manager, 'import_asset') as mock_import:
            mock_import.side_effect = FileNotFoundError("Asset file not found")
            
            result = self.runner.invoke(
                self.cli,
                ["asset", "import", non_existent_asset, "/Game/Test"],
                obj=self.cli
            )
            
            assert result.exit_code == 1
            assert "Error importing asset" in result.output
            print("✓ Correctly failed to import non-existent asset")
        
        # Step 4: Create asset and try again (should succeed)
        print("Step 4: Creating test asset and importing...")
        test_asset = Path(self.test_dir) / "recovery_asset.fbx"
        test_asset.write_bytes(b"test_fbx_data")
        
        with patch.object(self.cli.asset_manager, 'import_asset') as mock_import:
            mock_import.return_value = {
                "status": "success",
                "imported_asset": "recovery_asset"
            }
            
            result = self.runner.invoke(
                self.cli,
                ["asset", "import", str(test_asset), "/Game/Recovery"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            print("✓ Asset import successful after error recovery")
        
        print("✓ Error recovery scenario test passed!")
    
    def test_performance_and_stability(self) -> None:
        """Test performance and stability with multiple operations."""
        print("\n=== Testing Performance and Stability ===")
        
        # Test multiple rapid operations
        operations = 10
        start_time = time.time()
        
        with patch.multiple(
            self.cli,
            project_manager=Mock(),
            asset_manager=Mock(),
            blueprint_manager=Mock(),
            build_system=Mock()
        ):
            # Configure mocks
            self.cli.project_manager.create_project.return_value = {
                "status": "success",
                "project_name": "PerfTest"
            }
            self.cli.asset_manager.import_asset.return_value = {
                "status": "success",
                "imported_asset": "TestAsset"
            }
            self.cli.blueprint_manager.create_blueprint.return_value = {
                "status": "success",
                "blueprint_name": "TestBlueprint"
            }
            self.cli.build_system.compile.return_value = {
                "status": "success",
                "build_time": 100.0
            }
            
            # Execute multiple operations
            for i in range(operations):
                # Alternate between different commands
                if i % 3 == 0:
                    cmd = ["project", "create", f"TestProject_{i}"]
                elif i % 3 == 1:
                    cmd = ["asset", "import", f"/path/to/asset_{i}.fbx", f"/Game/Assets/Asset_{i}"]
                else:
                    cmd = ["blueprint", "create", f"Blueprint_{i}", "--type", "Actor"]
                
                result = self.runner.invoke(
                    self.cli,
                    cmd,
                    obj=self.cli
                )
                
                assert result.exit_code == 0, f"Operation {i} failed: {result.output}"
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"Executed {operations} operations in {total_time:.2f} seconds")
            print(f"Average time per operation: {total_time/operations:.3f} seconds")
            
            # Performance assertion: should complete within reasonable time
            assert total_time < 5.0, f"Performance test took too long: {total_time:.2f}s"
        
        print("✓ Performance and stability test passed!")
    
    def test_configuration_persistence(self) -> None:
        """Test configuration persistence across sessions."""
        print("\n=== Testing Configuration Persistence ===")
        
        # Test 1: Set configuration
        print("Step 1: Setting configuration...")
        with patch.object(self.cli, '_save_config') as mock_save:
            result = self.runner.invoke(
                self.cli,
                ["config", "update", "--output-format", "json", "--color-output", "false"],
                obj=self.cli
            )
            
            assert result.exit_code == 0
            mock_save.assert_called_once()
            print("✓ Configuration saved")
        
        # Test 2: Verify configuration persistence
        print("Step 2: Verifying configuration...")
        # Create a new CLI instance to simulate new session
        new_cli = UE5CLI()
        
        # Mock config loading to return our updated config
        with patch.object(new_cli, '_load_config') as mock_load:
            mock_load.return_value = {
                "default_engine_path": "",
                "default_project_path": "",
                "output_format": "json",
                "color_output": False,
                "interactive_mode": False,
                "auto_complete": True,
                "history_size": 1000,
            }
            
            # Show configuration
            result = self.runner.invoke(
                new_cli,
                ["config", "show"],
                obj=new_cli
            )
            
            assert result.exit_code == 0
            assert "json" in result.output.lower()
            assert "false" in result.output.lower()
            print("✓ Configuration persisted correctly")
        
        print("✓ Configuration persistence test passed!")


class TestRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def test_game_developer_workflow(self) -> None:
        """Test typical game developer workflow."""
        print("\n=== Testing Game Developer Workflow ===")
        
        # Mock all necessary components
        with patch.multiple(
            self.cli,
            project_manager=Mock(),
            asset_manager=Mock(),
            blueprint_manager=Mock(),
            level_manager=Mock(),
            build_system=Mock(),
            editor_manager=Mock(),
            session_manager=Mock(),
            cook_manager=Mock(),
            packaging_manager=Mock()
        ):
            # Set up mock returns for a complete game dev workflow
            self.cli.project_manager.create_project.return_value = {
                "status": "success",
                "project_name": "MyAwesomeGame",
                "engine_version": "5.4.0"
            }
            
            self.cli.asset_manager.import_asset.return_value = {
                "status": "success",
                "imported_assets": ["character", "environment", "props"]
            }
            
            self.cli.blueprint_manager.create_blueprint.return_value = {
                "status": "success",
                "blueprints": ["PlayerController", "GameMode", "HUD"]
            }
            
            self.cli.level_manager.create_level.return_value = {
                "status": "success",
                "levels": ["MainMenu", "Level1", "Level2", "BossLevel"]
            }
            
            self.cli.editor_manager.launch.return_value = {
                "status": "success",
                "editor_pid": 12345
            }
            
            self.cli.session_manager.start_session.return_value = {
                "status": "success",
                "session_id": "dev_session_001"
            }
            
            self.cli.build_system.compile.return_value = {
                "status": "success",
                "build_time": 420.5
            }
            
            self.cli.cook_manager.cook_content.return_value = {
                "status": "success",
                "cooked_assets": 5000
            }
            
            self.cli.packaging_manager.package_project.return_value = {
                "status": "success",
                "package_size": "2.5GB"
            }
            
            # Execute game developer workflow
            workflow_steps = [
                ("Creating project", ["project", "create", "MyAwesomeGame", "--engine-version", "5.4.0"]),
                ("Importing character models", ["asset", "import", "/assets/characters", "/Game/Characters"]),
                ("Creating player controller", ["blueprint", "create", "PlayerController", "--type", "PlayerController"]),
                ("Creating game mode", ["blueprint", "create", "GameMode", "--type", "GameMode"]),
                ("Creating levels", ["level", "create", "Level1"]),
                ("Launching editor", ["editor", "launch"]),
                ("Starting development session", ["session", "--start"]),
                ("Building project", ["build", "compile"]),
                ("Cooking content", ["cook", "content", "--platform", "Win64"]),
                ("Packaging for distribution", ["package", "build", "--platform", "Win64", "--configuration", "Shipping"]),
            ]
            
            for step_name, cmd in workflow_steps:
                print(f"Step: {step_name}")
                result = self.runner.invoke(
                    self.cli,
                    cmd,
                    obj=self.cli
                )
                
                assert result.exit_code == 0, f"Step '{step_name}' failed: {result.output}"
                print(f"✓ {step_name} successful")
        
        print("✓ Game developer workflow test passed!")
    
    def test_archviz_workflow(self) -> None:
        """Test architectural visualization workflow."""
        print("\n=== Testing Architectural Visualization Workflow ===")
        
        with patch.multiple(
            self.cli,
            project_manager=Mock(),
            asset_manager=Mock(),
            level_manager=Mock(),
            plugin_manager=Mock(),
            editor_manager=Mock()
        ):
            # Archviz specific setup
            self.cli.project_manager.create_project.return_value = {
                "status": "success",
                "project_name": "ArchVizProject",
                "template": "Architecture"
            }
            
            self.cli.asset_manager.import_asset.return_value = {
                "status": "success",
                "imported_assets": ["building_model", "furniture", "lighting"]
            }
            
            self.cli.plugin_manager.install_plugin.return_value = {
                "status": "success",
                "plugin": "Datasmith"
            }
            
            self.cli.plugin_manager.enable_plugin.return_value = {
                "status": "success",
                "plugin": "Datasmith",
                "enabled": True
            }
            
            self.cli.level_manager.create_level.return_value = {
                "status": "success",
                "level": "Showroom"
            }
            
            # Execute archviz workflow
            workflow = [
                ("Creating archviz project", ["project", "create", "ArchVizProject", "--template", "Architecture"]),
                ("Installing Datasmith plugin", ["plugin", "install", "/plugins/datasmith"]),
                ("Enabling Datasmith", ["plugin", "enable", "Datasmith"]),
                ("Importing building model", ["asset", "import", "/models/building.fbx", "/Game/Architecture"]),
                ("Creating showroom level", ["level", "create", "Showroom"]),
                ("Launching editor for visualization", ["editor", "launch", "--headless"]),
            ]
            
            for step_name, cmd in workflow:
                print(f"Step: {step_name}")
                result = self.runner.invoke(
                    self.cli,
                    cmd,
                    obj=self.cli
                )
                
                assert result.exit_code == 0, f"Step '{step_name}' failed: {result.output}"
                print(f"✓ {step_name} successful")
        
        print("✓ Architectural visualization workflow test passed!")
    
    def test_education_training_workflow(self) -> None:
        """Test education and training workflow."""
        print("\n=== Testing Education/Training Workflow ===")
        
        with patch.multiple(
            self.cli,
            project_manager=Mock(),
            blueprint_manager=Mock(),
            level_manager=Mock(),
            editor_manager=Mock(),
            session_manager=Mock()
        ):
            # Education setup
            self.cli.project_manager.create_project.return_value = {
                "status": "success",
                "project_name": "TrainingProject",
                "description": "UE5 Training Course"
            }
            
            self.cli.blueprint_manager.create_blueprint.return_value = {
                "status": "success",
                "blueprints": ["Lesson1", "Lesson2", "Lesson3"]
            }
            
            self.cli.level_manager.create_level.return_value = {
                "status": "success",
                "levels": ["TutorialLevel"]
            }
            
            self.cli.session_manager.start_session.return_value = {
                "status": "success",
                "session_id": "training_session",
                "duration": "2 hours"
            }
            
            # Execute education workflow
            workflow = [
                ("Creating training project", ["project", "create", "TrainingProject"]),
                ("Creating tutorial blueprints", ["blueprint", "create", "Lesson1", "--type", "Actor"]),
                ("Creating tutorial level", ["level", "create", "TutorialLevel"]),
                ("Starting training session", ["session", "--start"]),
                ("Launching editor for demonstration", ["editor", "launch"]),
            ]
            
            for step_name, cmd in workflow:
                print(f"Step: {step_name}")
                result = self.runner.invoke(
                    self.cli,
                    cmd,
                    obj=self.cli
                )
                
                assert result.exit_code == 0, f"Step '{step_name}' failed: {result.output}"
                print(f"✓ {step_name} successful")
        
        print("✓ Education/training workflow test passed!")


class TestCLIInterfaceUsability:
    """Tests for CLI interface usability and user experience."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.cli = UE5CLI()
        self.runner = CliRunner()
    
    def test_help_system(self) -> None:
        """Test comprehensive help system."""
        print("\n=== Testing Help System ===")
        
        # Test main help
        result = self.runner.invoke(self.cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output
        print("✓ Main help works")
        
        # Test command-specific help
        commands_to_test = [
            "project",
            "build",
            "editor",
            "asset",
            "plugin",
            "blueprint",
            "level",
            "package",
            "config",
            "session"
        ]
        
        for cmd in commands_to_test:
            result = self.runner.invoke(self.cli, [cmd, "--help"])
            assert result.exit_code == 0, f"Help for {cmd} failed"
            assert "Usage:" in result.output
            print(f"✓ Help for {cmd} works")
        
        print("✓ Complete help system test passed!")
    
    def test_output_formats(self) -> None:
        """Test different output formats."""
        print("\n=== Testing Output Formats ===")
        
        with patch.object(self.cli.project_manager, 'list_projects') as mock_list:
            test_data = {
                "projects": [
                    {"name": "Project1", "path": "/path/to/project1"},
                    {"name": "Project2", "path": "/path/to/project2"}
                ]
            }
            
            mock_list.return_value = test_data
            
            # Test text format (default)
            result_text = self.runner.invoke(
                self.cli,
                ["project", "list", "--format", "text"],
                obj=self.cli
            )
            assert result_text.exit_code == 0
            assert "Project1" in result_text.output
            print("✓ Text format works")
            
            # Test JSON format
            result_json = self.runner.invoke(
                self.cli,
                ["project", "list", "--format", "json"],
                obj=self.cli
            )
            assert result_json.exit_code == 0
            # Try to parse as JSON to verify
            import json
            json.loads(result_json.output)
            print("✓ JSON format works")
            
            # Test YAML format
            result_yaml = self.runner.invoke(
                self.cli,
                ["project", "list", "--format", "yaml"],
                obj=self.cli
            )
            assert result_yaml.exit_code == 0
            assert "Project1" in result_yaml.output
            print("✓ YAML format works")
        
        print("✓ Output formats test passed!")
    
    def test_error_messages_clarity(self) -> None:
        """Test clarity of error messages."""
        print("\n=== Testing Error Message Clarity ===")
        
        test_cases = [
            {
                "command": ["project", "open", "/nonexistent"],
                "error": ProjectNotFoundError("Project file not found"),
                "expected_message": "Error opening project"
            },
            {
                "command": ["asset", "import", "/nonexistent", "/Game/Test"],
                "error": FileNotFoundError("Asset file not found"),
                "expected_message": "Error importing asset"
            },
            {
                "command": ["build", "compile"],
                "error": Exception("Build failed with 15 errors"),
                "expected_message": "Error compiling project"
            },
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"Test case {i+1}: {test_case['command'][0]}")
            
            # Get the appropriate manager based on command
            manager_name = {
                "project": "project_manager",
                "asset": "asset_manager",
                "build": "build_system"
            }.get(test_case["command"][0])
            
            if manager_name:
                manager = getattr(self.cli, manager_name)
                with patch.object(manager, test_case["command"][1]) as mock_method:
                    mock_method.side_effect = test_case["error"]
                    
                    result = self.runner.invoke(
                        self.cli,
                        test_case["command"],
                        obj=self.cli
                    )
                    
                    assert result.exit_code == 1
                    assert test_case["expected_message"] in result.output
                    print(f"✓ Error message clear for {test_case['command'][0]}")
        
        print("✓ Error message clarity test passed!")


if __name__ == "__main__":
    """Run end-to-end tests directly."""
    print("=" * 60)
    print("Unreal Engine CLI - End-to-End Test Suite")
    print("=" * 60)
    
    # Run tests
    import pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 60)
    print(f"Test Suite Complete - Exit Code: {exit_code}")
    print("=" * 60)
    
    sys.exit(0 if exit_code == 0 else 1)
        
