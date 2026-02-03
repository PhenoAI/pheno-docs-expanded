#!/usr/bin/env python3
import json
import os
import glob

# Source directory with the updated markdown files
source_dir = "/home/ec2-user/workspace/pheno-docs/markdowns-expanded"
output_dir = "/home/ec2-user/workspace/pheno-docs-expanded/pheno_knowledge_base_expanded/datasets"

for subdir in glob.glob(f"{source_dir}/*/"):
    # Get the dataset name from the directory
    dataset_name = os.path.basename(os.path.normpath(subdir))
    md_file = os.path.join(subdir, f"{dataset_name}.md")
    
    # Special case for CBC which has a different filename
    if dataset_name == "019-blood_tests_CBC":
        md_file = os.path.join(subdir, "019-blood_test_CBC.md")
        dataset_name = "019-cbc"
    
    ipynb_file = os.path.join(output_dir, f"{dataset_name}.ipynb")
    
    if os.path.exists(md_file):
        # Read the markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Split into lines for the notebook
        # IMPORTANT: Each line in Jupyter notebooks should end with \n
        lines = md_content.split('\n')
        formatted_lines = [line + '\n' for line in lines[:-1]]
        if lines[-1]:  # If last line is not empty, add it with \n
            formatted_lines.append(lines[-1] + '\n')
        
        # Create notebook structure
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": formatted_lines
                }
            ],
            "metadata": {
                "language_info": {
                    "name": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        # Write to ipynb file
        with open(ipynb_file, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        
        print(f"Converted {md_file} -> {ipynb_file}")

print("Conversion complete!")
