# MLOps Lab 1 — Answers

## Question 1

`uv init` creates the basic structure of a Python project. `.python-version` specifies the Python version (3.11), `pyproject.toml` contains the project configuration, Python requirement, and dependencies, `main.py` is a starter Python file, and `README.md` is used for project documentation.

## Question 2

DVC creates the `.dvc` directory and `.dvcignore` file. The `.dvc` directory contains DVC configuration and internal files. The `.dvc/config` file contains the DVC repository configuration, while `.dvc/.gitignore` prevents DVC internal files from being tracked unnecessarily. `.dvcignore` specifies files that DVC should ignore.

The files needed by Git should be committed to GitHub, including the DVC configuration files and `.dvcignore`. The actual large datasets will be stored by DVC rather than directly in GitHub.