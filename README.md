# Git LFS Detect

Automatically detect and track large files with Git LFS based on size thresholds.

## Purpose

This script traverses a directory and its subdirectories to identify files larger than 50 MB and automatically registers them with Git LFS, if not already tracked.

## Features

- **Configurable size threshold**: Identifies files larger than a specified size (default: 50 MB)
- **Existing tracking awareness**: Reads `.gitattributes` and skips files already tracked with Git LFS
- **Individual file tracking**: Adds files one by one using `git lfs track --filename` rather than directory-based patterns, allowing for precise control and incremental updates
- **Git root detection**: Automatically locates the git repository root for proper path handling
- **Detailed reporting**: Shows progress with success/failure indicators for each tracked file

## Requirements

- Python 3.6+
- Git with Git LFS installed
- A git repository

## Installation

To make the script callable by name from anywhere:

```bash
sudo ln -s /path/to/git_lfs_detect/git_lfs_detect.py /usr/local/bin/git-lfs-detect
```

Replace `/path/to/git_lfs_detect` with the actual path to the script directory.

## Usage

After installation, call it directly:

```bash
git-lfs-detect <directory_path> [--size SIZE_MB]
```

Or run the script directly:

```bash
python git_lfs_detect.py <directory_path> [--size SIZE_MB]
```

**Arguments:**
- `directory_path`: The directory to scan for large files (required)
- `--size SIZE_MB`: File size threshold in megabytes (optional, default: 50)

**Examples:**
```bash
git-lfs-detect ./data                    # Use default 50 MB threshold
git-lfs-detect . --size 100              # Use 100 MB threshold
python git_lfs_detect.py ./data --size 200  # Use 200 MB threshold
```

## How It Works

1. Scans the specified directory recursively, skipping `.git` folder
2. Identifies all files larger than the specified threshold (default: 50 MB)
3. Reads the existing `.gitattributes` file (if present) to check current Git LFS tracking patterns
4. Filters out files already tracked by comparing against existing patterns
5. For each untracked large file, executes `git lfs track --filename <file_path>` individually
6. Reports the number of successfully tracked files

## Output Example

**Case 1: New files to track**
```
Scanning ./data for files larger than 50 MB...

Found 1 existing git lfs pattern in .gitattributes
Scanning for large files... found 3 file(s) larger than 50 MB

Tracking 2 new file(s) with git lfs...

✓ Tracked: data/model.bin (245.5 MB)
✓ Tracked: data/archive.tar.gz (523.2 MB)

Successfully tracked 2/2 files
```

**Case 2: All files already tracked**
```
Scanning ./data for files larger than 50 MB...

Found 2 existing git lfs patterns in .gitattributes
Scanning for large files... found 2 file(s) larger than 50 MB

Already tracked (2 file(s)):
  data/model.bin (245.5 MB)
  data/archive.tar.gz (523.2 MB)

Nothing to change.
```

## Notes

- Files are added one by one for fine-grained control, not as bulk directory patterns
- Paths are converted to relative paths from the git repository root before tracking
- Already-tracked files are automatically detected and skipped to avoid redundant operations
