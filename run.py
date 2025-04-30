#!/usr/bin/env python
"""
Talent Matcher CLI

This script provides a unified command-line interface for all Talent Matcher operations.
"""

import argparse
import sys
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Talent Matcher CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate data command
    generate_parser = subparsers.add_parser("generate-data", help="Generate synthetic data")
    generate_parser.add_argument("--num-resumes", type=int, default=100, help="Number of resumes to generate")
    generate_parser.add_argument("--num-jobs", type=int, default=100, help="Number of job descriptions to generate")
    generate_parser.add_argument("--output-dir", type=str, default="data/generated", help="Directory to save generated data")
    generate_parser.add_argument("--resume-only", action="store_true", help="Generate only resumes")
    generate_parser.add_argument("--job-only", action="store_true", help="Generate only job descriptions")
    
    # Load data command
    load_parser = subparsers.add_parser("load-data", help="Load data into database")
    
    # Run backend command
    backend_parser = subparsers.add_parser("backend", help="Run the backend server")
    backend_parser.add_argument("--port", type=int, help="Port to run the backend on")
    backend_parser.add_argument("--host", type=str, help="Host to bind the backend to")
    backend_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    # Run frontend command
    frontend_parser = subparsers.add_parser("frontend", help="Run the frontend dev server")
    
    # Run tests command
    tests_parser = subparsers.add_parser("test", help="Run tests")
    tests_parser.add_argument("--coverage", action="store_true", help="Generate test coverage report")
    tests_parser.add_argument("path", nargs="?", default="tests/", help="Path to test directory or file")
    
    args = parser.parse_args()
    
    if args.command == "generate-data":
        from src.data_generation.cli import main as generate_main
        return generate_main(args)
    elif args.command == "load-data":
        from src.etl.cli import main as load_main
        return load_main()
    elif args.command == "backend":
        from src.backend.cli import run_backend
        return run_backend(args.port, args.host, args.debug)
    elif args.command == "frontend":
        from src.frontend.cli import run_frontend
        return run_frontend()
    elif args.command == "test":
        print("Running Talent Matcher Tests...")
        cmd = ["pytest", args.path]
        
        if args.coverage:
            cmd = ["pytest", args.path, "--cov=src", "--cov-report=term", "--cov-report=html:coverage_html"]
            print("Generating coverage report...")
        
        try:
            result = subprocess.run(cmd)
            if args.coverage:
                print("\nCoverage report generated in coverage_html/")
            return result.returncode
        except Exception as e:
            print(f"Error running tests: {str(e)}")
            return 1
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 