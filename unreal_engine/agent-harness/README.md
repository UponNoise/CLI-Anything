# Unreal Engine CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful command-line interface for Unreal Engine 5, designed to streamline game development workflows and automate common tasks.

## Features

- **Project Management**: Create, open, and configure UE5 projects
- **Build System**: Compile targets with UBT/UAT integration
- **Editor Control**: Launch and control the Unreal Editor
- **Asset Management**: Import, export, and manage game assets
- **Blueprint Operations**: Create, compile, and manage Blueprints
- **Plugin Management**: Install, enable, and configure plugins
- **Packaging**: Cook, stage, and package projects for distribution
- **Interactive REPL**: Rich command-line interface with auto-completion

## Current Scope and Limitations

- This harness focuses on a stable CLI surface and file-structure workflows.
- Some editor-deep operations are currently scaffolded and require a running UE environment or future backend wiring.
- Certain asset and blueprint operations use simulated filesystem behavior to enable offline testing.
- For production automation, prefer commands that already invoke native UE build/cook tooling (UBT/UAT) and validate outputs in your environment.

## Installation

### From PyPI (Recommended)

```bash
pip install unreal-engine-cli
```

### From Source

```bash
# Clone the repository
git clone https://github.com/oc-cliany/unreal-engine-cli.git
cd unreal-engine-cli

# Install in development mode
pip install -e .
```

### Development Installation

```bash
# Clone and install with development dependencies
git clone https://github.com/oc-cliany/unreal-engine-cli.git
cd unreal-engine-cli

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Quick Start

### Basic Usage

```bash
# Show help
ue-cli --help

# List available commands
ue-cli --list

# Start interactive REPL
ue-cli repl

# Create a new project
ue-cli project create MyProject --template=FirstPerson

# Build project
ue-cli build --target=Editor --platform=Win64

# Launch editor
ue-cli editor launch --map=/Game/Maps/MyMap
```

### Interactive REPL

The CLI includes a powerful interactive REPL with features like:

- **Auto-completion**: Tab-completion for commands and arguments
- **Command History**: Navigate through previous commands
- **Syntax Highlighting**: Color-coded output for better readability
- **Inline Help**: Access help without leaving the REPL

```bash
# Start the REPL
ue-cli repl

# In the REPL:
ue> project create MyGame --template=ThirdPerson
ue> build --target=Game --platform=Win64
ue> editor launch --headless
ue> exit
```

## Command Reference

### Project Commands

```bash
# Create a new project
ue-cli project create <name> [--template=<template>] [--output-dir=<path>]

# Open existing project
ue-cli project open <path/to/project.uproject>

# List project templates
ue-cli project templates

# Get project info
ue-cli project info
```

### Build Commands

```bash
# Build a target
ue-cli build --target=<target> [--platform=<platform>] [--configuration=<config>]

# Clean build
ue-cli build clean

# Rebuild
ue-cli build rebuild

# Generate project files
ue-cli build generate
```

### Editor Commands

```bash
# Launch editor
ue-cli editor launch [--map=<map>] [--game-mode=<mode>] [--headless]

# Run commandlet
ue-cli editor commandlet <commandlet> [args...]

# Get editor status
ue-cli editor status
```

### Asset Commands

```bash
# Import asset
ue-cli asset import <source> <destination>

# Export asset
ue-cli asset export <asset-path> <output-dir>

# List assets
ue-cli asset list [--path=<path>]

# Find asset references
ue-cli asset references <asset-path>
```

### Plugin Commands

```bash
# List plugins
ue-cli plugin list

# Enable plugin
ue-cli plugin enable <plugin-name>

# Disable plugin
ue-cli plugin disable <plugin-name>

# Install plugin
ue-cli plugin install <source>
```

## Configuration

### Global Configuration

Create a configuration file at `~/.ue_cli/config.yaml`:

```yaml
# Default engine path
engine_path: "C:/Program Files/Epic Games/UE_5.3"

# Default project settings
default_project:
  template: "Blank"
  output_dir: "~/Projects"

# Build settings
build:
  default_platform: "Win64"
  default_configuration: "Development"

# Editor settings
editor:
  default_map: "/Game/Maps/DefaultMap"
  headless_by_default: false

# Logging
logging:
  level: "INFO"
  file: "~/.ue_cli/ue_cli.log"
```

### Project Configuration

Each project can have its own `.ue_cli_project.yaml`:

```yaml
# Project-specific settings
project_name: "MyGame"
engine_version: "5.3"

# Build targets
build_targets:
  - name: "Editor"
    platform: "Win64"
    configuration: "Development"
  
  - name: "Game"
    platform: "Win64"
    configuration: "Shipping"

# Asset directories
asset_directories:
  - "/Game/Characters"
  - "/Game/Environments"
  - "/Game/UI"
```

## Development

### Project Structure

```
unreal-engine-cli/
├── cli_anything/
│   └── unreal_engine/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Entry point
│       ├── unreal_engine_cli.py # Main CLI definition
│       ├── core/                # Core modules
│       │   ├── project.py       # Project management
│       │   ├── build.py         # Build system
│       │   ├── editor.py        # Editor control
│       │   ├── level.py         # Level operations
│       │   ├── asset.py         # Asset management
│       │   ├── blueprint.py     # Blueprint operations
│       │   ├── plugin.py        # Plugin management
│       │   ├── cook.py          # Cook and packaging
│       │   └── session.py       # Session management
│       ├── utils/               # Utility modules
│       │   ├── ue_backend.py    # UE backend interface
│       │   ├── path_manager.py  # Path management
│       │   ├── config_parser.py # Config file parsing
│       │   └── repl_skin.py     # REPL interface
│       └── tests/               # Test modules
│           ├── test_project.py
│           ├── test_build.py
│           └── test_integration.py
├── setup.py                     # Package configuration
├── requirements.txt             # Runtime dependencies
├── README.md                    # This file
└── pyproject.toml              # Build system configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=cli_anything.unreal_engine

# Run specific test module
pytest tests/test_project.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code
black .
ruff format .

# Lint code
ruff check .
mypy cli_anything/unreal_engine

# Run pre-commit hooks
pre-commit run --all-files
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/oc-cliany/unreal-engine-cli.git
cd unreal-engine-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Setup pre-commit
pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Unreal Engine](https://www.unrealengine.com/) by Epic Games
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) for the REPL interface
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## Support

- **Documentation**: [Read the Docs](https://unreal-engine-cli.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/oc-cliany/unreal-engine-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/oc-cliany/unreal-engine-cli/discussions)
- **Email**: contact@oc-cliany.org

---

Made with ❤️ by the OC-CLIANY Project