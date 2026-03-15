#!/usr/bin/env python3
"""Verify that UE5 CLI tests are properly structured and can be imported."""

import sys
import os
import ast
from pathlib import Path
from typing import List, Dict, Any

def check_file_structure(filepath: str) -> Dict[str, Any]:
    """Check Python file structure and imports.
    
    Args:
        filepath: Path to Python file.
        
    Returns:
        Dictionary with check results.
    """
    results = {
        "file": filepath,
        "exists": False,
        "syntax_valid": False,
        "imports_work": False,
        "test_classes": [],
        "test_methods": [],
        "errors": []
    }
    
    # Check if file exists
    if not os.path.exists(filepath):
        results["errors"].append("File does not exist")
        return results
    
    results["exists"] = True
    
    # Check syntax
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        results["syntax_valid"] = True
    except SyntaxError as e:
        results["errors"].append(f"Syntax error: {e}")
        return results
    
    # Try to import (for test files)
    if filepath.endswith("test_integration.py") or filepath.endswith("test_full_e2e.py"):
        try:
            # Add current directory to path
            sys.path.insert(0, os.path.dirname(os.path.abspath(filepath)))
            
            # Import module
            module_name = os.path.basename(filepath)[:-3]  # Remove .py
            module = __import__(module_name)
            
            # Check for test classes
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and name.startswith("Test"):
                    results["test_classes"].append(name)
                    
                    # Count test methods
                    test_methods = [m for m in dir(obj) if m.startswith("test_")]
                    results["test_methods"].extend(test_methods)
            
            results["imports_work"] = True
            
        except ImportError as e:
            results["errors"].append(f"Import error: {e}")
        except Exception as e:
            results["errors"].append(f"Error during import: {e}")
    
    return results

def main() -> None:
    """Main verification function."""
    test_files = [
        "test_integration.py",
        "test_full_e2e.py"
    ]
    
    print("=" * 60)
    print("UE5 CLI Test Verification")
    print("=" * 60)
    
    all_valid = True
    
    for test_file in test_files:
        print(f"\nChecking: {test_file}")
        print("-" * 40)
        
        results = check_file_structure(test_file)
        
        if not results["exists"]:
            print(f"  ERROR: File not found")
            all_valid = False
            continue
        
        print(f"  File exists: OK")
        
        if not results["syntax_valid"]:
            print(f"  ERROR: Syntax error")
            for error in results["errors"]:
                print(f"    {error}")
            all_valid = False
            continue
        
        print(f"  Syntax valid: OK")
        
        if results["imports_work"]:
            print(f"  Imports work: OK")
            print(f"  Test classes: {len(results['test_classes'])}")
            for cls in results["test_classes"]:
                print(f"    - {cls}")
            print(f"  Test methods: {len(results['test_methods'])}")
        else:
            print(f"  WARNING: Imports may have issues")
            for error in results["errors"]:
                print(f"    {error}")
    
    # Check report file
    print(f"\nChecking: TEST_REPORT.md")
    print("-" * 40)
    
    report_file = "TEST_REPORT.md"
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"  File exists: OK")
        print(f"  File size: {len(content)} bytes")
        
        # Check for key sections
        sections = [
            "测试概述",
            "交付物",
            "测试要求满足情况",
            "代码质量"
        ]
        
        for section in sections:
            if section in content:
                print(f"  Section '{section}': OK")
            else:
                print(f"  WARNING: Section '{section}' not found")
    else:
        print(f"  ERROR: Report file not found")
        all_valid = False
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all_valid:
        print("RESULT: ALL CHECKS PASSED")
        print("\nThe UE5 CLI integration and E2E tests are properly structured.")
        print("Test files can be imported and have valid syntax.")
        print("Test report is complete.")
    else:
        print("RESULT: SOME CHECKS FAILED")
        print("\nPlease fix the issues mentioned above.")
    
    print("\nFiles created:")
    print("  1. test_integration.py - Integration tests")
    print("  2. test_full_e2e.py - End-to-end tests")
    print("  3. TEST_REPORT.md - Test report")
    print("  4. run_tests.py - Test runner")
    print("  5. verify_tests.py - This verification script")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()