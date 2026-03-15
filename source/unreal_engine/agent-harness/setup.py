#!/usr/bin/env python3
"""Setup configuration for Unreal Engine CLI package.

This module provides the package configuration for pip installation,
dependency management, entry point configuration, and metadata settings.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from setuptools import setup, find_packages


def read_file(filepath: Path) -> str:
    """Read file content as string.
    
    Args:
        filepath: Path to the file to read.
        
    Returns:
        File content as string.
        
    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return filepath.read_text(encoding="utf-8")


def get_version() -> str:
    """Extract version from package __init__.py.
    
    Returns:
        Package version string.
        
    Raises:
        RuntimeError: If version cannot be found.
    """
    init_path = Path(__file__).parent / "cli_anything" / "unreal_engine" / "__init__.py"
    content = read_file(init_path)
    
    # Match __version__ = "x.y.z"
    version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if version_match:
        return version_match.group(1)
    
    raise RuntimeError("Unable to find version string in __init__.py")


def get_long_description() -> str:
    """Read long description from README.md.
    
    Returns:
        Long description for package.
    """
    readme_path = Path(__file__).parent / "README.md"
    try:
        return read_file(readme_path)
    except FileNotFoundError:
        return "Unreal Engine CLI - Command line interface for Unreal Engine 5"


def get_requirements() -> List[str]:
    """Read requirements from requirements.txt.
    
    Returns:
        List of requirement strings.
    """
    requirements_path = Path(__file__).parent / "requirements.txt"
    try:
        content = read_file(requirements_path)
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.startswith("#")
        ]
    except FileNotFoundError:
        # Default requirements if requirements.txt doesn't exist
        return [
            "click>=8.1.0",
            "pydantic>=2.0.0",
            "colorama>=0.4.6",
            "prompt-toolkit>=3.0.0",
            "rich>=13.0.0",
            "pygments>=2.15.0",
        ]


def get_extra_requirements() -> Dict[str, List[str]]:
    """Get extra requirements for different use cases.
    
    Returns:
        Dictionary mapping extra requirement names to lists of packages.
    """
    return {
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=2.0.0",
            "sphinx-autodoc-typehints>=1.0.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    }


def main() -> None:
    """Main setup function."""
    
    # Package metadata
    name = "unreal-engine-cli"
    version = get_version()
    description = "Command line interface for Unreal Engine 5"
    long_description = get_long_description()
    long_description_content_type = "text/markdown"
    
    # Author information
    author = "OC-CLIANY Project"
    author_email = "contact@oc-cliany.org"
    url = "https://github.com/oc-cliany/unreal-engine-cli"
    
    # Classifiers
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Topic :: Games/Entertainment",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
    
    # Keywords
    keywords = [
        "unreal-engine",
        "unreal-engine-5",
        "cli",
        "command-line",
        "game-development",
        "automation",
        "build-tools",
    ]
    
    # Package configuration
    packages = find_packages(where=".", exclude=["tests", "tests.*", "docs", "docs.*"])
    package_dir = {"": "."}
    
    # Entry points
    entry_points = {
        "console_scripts": [
            "ue-cli=cli_anything.unreal_engine.__main__:main",
            "unreal-engine-cli=cli_anything.unreal_engine.__main__:main",
        ],
    }
    
    # Requirements
    install_requires = get_requirements()
    extras_require = get_extra_requirements()
    
    # Python requirements
    python_requires = ">=3.10"
    
    # Setup configuration
    setup(
        # Basic information
        name=name,
        version=version,
        description=description,
        long_description=long_description,
        long_description_content_type=long_description_content_type,
        
        # Author information
        author=author,
        author_email=author_email,
        url=url,
        
        # Project URLs
        project_urls={
            "Bug Reports": f"{url}/issues",
            "Source": url,
            "Documentation": f"{url}/blob/main/README.md",
        },
        
        # Classification
        classifiers=classifiers,
        keywords=keywords,
        
        # Package configuration
        packages=packages,
        package_dir=package_dir,
        include_package_data=True,
        
        # Entry points
        entry_points=entry_points,
        
        # Dependencies
        install_requires=install_requires,
        extras_require=extras_require,
        python_requires=python_requires,
        
        # Additional metadata
        license="MIT",
        platforms=["Windows", "macOS", "Linux"],
        
        # Scripts
        scripts=[],
        
        # Data files
        data_files=[],
        
        # Zip safe
        zip_safe=False,
    )


if __name__ == "__main__":
    main()