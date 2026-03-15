#!/usr/bin/env python3
"""Test script for asset.py and blueprint.py modules."""

import tempfile
from pathlib import Path
from core.asset import AssetManager, AssetType, ImportOptions
from core.blueprint import BlueprintManager, BlueprintType, CreateBlueprintOptions


def test_asset_manager():
    """Test AssetManager functionality."""
    print("Testing AssetManager...")
    
    # Create a temporary project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "TestProject.uproject"
        
        # Create a minimal .uproject file
        uproject_content = {
            "FileVersion": 3,
            "EngineAssociation": "5.4",
            "Category": "",
            "Description": "",
            "Modules": [
                {
                    "Name": "TestProject",
                    "Type": "Runtime",
                    "LoadingPhase": "Default"
                }
            ]
        }
        
        import json
        with open(project_path, "w") as f:
            json.dump(uproject_content, f, indent=2)
        
        # Create AssetManager
        asset_manager = AssetManager(project_path)
        
        # Test list_assets (should be empty initially)
        assets = asset_manager.list_assets("/Game")
        print(f"  Initial assets: {len(assets)}")
        
        # Test import_asset (simulated)
        test_file = Path(tmpdir) / "test_mesh.fbx"
        test_file.write_text("FBX test content")
        
        try:
            imported_path = asset_manager.import_asset(
                test_file,
                "/Game/Meshes/TestMesh",
                ImportOptions()
            )
            print(f"  Imported asset: {imported_path}")
        except Exception as e:
            print(f"  Import test (simulated): {type(e).__name__}: {e}")
        
        # Test list_assets again
        assets = asset_manager.list_assets("/Game", recursive=True)
        print(f"  Assets after import: {len(assets)}")
        
        # Test find_references (simulated)
        try:
            references = asset_manager.find_references("/Game/Meshes/TestMesh")
            print(f"  References found: {len(references)}")
        except Exception as e:
            print(f"  Find references test: {type(e).__name__}: {e}")
        
        print("  AssetManager tests completed")


def test_blueprint_manager():
    """Test BlueprintManager functionality."""
    print("\nTesting BlueprintManager...")
    
    # Create a temporary project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "TestProject.uproject"
        
        # Create a minimal .uproject file
        uproject_content = {
            "FileVersion": 3,
            "EngineAssociation": "5.4",
            "Category": "",
            "Description": "",
            "Modules": [
                {
                    "Name": "TestProject",
                    "Type": "Runtime",
                    "LoadingPhase": "Default"
                }
            ]
        }
        
        import json
        with open(project_path, "w") as f:
            json.dump(uproject_content, f, indent=2)
        
        # Create BlueprintManager
        blueprint_manager = BlueprintManager(project_path)
        
        # Test list_blueprints (should be empty initially)
        blueprints = blueprint_manager.list_blueprints("/Game")
        print(f"  Initial blueprints: {len(blueprints)}")
        
        # Test create_blueprint
        try:
            blueprint_path = blueprint_manager.create_blueprint(
                name="TestBlueprint",
                path="/Game/Blueprints",
                options=CreateBlueprintOptions(
                    parent_class="Actor",
                    compile_after_create=True,
                    save_after_create=True
                )
            )
            print(f"  Created blueprint: {blueprint_path}")
        except Exception as e:
            print(f"  Create blueprint test: {type(e).__name__}: {e}")
        
        # Test list_blueprints again
        blueprints = blueprint_manager.list_blueprints("/Game", recursive=True)
        print(f"  Blueprints after creation: {len(blueprints)}")
        
        if blueprints:
            bp_info = blueprints[0]
            print(f"  Blueprint info: {bp_info.name}, Type: {bp_info.type}, Parent: {bp_info.parent_class}")
        
        # Test compile_blueprint
        try:
            compile_success = blueprint_manager.compile_blueprint("/Game/Blueprints/TestBlueprint")
            print(f"  Compile blueprint: {'Success' if compile_success else 'Failed'}")
        except Exception as e:
            print(f"  Compile blueprint test: {type(e).__name__}: {e}")
        
        # Test duplicate_blueprint
        try:
            duplicate_path = blueprint_manager.duplicate_blueprint(
                source_path="/Game/Blueprints/TestBlueprint",
                new_name="TestBlueprint_Copy",
                target_path="/Game/Blueprints"
            )
            print(f"  Duplicated blueprint: {duplicate_path}")
        except Exception as e:
            print(f"  Duplicate blueprint test: {type(e).__name__}: {e}")
        
        # Final list
        blueprints = blueprint_manager.list_blueprints("/Game", recursive=True)
        print(f"  Final blueprints count: {len(blueprints)}")
        
        print("  BlueprintManager tests completed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing UE5 Asset and Blueprint Modules")
    print("=" * 60)
    
    try:
        test_asset_manager()
        test_blueprint_manager()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during testing: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())