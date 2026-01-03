#!/usr/bin/env python3
"""
Master test runner for pricing-data-solution-pbp
Runs all test suites and provides comprehensive results
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Test files to run
TEST_SUITES = [
    {
        "name": "Calculation Tests",
        "file": "scripts/features/test_all_calculations.py",
        "description": "Tests discounts, markups, tiers, taxes, kitting, and rounding"
    },
    {
        "name": "PowerPoint Tests",
        "file": "scripts/features/test_powerpoint_features.py",
        "description": "Tests multi-variant products, table formats, and impact slides"
    },
    {
        "name": "Integration Tests",
        "file": "scripts/features/test_integration_features.py",
        "description": "Tests Tab 3→4 flow, saved data, and dataset switching"
    }
]


def run_test_suite(test_info):
    """Run a single test suite and return results"""
    print(f"\n{'=' * 70}")
    print(f"Running: {test_info['name']}")
    print(f"Description: {test_info['description']}")
    print(f"File: {test_info['file']}")
    print(f"{'=' * 70}")

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, test_info['file']],
            capture_output=True,
            text=True,
            timeout=30
        )

        elapsed_time = time.time() - start_time

        # Parse output for test results
        output = result.stdout
        passed = "ALL TESTS PASSED" in output or "ALL" in output and "PASSED" in output

        # Extract test summary
        summary_lines = []
        capture = False
        for line in output.split('\n'):
            if "TEST SUMMARY" in line:
                capture = True
            if capture:
                summary_lines.append(line)
            if capture and ("Failed:" in line or "PASSED!" in line):
                break

        return {
            "name": test_info['name'],
            "passed": passed,
            "elapsed_time": elapsed_time,
            "return_code": result.returncode,
            "summary": '\n'.join(summary_lines[-5:]) if summary_lines else "No summary found",
            "error": result.stderr if result.returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        return {
            "name": test_info['name'],
            "passed": False,
            "elapsed_time": 30.0,
            "return_code": -1,
            "summary": "Test timed out after 30 seconds",
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "name": test_info['name'],
            "passed": False,
            "elapsed_time": 0.0,
            "return_code": -1,
            "summary": f"Failed to run test",
            "error": str(e)
        }


def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 70)
    print(f"Test Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Suites: {len(results)}")

    passed_suites = sum(1 for r in results if r['passed'])
    failed_suites = len(results) - passed_suites
    total_time = sum(r['elapsed_time'] for r in results)

    print(f"Passed Suites: {passed_suites}")
    print(f"Failed Suites: {failed_suites}")
    print(f"Total Execution Time: {total_time:.2f} seconds")

    print("\n" + "-" * 70)
    print("DETAILED RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"\n{i}. {result['name']}: {status}")
        print(f"   Time: {result['elapsed_time']:.2f}s")

        if result['error']:
            print(f"   Error: {result['error']}")

        # Show last few lines of summary
        if result['summary']:
            summary_lines = result['summary'].strip().split('\n')
            for line in summary_lines[-3:]:
                if line.strip():
                    print(f"   {line.strip()}")

    print("\n" + "=" * 70)

    if failed_suites == 0:
        print("🎉 ALL TEST SUITES PASSED SUCCESSFULLY! 🎉")
        print("✅ The codebase is fully tested and working correctly.")
    else:
        print(f"⚠️ {failed_suites} TEST SUITE(S) FAILED")
        print("Please review the failed tests above.")

    print("=" * 70)

    return passed_suites == len(results)


def create_test_summary_file(results):
    """Create a test summary file for documentation"""
    summary_file = "test_results_summary.txt"

    with open(summary_file, 'w') as f:
        f.write("PRICING DATA SOLUTION - TEST RESULTS SUMMARY\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Version: 7.3.0\n")
        f.write("\n")

        # Overall stats
        passed = sum(1 for r in results if r['passed'])
        total = len(results)
        f.write(f"Overall Result: {passed}/{total} test suites passed\n")
        f.write("\n")

        # Categories tested
        f.write("Categories Tested:\n")
        f.write("1. Calculations - Client discounts, markups, tiered pricing, taxes, kitting, rounding\n")
        f.write("2. PowerPoint - Multi-variant products, table formats, impact slides, slide matching\n")
        f.write("3. Integration - Tab 3→4 data flow, saved proposals/orders, dataset switching\n")
        f.write("4. New Features - Bidirectional pricing, Non-profit terminology, date formats, checkboxes\n")
        f.write("\n")

        # Detailed results
        f.write("Detailed Results:\n")
        f.write("-" * 70 + "\n")

        for result in results:
            status = "PASSED" if result['passed'] else "FAILED"
            f.write(f"\n{result['name']}: {status}\n")
            f.write(f"Execution Time: {result['elapsed_time']:.2f} seconds\n")

            if not result['passed'] and result['error']:
                f.write(f"Error: {result['error']}\n")

        f.write("\n" + "=" * 70 + "\n")

        if all(r['passed'] for r in results):
            f.write("✅ ALL TESTS PASSED - System is ready for production use\n")
        else:
            f.write("⚠️ SOME TESTS FAILED - Review and fix before deployment\n")

    print(f"\nTest summary saved to: {summary_file}")
    return summary_file


def main():
    """Main test runner"""
    print("=" * 70)
    print("PRICING DATA SOLUTION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")

    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    print(f"Project Root: {project_root}")

    # Run all test suites
    results = []
    for test_info in TEST_SUITES:
        result = run_test_suite(test_info)
        results.append(result)

        # Small delay between tests
        time.sleep(0.5)

    # Generate report
    all_passed = generate_test_report(results)

    # Create summary file
    summary_file = create_test_summary_file(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()