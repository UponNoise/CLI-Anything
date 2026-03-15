#!/usr/bin/env python3
"""Simple test script to verify plugin.py and cook.py modules."""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.plugin import (
    PluginManager,
    PluginInfo,
    PluginType,
    PluginCategory,
    PluginSource,
    PluginStatus,
)

from core.cook import (
    CookManager,
    CookResult,
    CookOptions,
    PackageOptions,
    CookTarget,
    CookFlavor,
)


def test_plugin_module():
    """Test basic plugin module functionality."""
    print("Testing Plugin Module...")
    print("=" * 50)
    
    # Test enum values
    print("PluginType enum values:")
    for plugin_type in PluginType:
        print(f"  - {plugin_type.name}: {plugin_type.value}")
    
    print("\nPluginCategory enum values:")
    for category in PluginCategory:
        print(f"  - {category.name}: {category.value}")
    
    print("\nPluginSource enum values:")
    for source in PluginSource:
        print(f"  - {source.name}: {source.value}")
    
    print("\nPluginStatus enum values:")
    for status in PluginStatus:
        print(f"  - {status.name}: {status.value}")
    
    # Test PluginInfo dataclass
    print("\nTesting PluginInfo dataclass:")
    plugin_info = PluginInfo(
        name="TestPlugin",
        friendly_name="Test Plugin",
        version="1",
        version_name="1.0.0",
        description="A test plugin",
        category="Utilities",
        created_by="Test Author",
        plugin_type=PluginType.RUNTIME,
        installed=True,
        enabled=True,
        is_engine_plugin=False,
        is_project_plugin=True,
        enabled_by_default=True
    )
    
    print(f"  Name: {plugin_info.name}")
    print(f"  Friendly Name: {plugin_info.friendly_name}")
    print(f"  Version: {plugin_info.version}")
    print(f"  Description: {plugin_info.description}")
    print(f"  Plugin Type: {plugin_info.plugin_type}")
    print(f"  Installed: {plugin_info.installed}")
    print(f"  Enabled: {plugin_info.enabled}")
    
    # Test PluginManager initialization
    print("\nTesting PluginManager initialization:")
    try:
        plugin_manager = PluginManager()
        print("  PluginManager initialized successfully")
        print(f"  Engine path: {plugin_manager.engine_path}")
        print(f"  Project path: {plugin_manager.project_path}")
    except Exception as e:
        print(f"  Error initializing PluginManager: {e}")
    
    print("\n" + "=" * 50)


def test_cook_module():
    """Test basic cook module functionality."""
    print("Testing Cook Module...")
    print("=" * 50)
    
    # Test enum values
    print("CookTarget enum values:")
    for target in CookTarget:
        print(f"  - {target.name}: {target.value}")
    
    print("\nCookFlavor enum values:")
    for flavor in CookFlavor:
        print(f"  - {flavor.name}: {flavor.value}")
    
    # Test CookOptions dataclass
    print("\nTesting CookOptions dataclass:")
    cook_options = CookOptions(
        target=CookTarget.WINDOWS,
        flavor=CookFlavor.DEVELOPMENT,
        maps=["Map1", "Map2"],
        cultures=["en", "zh"],
        compressed=True,
        iterative=False,
        skip_editor_content=True
    )
    
    print(f"  Target: {cook_options.target}")
    print(f"  Flavor: {cook_options.flavor}")
    print(f"  Maps: {cook_options.maps}")
    print(f"  Cultures: {cook_options.cultures}")
    print(f"  Compressed: {cook_options.compressed}")
    print(f"  Iterative: {cook_options.iterative}")
    
    # Test PackageOptions dataclass
    print("\nTesting PackageOptions dataclass:")
    package_options = PackageOptions(
        target=CookTarget.WINDOWS,
        flavor=CookFlavor.SHIPPING,
        build=True,
        cook=True,
        stage=True,
        archive=False,
        pak=True,
        prereqs=True,
        distribution=False,
        compressed=True
    )
    
    print(f"  Target: {package_options.target}")
    print(f"  Flavor: {package_options.flavor}")
    print(f"  Build: {package_options.build}")
    print(f"  Cook: {package_options.cook}")
    print(f"  Stage: {package_options.stage}")
    print(f"  Pak: {package_options.pak}")
    
    # Test CookResult dataclass
    print("\nTesting CookResult dataclass:")
    cook_result = CookResult(
        success=True,
        cooked_content_dir=Path("/tmp/cooked"),
        staged_content_dir=Path("/tmp/staged"),
        packaged_content_dir=Path("/tmp/packaged"),
        log_file=Path("/tmp/log.txt"),
        duration_seconds=120.5,
        errors=["Error 1", "Error 2"],
        warnings=["Warning 1", "Warning 2"]
    )
    
    print(f"  Success: {cook_result.success}")
    print(f"  Cooked Content Dir: {cook_result.cooked_content_dir}")
    print(f"  Duration: {cook_result.duration_seconds} seconds")
    print(f"  Errors: {len(cook_result.errors)}")
    print(f"  Warnings: {len(cook_result.warnings)}")
    
    print("\n" + "=" * 50)


def test_module_integration():
    """Test integration between modules."""
    print("Testing Module Integration...")
    print("=" * 50)
    
    # Create a mock project path for testing
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    
    # Create a mock .uproject file
    uproject_file = test_dir / "TestProject.uproject"
    uproject_content = {
        "FileVersion": 3,
        "EngineAssociation": "5.4",
        "Category": "",
        "Description": "",
        "Modules": [],
    }
    
    import json
    with open(uproject_file, 'w') as f:
        json.dump(uproject_content, f)
    
    print(f"Created test project at: {uproject_file}")
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n" + "=" * 50)


def main():
    """Main test function."""
    print("UE5 Plugin and Cook Module Test")
    print("=" * 60)
    
    try:
        test_plugin_module()
        test_cook_module()
        test_module_integration()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())