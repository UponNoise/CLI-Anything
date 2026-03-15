#!/usr/bin/env python3
"""Unreal Engine CLI - Main CLI module.

This module provides the main command-line interface for Unreal Engine 5,
integrating all core modules and providing a unified user experience.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
import sys
import yaml
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import click
from click import Context, Parameter

try:
    from .utils.repl_skin import REPLSkin, OutputStyle, create_default_commands
except ImportError:
    # Fallback for testing
    REPLSkin = None
    OutputStyle = None
    create_default_commands = None


class OutputFormat(Enum):
    """Output format enumeration."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


class UE5CLI(click.MultiCommand):
    """Unreal Engine 5 CLI - Main command group.
    
    This class implements the main CLI interface with command discovery,
    help system, and output formatting.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        invoke_without_command: bool = False,
        no_args_is_help: bool = False,
        subcommand_metavar: Optional[str] = None,
        chain: bool = False,
        result_callback: Optional[callable] = None,
        **attrs: Any
    ) -> None:
        """Initialize UE5 CLI.
        
        Args:
            name: Command name.
            invoke_without_command: Whether to invoke without command.
            no_args_is_help: Whether to show help when no args.
            subcommand_metavar: Subcommand metavar.
            chain: Whether to chain commands.
            result_callback: Result callback.
            **attrs: Additional attributes.
        """
        super().__init__(
            name=name,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            **attrs
        )
        
        # Configuration
        self.config = self._load_config()
        
        # Command cache
        self._commands: Dict[str, click.Command] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary.
        """
        config_path = Path.home() / ".ue_cli" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default configuration
        return {
            "default_engine_path": "",
            "default_project_path": "",
            "output_format": "text",
            "color_output": True,
            "interactive_mode": False,
            "auto_complete": True,
            "history_size": 1000,
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        config_path = Path.home() / ".ue_cli" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
    
    def list_commands(self, ctx: Context) -> List[str]:
        """List all available commands.
        
        Args:
            ctx: Click context.
            
        Returns:
            List of command names.
        """
        commands = [
            "project",
            "build",
            "editor",
            "asset",
            "plugin",
            "cook",
            "session",
            "blueprint",
            "level",
            "package",
            "config",
            "status",
            "version",
            "repl",
            "help",
        ]
        return sorted(commands)
    
    def get_command(self, ctx: Context, cmd_name: str) -> Optional[click.Command]:
        """Get command by name.
        
        Args:
            ctx: Click context.
            cmd_name: Command name.
            
        Returns:
            Command object or None if not found.
        """
        if cmd_name in self._commands:
            return self._commands[cmd_name]
        
        # Create command if not cached
        command = self._create_command(cmd_name)
        if command:
            self._commands[cmd_name] = command
        
        return command
    
    def _create_command(self, cmd_name: str) -> Optional[click.Command]:
        """Create command by name.
        
        Args:
            cmd_name: Command name.
            
        Returns:
            Command object or None if not found.
        """
        if cmd_name == "project":
            return self._create_project_command()
        elif cmd_name == "build":
            return self._create_build_command()
        elif cmd_name == "editor":
            return self._create_editor_command()
        elif cmd_name == "asset":
            return self._create_asset_command()
        elif cmd_name == "plugin":
            return self._create_plugin_command()
        elif cmd_name == "cook":
            return self._create_cook_command()
        elif cmd_name == "session":
            return self._create_session_command()
        elif cmd_name == "blueprint":
            return self._create_blueprint_command()
        elif cmd_name == "level":
            return self._create_level_command()
        elif cmd_name == "package":
            return self._create_package_command()
        elif cmd_name == "config":
            return self._create_config_command()
        elif cmd_name == "status":
            return self._create_status_command()
        elif cmd_name == "version":
            return self._create_version_command()
        elif cmd_name == "repl":
            return self._create_repl_command()
        elif cmd_name == "help":
            return self._create_help_command()
        
        return None
    
    def _format_output(
        self,
        data: Any,
        format_type: OutputFormat,
        ctx: Optional[Context] = None
    ) -> str:
        """Format output according to specified format.
        
        Args:
            data: Data to format.
            format_type: Output format.
            ctx: Click context for color settings.
            
        Returns:
            Formatted output string.
        """
        if format_type == OutputFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type == OutputFormat.YAML:
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:  # TEXT
            if isinstance(data, (dict, list)):
                return self._format_text(data, ctx)
            else:
                return str(data)
    
    def _format_text(self, data: Any, ctx: Optional[Context] = None) -> str:
        """Format data as human-readable text.
        
        Args:
            data: Data to format.
            ctx: Click context for color settings.
            
        Returns:
            Formatted text.
        """
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                
                if ctx and ctx.color:
                    lines.append(f"\033[1;36m{key}:\033[0m {value_str}")
                else:
                    lines.append(f"{key}: {value_str}")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    item_str = self._format_text(item, ctx)
                    if ctx and ctx.color:
                        lines.append(f"\033[1;33m[{i}]\033[0m\n{item_str}")
                    else:
                        lines.append(f"[{i}]\n{item_str}")
                else:
                    if ctx and ctx.color:
                        lines.append(f"\033[1;33m[{i}]\033[0m {item}")
                    else:
                        lines.append(f"[{i}] {item}")
            return "\n".join(lines)
        
        else:
            return str(data)
    
    def _create_project_command(self) -> click.Group:
        """Create project command group.
        
        Returns:
            Project command group.
        """
        @click.group(name="project", help="Project management commands.")
        @click.pass_context
        def project_group(ctx):
            """Project management commands."""
            pass
        
        @project_group.command(name="create", help="Create a new Unreal Engine project.")
        @click.argument("name")
        @click.option("--template", "-t", help="Project template to use.")
        @click.option("--output-dir", "-o", type=click.Path(), help="Output directory.")
        @click.option("--engine-version", "-e", help="Unreal Engine version.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def project_create(ctx, name, template, output_dir, engine_version, format):
            """Create a new Unreal Engine project."""
            try:
                # Import here to avoid circular imports
                from .core.project import ProjectManager
                manager = ProjectManager()
                result = manager.create_project(
                    name=name,
                    template=template,
                    output_dir=output_dir,
                    engine_version=engine_version
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error creating project: {e}", err=True)
                ctx.exit(1)
        
        @project_group.command(name="open", help="Open an existing project.")
        @click.argument("path", type=click.Path(exists=True))
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def project_open(ctx, path, format):
            """Open an existing project."""
            try:
                from .core.project import ProjectManager
                manager = ProjectManager()
                result = manager.open_project(path)
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error opening project: {e}", err=True)
                ctx.exit(1)
        
        @project_group.command(name="list", help="List available projects.")
        @click.option("--path", "-p", type=click.Path(), help="Directory to search.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def project_list(ctx, path, format):
            """List available projects."""
            try:
                # Simulate project listing for now
                result = [
                    {"name": "ExampleProject", "path": "/path/to/project", "engine_version": "5.3"},
                    {"name": "TestGame", "path": "/another/path", "engine_version": "5.4"},
                ]
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error listing projects: {e}", err=True)
                ctx.exit(1)
        
        return project_group
    
    def _create_build_command(self) -> click.Group:
        """Create build command group.
        
        Returns:
            Build command group.
        """
        @click.group(name="build", help="Build system commands.")
        @click.pass_context
        def build_group(ctx):
            """Build system commands."""
            pass
        
        @build_group.command(name="compile", help="Compile project.")
        @click.option("--target", "-t", default="Editor", help="Build target.")
        @click.option("--platform", "-p", default="Win64", help="Target platform.")
        @click.option("--configuration", "-c", default="Development", help="Build configuration.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def build_compile(ctx, target, platform, configuration, project, format):
            """Compile project."""
            try:
                from .core.build import BuildSystem
                manager = BuildSystem()
                result = manager.compile(
                    target=target,
                    platform=platform,
                    configuration=configuration,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error compiling project: {e}", err=True)
                ctx.exit(1)
        
        @build_group.command(name="clean", help="Clean build artifacts.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def build_clean(ctx, project, format):
            """Clean build artifacts."""
            try:
                from .core.build import BuildSystem
                manager = BuildSystem()
                result = manager.clean(project_path=project)
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error cleaning build: {e}", err=True)
                ctx.exit(1)
        
        return build_group
    
    def _create_editor_command(self) -> click.Group:
        """Create editor command group.
        
        Returns:
            Editor command group.
        """
        @click.group(name="editor", help="Editor management commands.")
        @click.pass_context
        def editor_group(ctx):
            """Editor management commands."""
            pass
        
        @editor_group.command(name="launch", help="Launch Unreal Editor.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--map", "-m", help="Initial map to load.")
        @click.option("--game-mode", "-g", help="Game mode to use.")
        @click.option("--headless", is_flag=True, help="Launch in headless mode.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def editor_launch(ctx, project, map, game_mode, headless, format):
            """Launch Unreal Editor."""
            try:
                from .core.editor import EditorManager
                manager = EditorManager()
                result = manager.launch(
                    project_path=project,
                    map=map,
                    game_mode=game_mode,
                    headless=headless
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error launching editor: {e}", err=True)
                ctx.exit(1)
        
        return editor_group
    
    def _create_asset_command(self) -> click.Group:
        """Create asset command group.
        
        Returns:
            Asset command group.
        """
        @click.group(name="asset", help="Asset management commands.")
        @click.pass_context
        def asset_group(ctx):
            """Asset management commands."""
            pass
        
        @asset_group.command(name="import", help="Import asset into project.")
        @click.argument("source", type=click.Path(exists=True))
        @click.argument("destination")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def asset_import(ctx, source, destination, project, format):
            """Import asset into project."""
            try:
                from .core.asset import AssetManager
                manager = AssetManager()
                result = manager.import_asset(
                    source_path=source,
                    destination_path=destination,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error importing asset: {e}", err=True)
                ctx.exit(1)
        
        @asset_group.command(name="list", help="List assets in project.")
        @click.option("--path", "-p", help="Asset path filter.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def asset_list(ctx, path, project, format):
            """List assets in project."""
            try:
                from .core.asset import AssetManager
                manager = AssetManager()
                result = manager.list_assets(
                    path_filter=path,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error listing assets: {e}", err=True)
                ctx.exit(1)
        
        return asset_group
    
    def _create_plugin_command(self) -> click.Group:
        """Create plugin command group.
        
        Returns:
            Plugin command group.
        """
        @click.group(name="plugin", help="Plugin management commands.")
        @click.pass_context
        def plugin_group(ctx):
            """Plugin management commands."""
            pass
        
        @plugin_group.command(name="list", help="List installed plugins.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def plugin_list(ctx, project, format):
            """List installed plugins."""
            try:
                from .core.plugin import PluginManager
                manager = PluginManager()
                result = manager.list_plugins(project_path=project)
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error listing plugins: {e}", err=True)
                ctx.exit(1)
        
        @plugin_group.command(name="enable", help="Enable a plugin.")
        @click.argument("plugin_name")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def plugin_enable(ctx, plugin_name, project, format):
            """Enable a plugin."""
            try:
                from .core.plugin import PluginManager
                manager = PluginManager()
                result = manager.enable_plugin(
                    plugin_name=plugin_name,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error enabling plugin: {e}", err=True)
                ctx.exit(1)
        
        return plugin_group
    
    def _create_cook_command(self) -> click.Group:
        """Create cook command group.
        
        Returns:
            Cook command group.
        """
        @click.group(name="cook", help="Content cooking commands.")
        @click.pass_context
        def cook_group(ctx):
            """Content cooking commands."""
            pass
        
        @cook_group.command(name="content", help="Cook project content.")
        @click.option("--platform", "-p", default="Win64", help="Target platform.")
        @click.option("--maps", "-m", help="Comma-separated list of maps to cook.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def cook_content(ctx, platform, maps, project, format):
            """Cook project content."""
            try:
                from .core.cook import CookManager
                manager = CookManager()
                map_list = maps.split(",") if maps else None
                result = manager.cook_content(
                    platform=platform,
                    maps=map_list,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error cooking content: {e}", err=True)
                ctx.exit(1)
        
        return cook_group
    
    def _create_session_command(self) -> click.Command:
        """Create session command.
        
        Returns:
            Session command.
        """
        @click.command(name="session", help="Session management.")
        @click.option("--start", "-s", is_flag=True, help="Start a new session.")
        @click.option("--stop", "-S", is_flag=True, help="Stop current session.")
        @click.option("--status", "-t", is_flag=True, help="Show session status.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def session_command(ctx, start, stop, status, format):
            """Session management."""
            try:
                from .core.session import SessionManager
                manager = SessionManager()
                
                if start:
                    result = manager.start_session()
                elif stop:
                    result = manager.stop_session()
                elif status:
                    result = manager.get_session_status()
                else:
                    result = manager.get_session_status()
                
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error managing session: {e}", err=True)
                ctx.exit(1)
        
        return session_command
    
    def _create_blueprint_command(self) -> click.Group:
        """Create blueprint command group.
        
        Returns:
            Blueprint command group.
        """
        @click.group(name="blueprint", help="Blueprint management commands.")
        @click.pass_context
        def blueprint_group(ctx):
            """Blueprint management commands."""
            pass
        
        @blueprint_group.command(name="create", help="Create a new blueprint.")
        @click.argument("name")
        @click.option("--type", "-t", default="Actor", help="Blueprint type.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def blueprint_create(ctx, name, type, project, format):
            """Create a new blueprint."""
            try:
                from .core.blueprint import BlueprintManager
                manager = BlueprintManager()
                result = manager.create_blueprint(
                    name=name,
                    blueprint_type=type,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error creating blueprint: {e}", err=True)
                ctx.exit(1)
        
        return blueprint_group
    
    def _create_level_command(self) -> click.Group:
        """Create level command group.
        
        Returns:
            Level command group.
        """
        @click.group(name="level", help="Level management commands.")
        @click.pass_context
        def level_group(ctx):
            """Level management commands."""
            pass
        
        @level_group.command(name="create", help="Create a new level.")
        @click.argument("name")
        @click.option("--template", "-t", help="Level template.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def level_create(ctx, name, template, project, format):
            """Create a new level."""
            try:
                from .core.level import LevelManager
                manager = LevelManager()
                result = manager.create_level(
                    name=name,
                    template=template,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error creating level: {e}", err=True)
                ctx.exit(1)
        
        return level_group
    
    def _create_package_command(self) -> click.Group:
        """Create package command group.
        
        Returns:
            Package command group.
        """
        @click.group(name="package", help="Packaging commands.")
        @click.pass_context
        def package_group(ctx):
            """Packaging commands."""
            pass
        
        @package_group.command(name="build", help="Package project for distribution.")
        @click.option("--platform", "-p", default="Win64", help="Target platform.")
        @click.option("--configuration", "-c", default="Shipping", help="Build configuration.")
        @click.option("--project", "-P", type=click.Path(), help="Project path.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def package_build(ctx, platform, configuration, project, format):
            """Package project for distribution."""
            try:
                from .core.packaging import PackagingManager
                manager = PackagingManager()
                result = manager.package_project(
                    platform=platform,
                    configuration=configuration,
                    project_path=project
                )
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error packaging project: {e}", err=True)
                ctx.exit(1)
        
        return package_group
    
    def _create_config_command(self) -> click.Group:
        """Create config command group.
        
        Returns:
            Config command group.
        """
        @click.group(name="config", help="Configuration management.")
        @click.pass_context
        def config_group(ctx):
            """Configuration management."""
            pass
        
        @config_group.command(name="show", help="Show current configuration.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def config_show(ctx, format):
            """Show current configuration."""
            try:
                output = self._format_output(self.config, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error showing config: {e}", err=True)
                ctx.exit(1)
        
        @config_group.command(name="set", help="Set configuration value.")
        @click.argument("key")
        @click.argument("value")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def config_set(ctx, key, value, format):
            """Set configuration value."""
            try:
                # Parse value if it looks like JSON
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    # Try to parse as boolean
                    if value.lower() in ["true", "false"]:
                        parsed_value = value.lower() == "true"
                    else:
                        # Try to parse as number
                        try:
                            parsed_value = int(value)
                        except ValueError:
                            try:
                                parsed_value = float(value)
                            except ValueError:
                                parsed_value = value
                
                self.config[key] = parsed_value
                self._save_config()
                
                result = {"key": key, "value": parsed_value, "status": "updated"}
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error setting config: {e}", err=True)
                ctx.exit(1)
        
        @config_group.command(name="get", help="Get configuration value.")
        @click.argument("key")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def config_get(ctx, key, format):
            """Get configuration value."""
            try:
                if key in self.config:
                    result = {key: self.config[key]}
                else:
                    result = {"error": f"Key '{key}' not found"}
                
                output = self._format_output(result, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error getting config: {e}", err=True)
                ctx.exit(1)
        
        return config_group
    
    def _create_status_command(self) -> click.Command:
        """Create status command.
        
        Returns:
            Status command.
        """
        @click.command(name="status", help="Show system status.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def status_command(ctx, format):
            """Show system status."""
            try:
                status = {
                    "cli_version": "1.0.0",
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                    "config_path": str(Path.home() / ".ue_cli" / "config.json"),
                    "config_exists": (Path.home() / ".ue_cli" / "config.json").exists(),
                }
                
                output = self._format_output(status, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error getting status: {e}", err=True)
                ctx.exit(1)
        
        return status_command
    
    def _create_version_command(self) -> click.Command:
        """Create version command.
        
        Returns:
            Version command.
        """
        @click.command(name="version", help="Show version information.")
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def version_command(ctx, format):
            """Show version information."""
            try:
                version_info = {
                    "ue_cli_version": "1.0.0",
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                    "click_version": click.__version__,
                    "system": os.name,
                }
                
                output = self._format_output(version_info, OutputFormat(format), ctx)
                click.echo(output)
            except Exception as e:
                click.echo(f"Error getting version: {e}", err=True)
                ctx.exit(1)
        
        return version_command
    
    def _create_repl_command(self) -> click.Command:
        """Create REPL command.
        
        Returns:
            REPL command.
        """
        @click.command(name="repl", help="Start interactive REPL.")
        @click.option("--style", "-s", type=click.Choice(["rich", "plain", "minimal"]), default="rich", help="Output style.")
        @click.option("--prompt", "-p", default="ue> ", help="Prompt string.")
        @click.option("--history-file", "-H", type=click.Path(), help="History file path.")
        @click.pass_context
        def repl_command(ctx, style, prompt, history_file):
            """Start interactive REPL."""
            try:
                # Create commands from CLI
                commands = create_default_commands()
                
                # Create REPL
                repl = REPLSkin(
                    commands=commands,
                    prompt=prompt,
                    style=OutputStyle(style),
                    history_file=Path(history_file) if history_file else None
                )
                
                # Run REPL
                repl.run()
            except Exception as e:
                click.echo(f"Error starting REPL: {e}", err=True)
                ctx.exit(1)
        
        return repl_command
    
    def _create_help_command(self) -> click.Command:
        """Create help command.
        
        Returns:
            Help command.
        """
        @click.command(name="help", help="Show help information.")
        @click.argument("command", required=False)
        @click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
        @click.pass_context
        def help_command(ctx, command, format):
            """Show help information."""
            try:
                if command:
                    # Show help for specific command
                    cmd = self.get_command(ctx, command)
                    if cmd:
                        if format == "json":
                            help_info = {
                                "command": command,
                                "help": cmd.help or "No help available",
                            }
                            output = json.dumps(help_info, indent=2)
                        elif format == "yaml":
                            help_info = {
                                "command": command,
                                "help": cmd.help or "No help available",
                            }
                            output = yaml.dump(help_info, default_flow_style=False)
                        else:
                            output = f"Command: {command}\n\n{cmd.help or 'No help available'}"
                    else:
                        output = f"Command not found: {command}"
                else:
                    # Show general help
                    if format == "json":
                        commands = self.list_commands(ctx)
                        help_info = {
                            "available_commands": commands,
                            "description": "Unreal Engine CLI - Command line interface for Unreal Engine 5",
                        }
                        output = json.dumps(help_info, indent=2)
                    elif format == "yaml":
                        commands = self.list_commands(ctx)
                        help_info = {
                            "available_commands": commands,
                            "description": "Unreal Engine CLI - Command line interface for Unreal Engine 5",
                        }
                        output = yaml.dump(help_info, default_flow_style=False)
                    else:
                        output = self._format_general_help(ctx)
                
                click.echo(output)
            except Exception as e:
                click.echo(f"Error showing help: {e}", err=True)
                ctx.exit(1)
        
        return help_command
    
    def _format_general_help(self, ctx: Context) -> str:
        """Format general help text.
        
        Args:
            ctx: Click context.
            
        Returns:
            Formatted help text.
        """
        commands = self.list_commands(ctx)
        
        help_text = """Unreal Engine CLI - Command line interface for Unreal Engine 5

Usage: ue-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:"""
        
        for cmd in commands:
            cmd_obj = self.get_command(ctx, cmd)
            if cmd_obj:
                help_line = f"  {cmd:15} {cmd_obj.help or 'No description'}"
                help_text += f"\n{help_line}"
        
        help_text += "\n\nFor more information on a specific command, use: ue-cli help <command>"
        
        return help_text


# Main CLI function
@click.command(cls=UE5CLI, help="Unreal Engine CLI - Command line interface for Unreal Engine 5")
@click.version_option(version="1.0.0", prog_name="Unreal Engine CLI")
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format.")
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--quiet", "-q", is_flag=True, help="Enable quiet mode.")
@click.pass_context
def cli(ctx, format, no_color, verbose, quiet):
    """Main CLI entry point.
    
    Args:
        ctx: Click context.
        format: Output format.
        no_color: Disable colored output.
        verbose: Enable verbose output.
        quiet: Enable quiet mode.
    """
    # Set context settings
    ctx.color = not no_color
    ctx.verbose = verbose
    ctx.quiet = quiet
    
    # Store format in context
    ctx.format = format
    
    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()