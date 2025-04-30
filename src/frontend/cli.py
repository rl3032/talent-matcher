#!/usr/bin/env python
"""
Frontend CLI for Talent Matcher

This module provides CLI functionality to launch the frontend development server.
Must be run from the project root directory.
"""

import os
import sys
import subprocess

def run_frontend():
    """Run the frontend development server."""
    # Make sure we're running from the project root
    if not os.path.exists(os.path.join(os.getcwd(), 'src')):
        print("Error: This script must be run from the project root directory")
        sys.exit(1)
        
    frontend_dir = os.path.join(os.getcwd(), 'src', 'frontend')
    
    if not os.path.exists(frontend_dir):
        print(f"Error: Frontend directory not found at {frontend_dir}")
        return False
    
    try:
        print("Starting Talent Matcher frontend development server...")
        
        # Execute npm run dev in the frontend directory
        subprocess.run(
            ["npm", "run", "dev"],
            cwd=frontend_dir
        )
        
        return True
        
    except KeyboardInterrupt:
        print("\nStopping frontend server...")
        return True
    except Exception as e:
        print(f"Error starting frontend: {str(e)}")
        return False

def main():
    """CLI entry point for running the frontend server."""
    success = run_frontend()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 