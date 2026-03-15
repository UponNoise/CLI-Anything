#!/usr/bin/env python3
"""Test runner for UE5 CLI integration and E2E tests.

This script runs the test suites and provides a summary report.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def run_test_suite(test_file: str) -> Dict[str, Any]:
    """Run a test suite and return results.
    
    Args:
        test_file: Path to test file.
        
    Returns:
        Dictionary with test results.
    """
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    # Run pytest
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Parse output
        output = result.stdout + result.stderr
        
        # Count test results
        passed = output.count("PASSED")
        failed = output.count("FAILED")
        errors = output.count("ERROR")
        
        return {
            "file": test_file,
            "exit_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": output,
            "success": result.returncode == 0
        }
        
    except Exception as e:
        return {
            "file": test_file,
            "exit_code": 1,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "output": str(e),
            "success": False
        }

def generate_report(results: List[Dict[str, Any]]) -> str:
    """Generate a test report.
    
    Args:
        results: List of test results.
        
    Returns:
        Report string.
    """
    total_tests = sum(r["passed"] + r["failed"] + r["errors"] for r in results)
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    
    report = []
    report.append("=" * 60)
    report.append("UE5 CLI TEST REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary
    report.append("SUMMARY")
    report.append("-" * 40)
    report.append(f"Total Test Suites: {len(results)}")
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Passed: {total_passed} ({total_passed/max(total_tests, 1)*100:.1f}%)")
    report.append(f"Failed: {total_failed}")
    report.append(f"Errors: {total_errors}")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS")
    report.append("-" * 40)
    
    for result in results:
        status = "[PASS]" if result["success"] else "[FAIL]"
        report.append(f"{status} {result['file']}")
        report.append(f"  Tests: {result['passed']} passed, {result['failed']} failed, {result['errors']} errors")
        report.append(f"  Exit Code: {result['exit_code']}")
        
        if not result["success"]:
            # Show first few lines of error output
            error_lines = result["output"].split('\n')
            error_summary = [line for line in error_lines if any(
                keyword in line.lower() for keyword in ["error", "fail", "traceback"]
            )][:5]
            
            if error_summary:
                report.append("  Errors:")
                for line in error_summary:
                    report.append(f"    {line}")
        
        report.append("")
    
    # Overall status
    report.append("OVERALL STATUS")
    report.append("-" * 40)
    
    if total_failed == 0 and total_errors == 0:
        report.append("[PASS] ALL TESTS PASSED")
        report.append("The UE5 CLI integration and E2E tests are working correctly.")
    else:
        report.append("[FAIL] SOME TESTS FAILED")
        report.append(f"{total_failed} tests failed, {total_errors} errors occurred.")
        report.append("Please check the detailed output above.")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

def main() -> None:
    """Main function to run all tests."""
    test_files = [
        "test_integration.py",
        "test_full_e2e.py"
    ]
    
    # Check if test files exist
    existing_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_files.append(test_file)
        else:
            print(f"Warning: Test file not found: {test_file}")
    
    if not existing_files:
        print("No test files found!")
        sys.exit(1)
    
    # Run tests
    results = []
    for test_file in existing_files:
        result = run_test_suite(test_file)
        results.append(result)
    
    # Generate and print report
    report = generate_report(results)
    print(report)
    
    # Save report to file
    report_file = "test_execution_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Exit with appropriate code
    total_failed = sum(r["failed"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    
    if total_failed > 0 or total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()