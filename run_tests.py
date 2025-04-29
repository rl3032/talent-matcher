#!/usr/bin/env python
"""
Test Runner Script for Talent Matcher

This script runs all unit tests and integration tests for the Talent Matcher application.
It also calculates and reports test coverage.
"""

import unittest
import sys
import coverage
import os


def run_all_tests():
    """Run all unit and integration tests"""
    # Start the coverage measurement
    cov = coverage.Coverage(
        source=["src/backend"],
        omit=[
            "*/__pycache__/*",
            "*/tests/*",
            "*/.pytest_cache/*"
        ]
    )
    cov.start()

    # Create the test suite
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # Add all tests from the tests directory
    test_suite.addTests(test_loader.discover("tests", pattern="test_*.py"))

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Stop coverage measurement and report
    cov.stop()
    cov.save()
    
    # Report the coverage
    print("\nCoverage Report:")
    cov.report()
    
    # Generate HTML report
    if not os.path.exists('coverage_html'):
        os.makedirs('coverage_html')
    cov.html_report(directory='coverage_html')
    print(f"\nDetailed HTML coverage report saved to: {os.path.abspath('coverage_html/index.html')}")
    
    # Return the test result to set exit code
    return result


if __name__ == "__main__":
    print("Running Talent Matcher Tests...")
    result = run_all_tests()
    
    # Set the exit code based on the test result
    if not result.wasSuccessful():
        sys.exit(1) 