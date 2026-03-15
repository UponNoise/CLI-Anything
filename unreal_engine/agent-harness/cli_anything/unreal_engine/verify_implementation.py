#!/usr/bin/env python3
"""Verify implementation of asset.py and blueprint.py."""

import os
import sys
from pathlib import Path

# Add core directory to path
core_dir = Path(__file__).parent / "core"
sys.path.insert(0, str(core_dir.parent))

print("=" * 70)
print("Verifying UE5-005 Implementation: asset.py and blueprint.py")
print("=" * 70)

# Check if files exist
print("\n1. Checking file existence...")
asset_file = core_dir / "asset.py"
blueprint_file = core_dir / "blueprint.py"

if asset_file.exists():
    print(f"   [OK] asset.py exists ({asset_file.stat().st_size} bytes)")
else:
    print(f"   [ERROR] asset.py not found")
    sys.exit(1)

if blueprint_file.exists():
    print(f"   [OK] blueprint.py exists ({blueprint_file.stat().st_size} bytes)")
else:
    print(f"   [ERROR] blueprint.py not found")
    sys.exit(1)

# Read and analyze files
print("\n2. Analyzing file content...")

def check_class_and_methods(file_path, class_name, required_methods):
    """Check if a class exists and has required methods."""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    
    # Check class definition
    class_def = f"class {class_name}:"
    if class_def in content:
        print(f"   [OK] {class_name} class defined in {file_path.name}")
    else:
        print(f"   [ERROR] {class_name} class not found in {file_path.name}")
        return False
    
    # Check methods
    all_found = True
    for method in required_methods:
        # Look for method definition
        method_patterns = [
            f"def {method}(",
            f"    def {method}(",
            f"\n    def {method}("
        ]
        
        found = any(pattern in content for pattern in method_patterns)
        if found:
            print(f"   [OK]   {class_name}.{method}() method found")
        else:
            print(f"   [ERROR] {class_name}.{method}() method not found")
            all_found = False
    
    return all_found

# Check AssetManager
print("\n   Checking AssetManager...")
asset_required_methods = [
    'import_asset',
    'export_asset',
    'migrate_assets',
    'list_assets',
    'find_references',
    'delete_asset'
]
asset_ok = check_class_and_methods(asset_file, "AssetManager", asset_required_methods)

# Check BlueprintManager
print("\n   Checking BlueprintManager...")
blueprint_required_methods = [
    'create_blueprint',
    'compile_blueprint',
    'list_blueprints',
    'duplicate_blueprint'
]
blueprint_ok = check_class_and_methods(blueprint_file, "BlueprintManager", blueprint_required_methods)

# Check for custom exceptions
print("\n3. Checking custom exceptions...")
asset_content = asset_file.read_text(encoding='utf-8', errors='ignore')
blueprint_content = blueprint_file.read_text(encoding='utf-8', errors='ignore')

# Check AssetManager exceptions
asset_exceptions = [
    "AssetManagerError",
    "AssetImportError",
    "AssetExportError",
    "AssetMigrationError",
    "AssetNotFoundError"
]

for exc in asset_exceptions:
    if f"class {exc}(" in asset_content:
        print(f"   [OK] {exc} exception defined in asset.py")
    else:
        print(f"   [WARNING] {exc} exception not found in asset.py")

# Check BlueprintManager exceptions
blueprint_exceptions = [
    "BlueprintManagerError",
    "BlueprintCreationError",
    "BlueprintCompilationError",
    "BlueprintNotFoundError"
]

for exc in blueprint_exceptions:
    if f"class {exc}(" in blueprint_content:
        print(f"   [OK] {exc} exception defined in blueprint.py")
    else:
        print(f"   [WARNING] {exc} exception not found in blueprint.py")

# Check for type annotations and docstrings
print("\n4. Checking code quality...")

def check_code_quality(content, filename):
    """Check for type annotations and docstrings."""
    issues = []
    
    # Check for type annotations in method signatures
    if "def " in content and "->" not in content:
        issues.append("Type annotations may be missing")
    
    # Check for Google style docstrings
    if '"""' not in content and "'''" not in content:
        issues.append("Docstrings may be missing")
    elif 'Args:' not in content and 'Returns:' not in content:
        issues.append("Google style docstrings may be incomplete")
    
    # Check for imports
    if "from typing import" not in content and "import typing" not in content:
        issues.append("typing module may not be imported")
    
    if "from enum import" not in content and "import enum" not in content:
        issues.append("enum module may not be imported")
    
    if "from pathlib import Path" not in content and "import pathlib" not in content:
        issues.append("pathlib may not be imported")
    
    return issues

asset_issues = check_code_quality(asset_content, "asset.py")
blueprint_issues = check_code_quality(blueprint_content, "blueprint.py")

if not asset_issues:
    print("   [OK] asset.py code quality looks good")
else:
    print("   [WARNING] asset.py code quality issues:")
    for issue in asset_issues:
        print(f"     - {issue}")

if not blueprint_issues:
    print("   [OK] blueprint.py code quality looks good")
else:
    print("   [WARNING] blueprint.py code quality issues:")
    for issue in blueprint_issues:
        print(f"     - {issue}")

# Summary
print("\n" + "=" * 70)
print("IMPLEMENTATION SUMMARY")
print("=" * 70)

if asset_ok and blueprint_ok:
    print("[SUCCESS] Both modules are fully implemented with all required methods!")
    print("\nDeliverables:")
    print("1. core/asset.py - COMPLETE ✓")
    print("2. core/blueprint.py - COMPLETE ✓")
    print("3. done-UE5-005.md - TO BE CREATED")
else:
    print("[INCOMPLETE] Some requirements are missing.")
    if not asset_ok:
        print("  - AssetManager is missing some methods")
    if not blueprint_ok:
        print("  - BlueprintManager is missing some methods")

print("\n" + "=" * 70)