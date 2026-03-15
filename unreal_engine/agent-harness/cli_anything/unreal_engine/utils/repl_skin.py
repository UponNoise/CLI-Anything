#!/usr/bin/env python3
"""REPL interface for Unreal Engine CLI.

This module provides an interactive command-line interface with features like
command completion, history, colored output, help system, and error handling.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import os
import sys
import atexit
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
from enum import Enum

# readline is not available on Windows, handle gracefully
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from pygments.lexers.python import PythonLexer


class OutputStyle(Enum):
    """Output style enumeration."""
    PLAIN = "plain"
    RICH = "rich"
    MINIMAL = "minimal"


class CommandCompleter(Completer):
    """Command completer for REPL.
    
    Provides tab completion for commands and arguments.
    """
    
    def __init__(self, commands: Dict[str, Any]):
        """Initialize command completer.
        
        Args:
            commands: Dictionary of available commands.
        """
        self.commands = commands
        self._build_completion_dict()
    
    def _build_completion_dict(self) -> None:
        """Build completion dictionary from commands."""
        self.completion_dict = {}
        
        for cmd_name, cmd_info in self.commands.items():
            parts = cmd_name.split()
            current = self.completion_dict
            
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Store command info at leaf node
            current["__command__"] = cmd_info
    
    def get_completions(self, document, complete_event):
        """Get completions for current input.
        
        Args:
            document: Current document.
            complete_event: Completion event.
            
        Yields:
            Completion objects.
        """
        text = document.text_before_cursor
        words = text.split()
        
        if not words:
            # Show all top-level commands
            for cmd in self.completion_dict.keys():
                if not cmd.startswith("__"):
                    yield Completion(cmd, start_position=0)
            return
        
        # Navigate through command tree
        current = self.completion_dict
        for i, word in enumerate(words[:-1]):
            if word in current:
                current = current[word]
            else:
                return
        
        last_word = words[-1]
        
        # Find completions for last word
        for key in current.keys():
            if key.startswith("__"):
                continue
            
            if key.startswith(last_word):
                yield Completion(
                    key,
                    start_position=-len(last_word),
                    display=key,
                    display_meta=self._get_command_help(current.get(key, {}))
                )
    
    def _get_command_help(self, cmd_node: Dict) -> str:
        """Get command help text.
        
        Args:
            cmd_node: Command node dictionary.
            
        Returns:
            Help text for command.
        """
        if "__command__" in cmd_node:
            cmd_info = cmd_node["__command__"]
            if isinstance(cmd_info, dict) and "help" in cmd_info:
                return cmd_info["help"]
        return ""


class REPLSkin:
    """REPL interface for Unreal Engine CLI.
    
    Provides an interactive command-line interface with rich features.
    """
    
    def __init__(
        self,
        commands: Dict[str, Any],
        prompt: str = "ue> ",
        style: OutputStyle = OutputStyle.RICH,
        history_file: Optional[Path] = None
    ):
        """Initialize REPL interface.
        
        Args:
            commands: Dictionary of available commands.
            prompt: Prompt string.
            style: Output style.
            history_file: Path to history file.
        """
        self.commands = commands
        self.prompt = prompt
        self.style = style
        self.history_file = history_file or Path.home() / ".ue_cli_history"
        
        # Initialize console
        self.console = Console()
        
        # Initialize prompt session
        self.session = self._create_prompt_session()
        
        # Initialize completer
        self.completer = CommandCompleter(commands)
        
        # Command history
        self.history: List[str] = []
        self._load_history()
        
        # Key bindings
        self.key_bindings = self._create_key_bindings()
        
        # Session state
        self.running = True
        self.last_result = None
        
        # Register cleanup
        atexit.register(self._save_history)
    
    def _create_prompt_session(self) -> PromptSession:
        """Create prompt session.
        
        Returns:
            Configured PromptSession.
        """
        # Define style
        style = Style.from_dict({
            "prompt": "ansicyan bold",
            "command": "ansigreen",
            "error": "ansired",
            "warning": "ansiyellow",
            "info": "ansiblue",
            "success": "ansigreen",
        })
        
        # Create session
        session = PromptSession(
            message=self.prompt,
            style=style,
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            complete_while_typing=True,
            mouse_support=True,
        )
        
        return session
    
    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings.
        
        Returns:
            KeyBindings object.
        """
        kb = KeyBindings()
        
        @kb.add("c-c")
        def _(event):
            """Handle Ctrl+C."""
            event.app.exit(exception=KeyboardInterrupt)
        
        @kb.add("c-d")
        def _(event):
            """Handle Ctrl+D."""
            event.app.exit()
        
        @kb.add("tab")
        def _(event):
            """Handle Tab for completion."""
            b = event.app.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=True)
        
        return kb
    
    def _load_history(self) -> None:
        """Load command history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.print_warning(f"Failed to load history: {e}")
    
    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                for cmd in self.history[-1000:]:  # Keep last 1000 commands
                    f.write(f"{cmd}\n")
        except Exception as e:
            self.print_warning(f"Failed to save history: {e}")
    
    def print_error(self, message: str, details: Optional[str] = None) -> None:
        """Print error message.
        
        Args:
            message: Error message.
            details: Optional details.
        """
        if self.style == OutputStyle.RICH:
            error_text = Text(f"✗ {message}", style="bold red")
            if details:
                error_text.append(f"\n{details}", style="red")
            self.console.print(error_text)
        else:
            print(f"ERROR: {message}")
            if details:
                print(f"  {details}")
    
    def print_warning(self, message: str) -> None:
        """Print warning message.
        
        Args:
            message: Warning message.
        """
        if self.style == OutputStyle.RICH:
            self.console.print(f"[yellow]⚠ {message}[/yellow]")
        else:
            print(f"WARNING: {message}")
    
    def print_info(self, message: str) -> None:
        """Print info message.
        
        Args:
            message: Info message.
        """
        if self.style == OutputStyle.RICH:
            self.console.print(f"[blue]ℹ {message}[/blue]")
        else:
            print(f"INFO: {message}")
    
    def print_success(self, message: str) -> None:
        """Print success message.
        
        Args:
            message: Success message.
        """
        if self.style == OutputStyle.RICH:
            self.console.print(f"[green]✓ {message}[/green]")
        else:
            print(f"SUCCESS: {message}")
    
    def print_table(self, data: List[Dict[str, Any]], title: Optional[str] = None) -> None:
        """Print data as table.
        
        Args:
            data: List of dictionaries to display.
            title: Optional table title.
        """
        if not data:
            self.print_info("No data to display")
            return
        
        if self.style == OutputStyle.RICH:
            table = Table(title=title, show_header=True, header_style="bold magenta")
            
            # Add columns
            for key in data[0].keys():
                table.add_column(key, style="cyan")
            
            # Add rows
            for row in data:
                table.add_row(*[str(row.get(key, "")) for key in data[0].keys()])
            
            self.console.print(table)
        else:
            if title:
                print(f"\n{title}")
                print("=" * len(title))
            
            # Print header
            headers = list(data[0].keys())
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
            
            # Print rows
            for row in data:
                print(" | ".join(str(row.get(h, "")) for h in headers))
    
    def print_code(self, code: str, language: str = "python") -> None:
        """Print code with syntax highlighting.
        
        Args:
            code: Code to display.
            language: Programming language for syntax highlighting.
        """
        if self.style == OutputStyle.RICH:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            print(code)
    
    def show_help(self, command: Optional[str] = None) -> None:
        """Show help for commands.
        
        Args:
            command: Optional specific command to show help for.
        """
        if self.style == OutputStyle.RICH:
            if command:
                # Show help for specific command
                if command in self.commands:
                    cmd_info = self.commands[command]
                    panel = Panel.fit(
                        f"[bold]{command}[/bold]\n\n{cmd_info.get('help', 'No help available.')}",
                        title="Command Help",
                        border_style="blue"
                    )
                    self.console.print(panel)
                    
                    # Show usage if available
                    if "usage" in cmd_info:
                        self.console.print(f"\n[b]Usage:[/b] {cmd_info['usage']}")
                    
                    # Show examples if available
                    if "examples" in cmd_info:
                        self.console.print("\n[b]Examples:[/b]")
                        for example in cmd_info["examples"]:
                            self.console.print(f"  {example}")
                else:
                    self.print_error(f"Command not found: {command}")
            else:
                # Show all commands
                table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
                table.add_column("Command", style="green")
                table.add_column("Description", style="white")
                
                for cmd_name, cmd_info in sorted(self.commands.items()):
                    description = cmd_info.get("help", "No description").split("\n")[0]
                    table.add_row(cmd_name, description)
                
                self.console.print(table)
                self.console.print("\nType 'help <command>' for detailed help on a specific command.")
        else:
            if command:
                if command in self.commands:
                    cmd_info = self.commands[command]
                    print(f"\n{command}:")
                    print(f"  {cmd_info.get('help', 'No help available.')}")
                    
                    if "usage" in cmd_info:
                        print(f"\n  Usage: {cmd_info['usage']}")
                    
                    if "examples" in cmd_info:
                        print("\n  Examples:")
                        for example in cmd_info["examples"]:
                            print(f"    {example}")
                else:
                    print(f"Command not found: {command}")
            else:
                print("\nAvailable Commands:")
                print("=" * 50)
                for cmd_name, cmd_info in sorted(self.commands.items()):
                    description = cmd_info.get("help", "No description").split("\n")[0]
                    print(f"{cmd_name:30} {description}")
                print("\nType 'help <command>' for detailed help.")
    
    def show_progress(self, title: str = "Processing") -> Progress:
        """Show progress bar.
        
        Args:
            title: Progress title.
            
        Returns:
            Progress context manager.
        """
        if self.style == OutputStyle.RICH:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            )
        else:
            # Simple progress indicator for plain style
            class SimpleProgress:
                def __init__(self, title: str):
                    self.title = title
                    print(f"{title}...", end="", flush=True)
                
                def __enter__(self):
                    return self
                
                def __exit__(self, *args):
                    print(" Done!")
            
            return SimpleProgress(title)
    
    def parse_command(self, input_str: str) -> Tuple[str, List[str]]:
        """Parse command input.
        
        Args:
            input_str: Raw input string.
            
        Returns:
            Tuple of (command, args).
        """
        input_str = input_str.strip()
        if not input_str:
            return "", []
        
        # Handle quoted arguments
        import shlex
        try:
            parts = shlex.split(input_str)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")
        
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    def execute_command(self, command: str, args: List[str]) -> Any:
        """Execute a command.
        
        Args:
            command: Command name.
            args: Command arguments.
            
        Returns:
            Command result.
            
        Raises:
            ValueError: If command not found or invalid arguments.
        """
        if command not in self.commands:
            raise ValueError(f"Unknown command: {command}")
        
        cmd_info = self.commands[command]
        
        # Check if command is callable
        if "handler" not in cmd_info:
            raise ValueError(f"Command '{command}' has no handler")
        
        handler = cmd_info["handler"]
        
        try:
            # Execute command
            result = handler(*args)
            self.last_result = result
            return result
        except Exception as e:
            raise ValueError(f"Error executing command '{command}': {e}")
    
    def handle_special_commands(self, command: str, args: List[str]) -> bool:
        """Handle special built-in commands.
        
        Args:
            command: Command name.
            args: Command arguments.
            
        Returns:
            True if command was handled, False otherwise.
        """
        if command == "help":
            if args:
                self.show_help(args[0])
            else:
                self.show_help()
            return True
        
        elif command == "exit" or command == "quit":
            self.running = False
            self.print_info("Goodbye!")
            return True
        
        elif command == "clear":
            if self.style == OutputStyle.RICH:
                self.console.clear()
            else:
                os.system("cls" if os.name == "nt" else "clear")
            return True
        
        elif command == "history":
            if self.history:
                self.print_table(
                    [{"#": i + 1, "Command": cmd} for i, cmd in enumerate(self.history[-20:])],
                    "Recent Commands (last 20)"
                )
            else:
                self.print_info("No command history")
            return True
        
        elif command == "echo":
            if args:
                self.print_info(" ".join(args))
            return True
        
        elif command == "pwd":
            self.print_info(f"Current directory: {os.getcwd()}")
            return True
        
        elif command == "cd":
            if args:
                try:
                    os.chdir(args[0])
                    self.print_info(f"Changed directory to: {os.getcwd()}")
                except Exception as e:
                    self.print_error(f"Failed to change directory: {e}")
            else:
                self.print_info(f"Current directory: {os.getcwd()}")
            return True
        
        elif command == "ls" or command == "dir":
            try:
                files = os.listdir(".")
                data = []
                for f in files:
                    path = Path(f)
                    data.append({
                        "Name": f,
                        "Type": "Directory" if path.is_dir() else "File",
                        "Size": f"{path.stat().st_size:,}" if path.is_file() else "-",
                        "Modified": path.stat().st_mtime
                    })
                self.print_table(data, "Directory Contents")
            except Exception as e:
                self.print_error(f"Failed to list directory: {e}")
            return True
        
        return False
    
    def run(self) -> None:
        """Run the REPL main loop."""
        self.print_info("Unreal Engine CLI REPL")
        self.print_info("Type 'help' for available commands, 'exit' to quit")
        
        while self.running:
            try:
                # Get user input
                user_input = self.session.prompt(
                    completer=self.completer,
                    key_bindings=self.key_bindings
                ).strip()
                
                if not user_input:
                    continue
                
                # Add to history
                if user_input not in self.history[-10:]:  # Avoid duplicates in recent history
                    self.history.append(user_input)
                
                # Parse command
                try:
                    command, args = self.parse_command(user_input)
                except ValueError as e:
                    self.print_error(str(e))
                    continue
                
                # Handle special commands
                if self.handle_special_commands(command, args):
                    continue
                
                # Execute regular command
                try:
                    result = self.execute_command(command, args)
                    
                    # Display result if not None
                    if result is not None:
                        if isinstance(result, (list, tuple)) and all(
                            isinstance(item, dict) for item in result
                        ):
                            self.print_table(result)
                        elif isinstance(result, str):
                            if result.startswith("```") and result.endswith("```"):
                                # Code block
                                code = result[3:-3].strip()
                                self.print_code(code)
                            else:
                                self.print_info(result)
                        elif isinstance(result, dict):
                            self.print_table([result])
                        else:
                            self.print_info(str(result))
                    
                    self.print_success(f"Command '{command}' executed successfully")
                    
                except ValueError as e:
                    self.print_error(str(e))
                except Exception as e:
                    self.print_error(f"Unexpected error: {e}")
                    import traceback
                    if self.style == OutputStyle.RICH:
                        self.console.print_exception(show_locals=False)
                    else:
                        traceback.print_exc()
            
            except KeyboardInterrupt:
                self.print_info("\nInterrupted. Press Ctrl+D to exit.")
                continue
            except EOFError:
                self.running = False
                self.print_info("\nGoodbye!")
                break
            except Exception as e:
                self.print_error(f"REPL error: {e}")
                import traceback
                if self.style == OutputStyle.RICH:
                    self.console.print_exception(show_locals=False)
                else:
                    traceback.print_exc()
        
        # Save history on exit
        self._save_history()


def create_default_commands() -> Dict[str, Dict[str, Any]]:
    """Create default commands for REPL.
    
    Returns:
        Dictionary of default commands.
    """
    return {
        "project create": {
            "help": "Create a new Unreal Engine project.",
            "usage": "project create <name> [--template=<template>] [--output-dir=<path>]",
            "examples": [
                "project create MyGame --template=FirstPerson",
                "project create MyProject --output-dir=~/Projects"
            ],
            "handler": lambda *args: f"Creating project with args: {args}"
        },
        "project open": {
            "help": "Open an existing Unreal Engine project.",
            "usage": "project open <path/to/project.uproject>",
            "examples": ["project open C:/Projects/MyGame/MyGame.uproject"],
            "handler": lambda *args: f"Opening project: {args[0] if args else 'No path specified'}"
        },
        "project list": {
            "help": "List all projects in current directory.",
            "usage": "project list [--path=<path>]",
            "handler": lambda *args: [
                {"Name": "MyGame", "Path": "C:/Projects/MyGame", "Engine": "5.3"},
                {"Name": "TestProject", "Path": "C:/Projects/Test", "Engine": "5.2"},
            ]
        },
        "build": {
            "help": "Build Unreal Engine project.",
            "usage": "build [--target=<target>] [--platform=<platform>] [--configuration=<config>]",
            "examples": [
                "build --target=Editor --platform=Win64",
                "build --target=Game --configuration=Shipping"
            ],
            "handler": lambda *args: f"Building with args: {args}"
        },
        "build clean": {
            "help": "Clean build artifacts.",
            "usage": "build clean",
            "handler": lambda *args: "Cleaning build artifacts..."
        },
        "editor launch": {
            "help": "Launch Unreal Editor.",
            "usage": "editor launch [--map=<map>] [--game-mode=<mode>] [--headless]",
            "examples": [
                "editor launch --map=/Game/Maps/MyMap",
                "editor launch --headless"
            ],
            "handler": lambda *args: f"Launching editor with args: {args}"
        },
        "asset import": {
            "help": "Import asset into project.",
            "usage": "asset import <source> <destination>",
            "examples": ["asset import C:/Models/character.fbx /Game/Characters"],
            "handler": lambda *args: f"Importing asset: {args}"
        },
        "asset list": {
            "help": "List assets in project.",
            "usage": "asset list [--path=<path>]",
            "handler": lambda *args: [
                {"Name": "Character", "Path": "/Game/Characters/Hero", "Type": "SkeletalMesh"},
                {"Name": "Weapon", "Path": "/Game/Weapons/Sword", "Type": "StaticMesh"},
                {"Name": "Environment", "Path": "/Game/Environments/Forest", "Type": "Material"},
            ]
        },
        "plugin list": {
            "help": "List installed plugins.",
            "usage": "plugin list",
            "handler": lambda *args: [
                {"Name": "EditorScriptingUtilities", "Enabled": True, "Version": "1.0"},
                {"Name": "PythonScriptPlugin", "Enabled": True, "Version": "1.0"},
                {"Name": "AlembicImporter", "Enabled": False, "Version": "1.0"},
            ]
        },
        "plugin enable": {
            "help": "Enable a plugin.",
            "usage": "plugin enable <plugin-name>",
            "handler": lambda *args: f"Enabling plugin: {args[0] if args else 'No plugin specified'}"
        },
        "plugin disable": {
            "help": "Disable a plugin.",
            "usage": "plugin disable <plugin-name>",
            "handler": lambda *args: f"Disabling plugin: {args[0] if args else 'No plugin specified'}"
        },
        "cook": {
            "help": "Cook project content.",
            "usage": "cook [--platform=<platform>] [--maps=<maps>]",
            "handler": lambda *args: f"Cooking with args: {args}"
        },
        "package": {
            "help": "Package project for distribution.",
            "usage": "package [--platform=<platform>] [--configuration=<config>]",
            "handler": lambda *args: f"Packaging with args: {args}"
        },
        "config show": {
            "help": "Show current configuration.",
            "usage": "config show",
            "handler": lambda *args: {
                "Engine Path": "C:/Program Files/Epic Games/UE_5.3",
                "Project": "C:/Projects/MyGame",
                "Default Platform": "Win64",
                "Default Configuration": "Development",
            }
        },
        "config set": {
            "help": "Set configuration value.",
            "usage": "config set <key> <value>",
            "handler": lambda *args: f"Setting config: {args[0]} = {args[1] if len(args) > 1 else 'No value'}"
        },
        "status": {
            "help": "Show current status.",
            "usage": "status",
            "handler": lambda *args: {
                "Engine": "5.3.2",
                "Project": "MyGame",
                "Build Targets": "Editor, Game",
                "Plugins": "12 installed, 10 enabled",
                "Assets": "1,234 total",
            }
        },
        "version": {
            "help": "Show version information.",
            "usage": "version",
            "handler": lambda *args: {
                "UE CLI Version": "1.0.0",
                "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "Platform": sys.platform,
            }
        },
    }


def main() -> None:
    """Main entry point for REPL."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unreal Engine CLI REPL")
    parser.add_argument(
        "--style",
        choices=["rich", "plain", "minimal"],
        default="rich",
        help="Output style"
    )
    parser.add_argument(
        "--prompt",
        default="ue> ",
        help="Prompt string"
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Path to history file"
    )
    
    args = parser.parse_args()
    
    # Create commands
    commands = create_default_commands()
    
    # Create REPL
    repl = REPLSkin(
        commands=commands,
        prompt=args.prompt,
        style=OutputStyle(args.style),
        history_file=args.history_file
    )
    
    # Run REPL
    repl.run()


if __name__ == "__main__":
    main()