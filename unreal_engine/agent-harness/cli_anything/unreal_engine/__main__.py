#!/usr/bin/env python3
"""Unreal Engine CLI - Main entry point.

This module provides the main entry point for the Unreal Engine CLI,
handling command-line argument parsing, error handling, and output formatting.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml

try:
    from .unreal_engine_cli import cli, OutputFormat
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from unreal_engine_cli import cli, OutputFormat


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging.
        quiet: Enable quiet mode.
    """
    import logging
    
    if quiet:
        logging.basicConfig(level=logging.ERROR)
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO)


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """Handle uncaught exceptions.
    
    Args:
        exc_type: Exception type.
        exc_value: Exception value.
        exc_traceback: Exception traceback.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't print traceback for keyboard interrupt
        sys.stderr.write("\nOperation cancelled by user\n")
        sys.exit(130)
    
    # Print error message
    sys.stderr.write(f"\nError: {exc_value}\n")
    
    # Print traceback in verbose mode
    if os.environ.get("UE_CLI_VERBOSE", "").lower() in ["1", "true", "yes"]:
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    sys.exit(1)


def load_config() -> Dict[str, Any]:
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


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary.
    """
    config_path = Path.home() / ".ue_cli" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


def format_output(data: Any, format_type: str, color: bool = True) -> str:
    """Format output according to specified format.
    
    Args:
        data: Data to format.
        format_type: Output format (text, json, yaml).
        color: Whether to use color in text output.
        
    Returns:
        Formatted output string.
    """
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif format_type == "yaml":
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    else:  # text
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                
                if color:
                    lines.append(f"\033[1;36m{key}:\033[0m {value_str}")
                else:
                    lines.append(f"{key}: {value_str}")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    item_str = format_output(item, "text", color)
                    if color:
                        lines.append(f"\033[1;33m[{i}]\033[0m\n{item_str}")
                    else:
                        lines.append(f"[{i}]\n{item_str}")
                else:
                    if color:
                        lines.append(f"\033[1;33m[{i}]\033[0m {item}")
                    else:
                        lines.append(f"[{i}] {item}")
            return "\n".join(lines)
        
        else:
            return str(data)


def print_banner() -> None:
    """Print CLI banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 Unreal Engine CLI v1.0.0                     ║
║        Command-line interface for Unreal Engine 5            ║
╚══════════════════════════════════════════════════════════════╝
"""
    click.echo(click.style(banner, fg="cyan", bold=True))


def print_help_summary() -> None:
    """Print help summary."""
    help_text = """
Quick Start:
  ue-cli project create MyGame           # Create a new project
  ue-cli build compile                   # Compile project
  ue-cli editor launch                   # Launch Unreal Editor
  ue-cli asset import model.fbx /Game    # Import asset
  ue-cli plugin list                     # List plugins
  ue-cli cook content                    # Cook content
  ue-cli package build                   # Package project

Common Options:
  --format text|json|yaml                # Output format
  --no-color                             # Disable colored output
  --verbose, -v                          # Enable verbose output
  --quiet, -q                            # Enable quiet mode
  --help                                 # Show help

For detailed help on a command: ue-cli help <command>
For interactive mode: ue-cli repl
"""
    click.echo(help_text)


def check_dependencies() -> bool:
    """Check if all dependencies are available.
    
    Returns:
        True if all dependencies are available, False otherwise.
    """
    missing_deps = []
    
    # Check required packages
    try:
        import click
    except ImportError:
        missing_deps.append("click>=8.1.0")
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("PyYAML>=6.0.0")
    
    try:
        from prompt_toolkit import __version__ as pt_version
    except ImportError:
        missing_deps.append("prompt-toolkit>=3.0.0")
    
    try:
        import rich
    except ImportError:
        missing_deps.append("rich>=13.0.0")
    
    if missing_deps:
        click.echo(click.style("Error: Missing dependencies:", fg="red", bold=True))
        for dep in missing_deps:
            click.echo(f"  - {dep}")
        click.echo("\nInstall with: pip install " + " ".join(missing_deps))
        return False
    
    return True


def check_python_version() -> bool:
    """Check Python version compatibility.
    
    Returns:
        True if Python version is compatible, False otherwise.
    """
    import sys
    
    if sys.version_info < (3, 10):
        click.echo(click.style(
            f"Error: Python 3.10 or higher is required (current: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})",
            fg="red", bold=True
        ))
        return False
    
    return True


def main() -> None:
    """Main entry point for Unreal Engine CLI."""
    # Set up exception handler
    sys.excepthook = handle_exception
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Parse command line arguments
    try:
        # Check for special commands
        if len(sys.argv) == 1:
            # No arguments, show banner and help
            print_banner()
            print_help_summary()
            sys.exit(0)
        
        elif len(sys.argv) == 2 and sys.argv[1] in ["--version", "-V"]:
            # Show version
            click.echo("Unreal Engine CLI v1.0.0")
            sys.exit(0)
        
        elif len(sys.argv) == 2 and sys.argv[1] in ["--help", "-h"]:
            # Show help
            print_banner()
            cli(["--help"])
            sys.exit(0)
        
        elif len(sys.argv) == 2 and sys.argv[1] == "repl":
            # Start REPL
            print_banner()
            try:
                from .utils.repl_skin import REPLSkin, OutputStyle, create_default_commands
            except ImportError:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from utils.repl_skin import REPLSkin, OutputStyle, create_default_commands
            
            commands = create_default_commands()
            repl = REPLSkin(
                commands=commands,
                prompt="ue> ",
                style=OutputStyle.RICH,
                history_file=Path.home() / ".ue_cli_history"
            )
            repl.run()
            sys.exit(0)
        
        else:
            # Run CLI
            cli()
    
    except click.exceptions.Exit as e:
        # Click already handled the exit
        sys.exit(e.exit_code)
    
    except Exception as e:
        # Handle other exceptions
        click.echo(click.style(f"Error: {e}", fg="red", bold=True))
        
        # Show traceback in verbose mode
        if os.environ.get("UE_CLI_VERBOSE", "").lower() in ["1", "true", "yes"]:
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()