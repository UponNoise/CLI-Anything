#!/usr/bin/env python3
"""Unreal Engine CLI - Main CLI module.

This module provides a functional end-to-end CLI for UE5 project automation.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from click import Context

try:
    from .utils.repl_skin import REPLSkin, OutputStyle, create_default_commands
except ImportError:
    REPLSkin = None
    OutputStyle = None
    create_default_commands = None


class OutputFormat(Enum):
    """Output format enumeration."""

    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


class UE5CLI(click.MultiCommand):
    """Unreal Engine 5 CLI main command group."""

    def __init__(
        self,
        name: Optional[str] = None,
        invoke_without_command: bool = False,
        no_args_is_help: bool = False,
        subcommand_metavar: Optional[str] = None,
        chain: bool = False,
        result_callback: Optional[callable] = None,
        **attrs: Any,
    ) -> None:
        super().__init__(
            name=name,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            **attrs,
        )
        self.config = self._load_config()
        self._commands: Dict[str, click.Command] = {}

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path.home() / ".ue_cli" / "config.json"
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "default_engine_path": "",
            "default_project_path": "",
            "output_format": "text",
            "color_output": True,
            "interactive_mode": False,
            "history_size": 1000,
        }

    def _save_config(self) -> None:
        config_path = Path.home() / ".ue_cli" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    def list_commands(self, ctx: Context) -> List[str]:
        return sorted(
            [
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
                "cpp",
                "config",
                "status",
                "version",
                "repl",
                "help",
            ]
        )

    def get_command(self, ctx: Context, cmd_name: str) -> Optional[click.Command]:
        if cmd_name in self._commands:
            return self._commands[cmd_name]
        command = self._create_command(cmd_name)
        if command:
            self._commands[cmd_name] = command
        return command

    def _create_command(self, cmd_name: str) -> Optional[click.Command]:
        mapping = {
            "project": self._create_project_command,
            "build": self._create_build_command,
            "editor": self._create_editor_command,
            "asset": self._create_asset_command,
            "plugin": self._create_plugin_command,
            "cook": self._create_cook_command,
            "session": self._create_session_command,
            "blueprint": self._create_blueprint_command,
            "level": self._create_level_command,
            "package": self._create_package_command,
            "cpp": self._create_cpp_command,
            "config": self._create_config_command,
            "status": self._create_status_command,
            "version": self._create_version_command,
            "repl": self._create_repl_command,
            "help": self._create_help_command,
        }
        factory = mapping.get(cmd_name)
        return factory() if factory else None

    def _serialize(self, data: Any) -> Any:
        if isinstance(data, Enum):
            return data.value
        if isinstance(data, Path):
            return str(data)
        if is_dataclass(data):
            return self._serialize(asdict(data))
        if isinstance(data, dict):
            return {str(k): self._serialize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._serialize(v) for v in data]
        return data

    def _format_output(self, data: Any, format_type: OutputFormat, ctx: Optional[Context] = None) -> str:
        serializable = self._serialize(data)
        if format_type == OutputFormat.JSON:
            return json.dumps(serializable, indent=2, ensure_ascii=False)
        if format_type == OutputFormat.YAML:
            return yaml.dump(serializable, default_flow_style=False, allow_unicode=True)
        return self._format_text(serializable, ctx)

    def _format_text(self, data: Any, ctx: Optional[Context] = None) -> str:
        if isinstance(data, dict):
            lines: List[str] = []
            for key, value in data.items():
                value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                if ctx and ctx.color:
                    lines.append(f"\033[1;36m{key}:\033[0m {value_str}")
                else:
                    lines.append(f"{key}: {value_str}")
            return "\n".join(lines)
        if isinstance(data, list):
            return "\n".join([f"[{i}] {self._format_text(v, ctx)}" for i, v in enumerate(data, start=1)])
        return str(data)

    def _session_manager(self):
        from .core.session import SessionManager

        return SessionManager(working_dir=Path.cwd())

    def _resolve_project_path(self, project_arg: Optional[str], required: bool = True) -> Optional[Path]:
        candidate = project_arg or self.config.get("default_project_path") or os.environ.get("UE_PROJECT_PATH")
        if not candidate:
            try:
                candidate = str(self._session_manager().get_project() or "")
            except Exception:
                candidate = ""

        if not candidate:
            if required:
                raise click.ClickException(
                    "Project path is required. Use --project or set config default_project_path."
                )
            return None

        path = Path(candidate).resolve()
        if path.is_dir():
            matches = list(path.glob("*.uproject"))
            if len(matches) == 1:
                path = matches[0]
            elif len(matches) > 1:
                raise click.ClickException(
                    f"Multiple .uproject files found under {path}. Please specify --project explicitly."
                )

        if not path.exists() or path.suffix != ".uproject":
            raise click.ClickException(f"Invalid .uproject path: {path}")

        return path

    def _resolve_engine_path(self, engine_arg: Optional[str], required: bool = True) -> Optional[Path]:
        candidate = engine_arg or self.config.get("default_engine_path") or os.environ.get("UE_ENGINE_PATH")
        if not candidate:
            try:
                candidate = str(self._session_manager().get_engine() or "")
            except Exception:
                candidate = ""

        if not candidate:
            try:
                from .utils.ue_backend import UEEngineLocator

                candidate = str(UEEngineLocator().get_default_engine().path)
            except Exception:
                candidate = ""

        if not candidate:
            if required:
                raise click.ClickException(
                    "Engine path is required. Use --engine or set config default_engine_path."
                )
            return None

        path = Path(candidate).resolve()
        if not path.exists():
            raise click.ClickException(f"Engine path does not exist: {path}")
        return path

    def _emit(self, ctx: Context, payload: Any, fmt: str) -> None:
        click.echo(self._format_output(payload, OutputFormat(fmt), ctx))

    def _create_project_command(self) -> click.Group:
        @click.group(name="project", help="Project management commands.")
        def group() -> None:
            pass

        @group.command(name="create", help="Create a new .uproject file.")
        @click.argument("name")
        @click.option("--output-dir", "output_dir", type=click.Path(), default=".")
        @click.option("--engine-version", "engine_version", default="5.4.0")
        @click.option("--template", "template", default="Blank")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def create_project(ctx: Context, name: str, output_dir: str, engine_version: str, template: str, fmt: str) -> None:
            from .core import project as project_core

            base = Path(output_dir).resolve() / name
            base.mkdir(parents=True, exist_ok=True)
            uproject_path = base / f"{name}.uproject"

            project_data = project_core.create_project(name=name, engine_version=engine_version)
            project_data.setdefault("AdditionalProperties", {})["Template"] = template
            saved = project_core.save_project(project_data, uproject_path)

            self._emit(ctx, {"project": saved, "status": "created"}, fmt)

        @group.command(name="open", help="Open and print .uproject content.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def open_project(ctx: Context, project: Optional[str], fmt: str) -> None:
            from .core import project as project_core

            project_path = self._resolve_project_path(project)
            data = project_core.open_project(project_path)
            self._emit(ctx, data, fmt)

        @group.command(name="info", help="Show project summary.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def info_project(ctx: Context, project: Optional[str], fmt: str) -> None:
            from .core import project as project_core

            project_path = self._resolve_project_path(project)
            data = project_core.get_project_info(project_core.open_project(project_path))
            self._emit(ctx, data, fmt)

        return group

    def _create_build_command(self) -> click.Group:
        @click.group(name="build", help="C++ build commands via UBT/UAT.")
        def group() -> None:
            pass

        @group.command(name="compile", help="Compile project via UBT.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--target", "target", default="Editor")
        @click.option("--platform", "platform_name", default="Win64")
        @click.option("--configuration", "configuration", default="Development")
        @click.option("--rebuild", "rebuild", is_flag=True)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def compile_project(
            ctx: Context,
            project: Optional[str],
            engine: Optional[str],
            target: str,
            platform_name: str,
            configuration: str,
            rebuild: bool,
            fmt: str,
        ) -> None:
            from .core.build import BuildConfiguration, BuildOptions, BuildPlatform, BuildSystem, BuildTarget

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            build = BuildSystem(engine_path)

            options = BuildOptions(
                target=BuildTarget(target),
                platform=BuildPlatform(platform_name),
                configuration=BuildConfiguration(configuration),
            )
            result = build.build_project(project_path=project_path, options=options, rebuild=rebuild)
            self._emit(ctx, result, fmt)

        @group.command(name="clean", help="Clean project build artifacts.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--target", "target", default="Editor")
        @click.option("--platform", "platform_name", default="Win64")
        @click.option("--configuration", "configuration", default="Development")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def clean_project(
            ctx: Context,
            project: Optional[str],
            engine: Optional[str],
            target: str,
            platform_name: str,
            configuration: str,
            fmt: str,
        ) -> None:
            from .core.build import BuildConfiguration, BuildOptions, BuildPlatform, BuildSystem, BuildTarget

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            build = BuildSystem(engine_path)

            options = BuildOptions(
                target=BuildTarget(target),
                platform=BuildPlatform(platform_name),
                configuration=BuildConfiguration(configuration),
            )
            result = build.clean_project(project_path=project_path, options=options)
            self._emit(ctx, result, fmt)

        @group.command(name="generate", help="Generate IDE project files.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--ide", "ide", default="VisualStudio2022")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def generate_project_files(ctx: Context, project: Optional[str], engine: Optional[str], ide: str, fmt: str) -> None:
            from .core.build import BuildSystem

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            build = BuildSystem(engine_path)
            result = build.generate_project_files(project_path=project_path, ide=ide)
            self._emit(ctx, result, fmt)

        return group

    def _create_editor_command(self) -> click.Group:
        @click.group(name="editor", help="Editor launch and commandlet commands.")
        def group() -> None:
            pass

        @group.command(name="launch", help="Launch Unreal Editor.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--map", "map_name", default=None)
        @click.option("--game-mode", "game_mode", default=None)
        @click.option("--headless", "headless", is_flag=True)
        @click.option("--wait", "wait", is_flag=True)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def launch_editor(
            ctx: Context,
            project: Optional[str],
            engine: Optional[str],
            map_name: Optional[str],
            game_mode: Optional[str],
            headless: bool,
            wait: bool,
            fmt: str,
        ) -> None:
            from .core.editor import EditorManager, EditorMode, EditorOptions

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            manager = EditorManager(engine_path=engine_path, project_path=project_path)
            options = EditorOptions(
                map=map_name,
                game_mode=game_mode,
                mode=EditorMode.HEADLESS if headless else EditorMode.NORMAL,
            )
            proc = manager.launch(options=options, wait=wait)
            if wait:
                payload = {
                    "success": proc.returncode == 0,
                    "return_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            else:
                payload = {"success": True, "pid": proc.pid}
            self._emit(ctx, payload, fmt)

        return group

    def _create_asset_command(self) -> click.Group:
        @click.group(name="asset", help="Asset management commands.")
        def group() -> None:
            pass

        @group.command(name="import", help="Import an external file as asset.")
        @click.argument("source", type=click.Path(exists=True))
        @click.argument("destination")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def import_asset(ctx: Context, source: str, destination: str, project: Optional[str], engine: Optional[str], fmt: str) -> None:
            from .core.asset import AssetManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = AssetManager(project_path=project_path, engine_path=engine_path)
            result = manager.import_asset(source_path=Path(source), destination_path=destination)
            self._emit(ctx, {"asset": result, "status": "imported"}, fmt)

        @group.command(name="list", help="List assets from /Game path.")
        @click.option("--path", "asset_path", default="/Game")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def list_assets(ctx: Context, asset_path: str, project: Optional[str], engine: Optional[str], fmt: str) -> None:
            from .core.asset import AssetManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = AssetManager(project_path=project_path, engine_path=engine_path)
            result = manager.list_assets(path_filter=asset_path)
            self._emit(ctx, result, fmt)

        return group

    def _create_plugin_command(self) -> click.Group:
        @click.group(name="plugin", help="Plugin management commands.")
        def group() -> None:
            pass

        @group.command(name="list", help="List project/engine plugins.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--include-engine", "include_engine", is_flag=True, default=True)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def list_plugins(ctx: Context, project: Optional[str], engine: Optional[str], include_engine: bool, fmt: str) -> None:
            from .core.plugin import PluginManager

            project_path = self._resolve_project_path(project, required=False)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = PluginManager(engine_path=engine_path, project_path=project_path.parent if project_path else None)
            result = manager.list_plugins(include_engine=include_engine)
            self._emit(ctx, result, fmt)

        @group.command(name="enable", help="Enable a plugin in project config.")
        @click.argument("plugin_name")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def enable_plugin(ctx: Context, plugin_name: str, project: Optional[str], engine: Optional[str], fmt: str) -> None:
            from .core.plugin import PluginManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = PluginManager(engine_path=engine_path, project_path=project_path.parent)
            ok = manager.enable_plugin(plugin_name)
            self._emit(ctx, {"plugin": plugin_name, "enabled": ok}, fmt)

        @group.command(name="disable", help="Disable a plugin in project config.")
        @click.argument("plugin_name")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def disable_plugin(ctx: Context, plugin_name: str, project: Optional[str], engine: Optional[str], fmt: str) -> None:
            from .core.plugin import PluginManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = PluginManager(engine_path=engine_path, project_path=project_path.parent)
            ok = manager.disable_plugin(plugin_name)
            self._emit(ctx, {"plugin": plugin_name, "disabled": ok}, fmt)

        return group

    def _create_cook_command(self) -> click.Group:
        @click.group(name="cook", help="Cook content for target platform.")
        def group() -> None:
            pass

        @group.command(name="content", help="Cook project content using UAT.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--target", "target", default="Windows")
        @click.option("--flavor", "flavor", default="Development")
        @click.option("--maps", "maps", default="")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def cook_content(
            ctx: Context,
            project: Optional[str],
            engine: Optional[str],
            target: str,
            flavor: str,
            maps: str,
            fmt: str,
        ) -> None:
            from .core.cook import CookFlavor, CookManager, CookOptions, CookTarget

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            manager = CookManager(engine_path=engine_path, project_path=project_path)
            options = CookOptions(
                target=CookTarget(target),
                flavor=CookFlavor(flavor),
                maps=[m.strip() for m in maps.split(",") if m.strip()],
            )
            result = manager.cook_content(options=options)
            self._emit(ctx, result, fmt)

        return group

    def _create_session_command(self) -> click.Group:
        @click.group(name="session", help="Session state management.")
        def group() -> None:
            pass

        @group.command(name="show", help="Show current session state.")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def show_session(ctx: Context, fmt: str) -> None:
            manager = self._session_manager()
            self._emit(ctx, manager.export_to_dict(), fmt)

        @group.command(name="set-engine", help="Set current engine path.")
        @click.argument("engine_path", type=click.Path(exists=True))
        @click.pass_context
        def set_engine(ctx: Context, engine_path: str) -> None:
            manager = self._session_manager()
            manager.set_engine(engine_path)
            self._emit(ctx, {"engine": str(Path(engine_path).resolve()), "status": "set"}, "text")

        @group.command(name="set-project", help="Set current project path.")
        @click.argument("project_path", type=click.Path(exists=True))
        @click.pass_context
        def set_project(ctx: Context, project_path: str) -> None:
            manager = self._session_manager()
            manager.set_project(project_path)
            self._emit(ctx, {"project": str(Path(project_path).resolve()), "status": "set"}, "text")

        return group

    def _create_blueprint_command(self) -> click.Group:
        @click.group(name="blueprint", help="Blueprint development commands.")
        def group() -> None:
            pass

        @group.command(name="create", help="Create blueprint in /Game path.")
        @click.argument("name")
        @click.option("--path", "bp_path", default="/Game/Blueprints")
        @click.option("--parent-class", "parent_class", default="Actor")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def create_blueprint(
            ctx: Context,
            name: str,
            bp_path: str,
            parent_class: str,
            project: Optional[str],
            engine: Optional[str],
            fmt: str,
        ) -> None:
            from .core.blueprint import BlueprintManager, CreateBlueprintOptions

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = BlueprintManager(project_path=project_path, engine_path=engine_path)
            options = CreateBlueprintOptions(parent_class=parent_class)
            result = manager.create_blueprint(name=name, path=bp_path, options=options)
            self._emit(ctx, {"blueprint": result, "status": "created"}, fmt)

        @group.command(name="compile", help="Compile a blueprint by /Game path.")
        @click.argument("blueprint_path")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def compile_blueprint(
            ctx: Context,
            blueprint_path: str,
            project: Optional[str],
            engine: Optional[str],
            fmt: str,
        ) -> None:
            from .core.blueprint import BlueprintManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = BlueprintManager(project_path=project_path, engine_path=engine_path)
            result = manager.compile_blueprint(blueprint_path)
            self._emit(ctx, {"blueprint": blueprint_path, "compiled": result}, fmt)

        @group.command(name="list", help="List blueprints.")
        @click.option("--path", "bp_path", default="/Game")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def list_blueprints(ctx: Context, bp_path: str, project: Optional[str], engine: Optional[str], fmt: str) -> None:
            from .core.blueprint import BlueprintManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = BlueprintManager(project_path=project_path, engine_path=engine_path)
            result = manager.list_blueprints(path=bp_path)
            self._emit(ctx, result, fmt)

        return group

    def _create_level_command(self) -> click.Group:
        @click.group(name="level", help="Level operations.")
        def group() -> None:
            pass

        @group.command(name="create", help="Create level .umap in Content/Maps.")
        @click.argument("name")
        @click.option("--subfolder", "subfolder", default="Maps")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def create_level(
            ctx: Context,
            name: str,
            subfolder: str,
            project: Optional[str],
            engine: Optional[str],
            fmt: str,
        ) -> None:
            from .core.level import LevelManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = LevelManager(project_path=project_path.parent, engine_path=engine_path)
            result = manager.create_level(name=name, subfolder=subfolder)
            self._emit(ctx, {"level": str(result), "status": "created"}, fmt)

        return group

    def _create_package_command(self) -> click.Group:
        @click.group(name="package", help="Package builds for distribution.")
        def group() -> None:
            pass

        @group.command(name="build", help="Run UAT BuildCookRun package flow.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--archive", "archive", type=click.Path(), default=None)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def package_build(ctx: Context, project: Optional[str], engine: Optional[str], archive: Optional[str], fmt: str) -> None:
            from .core.build import BuildSystem, PackageOptions

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            build = BuildSystem(engine_path)
            options = PackageOptions(archive=bool(archive), archive_directory=archive)
            result = build.package_project(project_path=project_path, options=options)
            self._emit(ctx, result, fmt)

        return group

    def _create_cpp_command(self) -> click.Group:
        @click.group(name="cpp", help="C++ workflow commands.")
        def group() -> None:
            pass

        @group.command(name="add-module", help="Add C++ module in .uproject and save.")
        @click.argument("module_name")
        @click.option("--module-type", "module_type", default="Runtime")
        @click.option("--loading-phase", "loading_phase", default="Default")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def add_module(
            ctx: Context,
            module_name: str,
            module_type: str,
            loading_phase: str,
            project: Optional[str],
            fmt: str,
        ) -> None:
            from .core import project as project_core

            project_path = self._resolve_project_path(project)
            project_data = project_core.open_project(project_path)
            updated = project_core.add_module(
                project_data,
                name=module_name,
                module_type=module_type,
                loading_phase=loading_phase,
            )
            project_core.save_project(updated, project_path)
            self._emit(ctx, {"module": module_name, "status": "added", "project": str(project_path)}, fmt)

        @group.command(name="create-plugin", help="Create C++ plugin skeleton.")
        @click.argument("plugin_name")
        @click.option("--template", "template", default="Blank")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def create_plugin(
            ctx: Context,
            plugin_name: str,
            template: str,
            project: Optional[str],
            engine: Optional[str],
            fmt: str,
        ) -> None:
            from .core.plugin import PluginManager

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine, required=False)
            manager = PluginManager(engine_path=engine_path, project_path=project_path.parent)
            result = manager.create_plugin(name=plugin_name, template=template)
            self._emit(ctx, result, fmt)

        @group.command(name="generate-files", help="Generate C++ IDE project files.")
        @click.option("--project", "project", type=click.Path(), required=False)
        @click.option("--engine", "engine", type=click.Path(), required=False)
        @click.option("--ide", "ide", default="VisualStudio2022")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def generate_files(ctx: Context, project: Optional[str], engine: Optional[str], ide: str, fmt: str) -> None:
            from .core.build import BuildSystem

            project_path = self._resolve_project_path(project)
            engine_path = self._resolve_engine_path(engine)
            result = BuildSystem(engine_path).generate_project_files(project_path=project_path, ide=ide)
            self._emit(ctx, result, fmt)

        return group

    def _create_config_command(self) -> click.Group:
        @click.group(name="config", help="Configuration management.")
        def group() -> None:
            pass

        @group.command(name="show")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def show_config(ctx: Context, fmt: str) -> None:
            self._emit(ctx, self.config, fmt)

        @group.command(name="set")
        @click.argument("key")
        @click.argument("value")
        @click.pass_context
        def set_config(ctx: Context, key: str, value: str) -> None:
            try:
                parsed = json.loads(value)
            except Exception:
                parsed = value
            self.config[key] = parsed
            self._save_config()
            self._emit(ctx, {"key": key, "value": parsed, "status": "updated"}, "text")

        return group

    def _create_status_command(self) -> click.Command:
        @click.command(name="status", help="Show environment status.")
        @click.option("--format", "fmt", type=click.Choice(["text", "json", "yaml"]), default="text")
        @click.pass_context
        def status_command(ctx: Context, fmt: str) -> None:
            status: Dict[str, Any] = {
                "cli_version": "1.0.0",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
            }
            try:
                status["resolved_engine"] = str(self._resolve_engine_path(None, required=False) or "")
            except Exception as exc:
                status["resolved_engine_error"] = str(exc)
            try:
                status["resolved_project"] = str(self._resolve_project_path(None, required=False) or "")
            except Exception as exc:
                status["resolved_project_error"] = str(exc)
            self._emit(ctx, status, fmt)

        return status_command

    def _create_version_command(self) -> click.Command:
        @click.command(name="version", help="Show version information.")
        def version_command() -> None:
            click.echo("Unreal Engine CLI v1.0.0")

        return version_command

    def _create_repl_command(self) -> click.Command:
        @click.command(name="repl", help="Start interactive REPL.")
        @click.option("--style", "style", type=click.Choice(["rich", "plain", "minimal"]), default="rich")
        @click.option("--prompt", "prompt", default="ue> ")
        @click.option("--history-file", "history_file", type=click.Path())
        @click.pass_context
        def repl_command(ctx: Context, style: str, prompt: str, history_file: Optional[str]) -> None:
            if REPLSkin is None or OutputStyle is None or create_default_commands is None:
                raise click.ClickException("REPL dependencies are unavailable in this environment.")
            commands = create_default_commands()
            repl = REPLSkin(
                commands=commands,
                prompt=prompt,
                style=OutputStyle(style),
                history_file=Path(history_file) if history_file else None,
            )
            repl.run()

        return repl_command

    def _create_help_command(self) -> click.Command:
        @click.command(name="help", help="Show help information.")
        @click.argument("command", required=False)
        @click.pass_context
        def help_command(ctx: Context, command: Optional[str]) -> None:
            if command:
                cmd = self.get_command(ctx, command)
                if not cmd:
                    click.echo(f"Command not found: {command}")
                    return
                click.echo(cmd.get_help(ctx))
                return
            click.echo(self._format_general_help(ctx))

        return help_command

    def _format_general_help(self, ctx: Context) -> str:
        commands = self.list_commands(ctx)
        text = [
            "Unreal Engine CLI - Command line interface for Unreal Engine 5",
            "",
            "Usage: ue-cli [OPTIONS] COMMAND [ARGS]...",
            "",
            "Commands:",
        ]
        for cmd in commands:
            cmd_obj = self.get_command(ctx, cmd)
            text.append(f"  {cmd:12} {cmd_obj.help if cmd_obj else ''}")
        return "\n".join(text)


@click.command(cls=UE5CLI, help="Unreal Engine CLI - Command line interface for Unreal Engine 5")
@click.version_option(version="1.0.0", prog_name="Unreal Engine CLI")
@click.option("--format", "format", type=click.Choice(["text", "json", "yaml"]), default="text")
@click.option("--no-color", "no_color", is_flag=True)
@click.option("--verbose", "verbose", is_flag=True)
@click.option("--quiet", "quiet", is_flag=True)
@click.pass_context
def cli(ctx: Context, format: str, no_color: bool, verbose: bool, quiet: bool) -> None:
    ctx.color = not no_color
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.format = format
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()


def main() -> None:
    """Main entry point."""

    cli()


if __name__ == "__main__":
    main()
