# MLOps Lab 1 — Answers

## Question 1

`uv init` creates the basic structure of a Python project. `.python-version` specifies the Python version (3.11), `pyproject.toml` contains the project configuration, Python requirement, and dependencies, `main.py` is a starter Python file, and `README.md` is used for project documentation.

## Question 2

DVC creates the `.dvc` directory and `.dvcignore` file. The `.dvc` directory contains DVC configuration and internal files. The `.dvc/config` file contains the DVC repository configuration, while `.dvc/.gitignore` prevents DVC internal files from being tracked unnecessarily. `.dvcignore` specifies files that DVC should ignore.

The files needed by Git should be committed to GitHub, including the DVC configuration files and `.dvcignore`. The actual large datasets will be stored by DVC rather than directly in GitHub.

## Question 3

When using `--global`, the DVC credentials are stored in the user's global DVC configuration rather than in the project repository. This keeps the credentials outside the Git repository.

Another option is `--local`, which stores the settings in the project's local DVC configuration. The credentials should **never be pushed to GitHub**, especially because the repository is public. Only non-sensitive DVC configuration should be committed.

## Question 4

After running `dvc add data`, DVC added `/data` to `.gitignore`. This tells Git to ignore the actual data folder so that the large Food-11 dataset is not tracked or uploaded directly to GitHub. Instead, DVC tracks the dataset and creates `data.dvc`, which is a small file containing information used by DVC to identify and manage the data.

## Question 5

Yes, DVC created a `data.dvc` file. It contains metadata about the tracked dataset, including its MD5 hash, total size, number of files, hashing method, and path. In this case, the dataset contains 16,643 files and is about 1.19 GB. The `data.dvc` file does not contain the actual images; it allows DVC to identify and manage the correct version of the data.

## Question 6

The code and Git-tracked project files are stored in GitHub, while the actual Food-11 dataset is stored using DVC in DagsHub Storage. The file data.dvc is stored in Git and acts as a pointer containing metadata that identifies the DVC-tracked data. In DagsHub, the data is recognized as DVC-tracked data and can be accessed through the Data/DVC interface.