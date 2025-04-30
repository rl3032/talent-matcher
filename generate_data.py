#!/usr/bin/env python
"""
Data Generation Script for Talent Matcher

This script generates synthetic resume and job description datasets for
development, testing, and demonstration purposes.
"""

import argparse
import sys
from pathlib import Path
from src.data_generation.generators import ResumeGenerator, JobGenerator

def main():
    """Generate a complete dataset of resumes and job descriptions."""
    parser = argparse.ArgumentParser(description="Generate resume and job description datasets")
    parser.add_argument("--num-resumes", type=int, default=100, help="Number of resumes to generate")
    parser.add_argument("--num-jobs", type=int, default=100, help="Number of job descriptions to generate")
    parser.add_argument("--output-dir", type=str, default="data/generated", help="Directory to save generated data")
    parser.add_argument("--resume-only", action="store_true", help="Generate only resumes")
    parser.add_argument("--job-only", action="store_true", help="Generate only job descriptions")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_path = Path("data") / args.output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate resumes if requested
    if not args.job_only:
        print(f"Generating {args.num_resumes} resumes...")
        resume_generator = ResumeGenerator(output_dir=args.output_dir)
        resume_generator.generate(args.num_resumes)
        resume_generator.create_combined_dataset("data/resume_dataset.json")
    
    # Generate job descriptions if requested
    if not args.resume_only:
        print(f"Generating {args.num_jobs} job descriptions...")
        job_generator = JobGenerator(output_dir=args.output_dir)
        job_generator.generate(args.num_jobs)
        job_generator.create_combined_dataset("data/job_dataset.json")
    
    print("Dataset generation complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 