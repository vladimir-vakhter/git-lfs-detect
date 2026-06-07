#!/usr/bin/env python3
"""
Git LFS Detector - Tracks large files with Git LFS.

Traverses a directory to find files larger than a specified size
and adds them to git lfs tracking if not already tracked.

Usage: python git_lfs_detect.py <directory_path> [--size SIZE_MB]
"""

import os
import sys
import subprocess
import fnmatch


def format_size(bytes_size):
    """Format byte size to human-readable format."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


def find_git_root(start_path='.'):
    """Find the git repository root directory."""
    current = os.path.abspath(start_path)

    while current != os.path.dirname(current):  # Stop at filesystem root
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        current = os.path.dirname(current)

    return None


def parse_gitattributes(gitattributes_path):
    """Parse .gitattributes file and return patterns that are tracked with git lfs."""
    lfs_patterns = set()

    if not os.path.exists(gitattributes_path):
        return lfs_patterns

    try:
        with open(gitattributes_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Check if this pattern is tracked by git lfs
                if 'filter=lfs' in line:
                    # Extract the pattern (first part before whitespace)
                    pattern = line.split()[0]
                    lfs_patterns.add(pattern)
    except Exception as e:
        print(f"Error reading .gitattributes: {e}", file=sys.stderr)

    return lfs_patterns


def is_file_tracked(file_path, lfs_patterns, git_root):
    """Check if a file matches any of the git lfs tracking patterns."""
    file_name = os.path.basename(file_path)

    # Normalize file path to relative from git root
    try:
        rel_path = os.path.relpath(file_path, git_root)
    except ValueError:
        rel_path = file_path

    for pattern in lfs_patterns:
        # Handle glob patterns like *.psd
        if fnmatch.fnmatch(file_name, pattern):
            return True
        # Check full relative path for exact matches or glob patterns
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Direct string comparison for exact file paths
        if rel_path == pattern:
            return True

    return False


def find_large_files(directory, size_threshold_mb=50):
    """Find all files larger than the specified size threshold."""
    size_threshold_bytes = size_threshold_mb * 1024 * 1024
    large_files = []

    try:
        for root, dirs, files in os.walk(directory):
            # Skip git directory
            if '.git' in dirs:
                dirs.remove('.git')

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > size_threshold_bytes:
                        large_files.append(file_path)
                except OSError as e:
                    print(f"Warning: Could not access {file_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error traversing directory: {e}", file=sys.stderr)

    return large_files


def track_file_with_lfs(file_path, git_root):
    """Execute git lfs track command for a single file."""
    # Make path relative to git root for cleaner tracking
    try:
        rel_path = os.path.relpath(file_path, git_root)
    except ValueError:
        # If can't make relative, use absolute
        rel_path = file_path

    try:
        file_size = os.path.getsize(file_path)
        size_str = format_size(file_size)

        result = subprocess.run(
            ['git', 'lfs', 'track', '--filename', rel_path],
            capture_output=True,
            text=True,
            check=False,
            cwd=git_root
        )

        if result.returncode == 0:
            print(f"✓ Tracked: {rel_path} ({size_str})")
            return True
        else:
            print(f"✗ Failed to track {rel_path}: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"✗ Error tracking {rel_path}: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python git_lfs_detect.py <directory_path> [--size SIZE_MB]", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    size_threshold_mb = 50  # Default threshold

    # Parse optional --size argument
    if len(sys.argv) > 2:
        if sys.argv[2] == '--size' and len(sys.argv) > 3:
            try:
                size_threshold_mb = int(sys.argv[3])
            except ValueError:
                print(f"Error: SIZE_MB must be an integer, got '{sys.argv[3]}'", file=sys.stderr)
                sys.exit(1)
        else:
            print("Usage: python git_lfs_detect.py <directory_path> [--size SIZE_MB]", file=sys.stderr)
            sys.exit(1)

    # Validate directory exists
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Find git root
    git_root = find_git_root(directory)
    if not git_root:
        print("Error: Not in a git repository", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {directory} for files larger than {size_threshold_mb} MB...\n")

    # Find .gitattributes in the git root
    gitattributes_path = os.path.join(git_root, '.gitattributes')
    lfs_patterns = parse_gitattributes(gitattributes_path)

    if lfs_patterns:
        print(f"Found {len(lfs_patterns)} existing git lfs patterns in .gitattributes")
    else:
        print("No existing .gitattributes file or no git lfs patterns found")

    print("Scanning for large files...", end='', flush=True)
    # Find large files
    large_files = find_large_files(directory, size_threshold_mb)
    print(f" found {len(large_files)} file(s) larger than {size_threshold_mb} MB" if large_files else " done")

    if not large_files:
        print(f"No files larger than {size_threshold_mb} MB found.")
        return

    print()

    # Separate already tracked from new files
    already_tracked = [f for f in large_files if is_file_tracked(f, lfs_patterns, git_root)]
    files_to_track = [f for f in large_files if not is_file_tracked(f, lfs_patterns, git_root)]

    # Report already tracked files
    if already_tracked:
        print(f"\nAlready tracked ({len(already_tracked)} file(s)):")
        for file_path in already_tracked:
            try:
                rel_path = os.path.relpath(file_path, git_root)
            except ValueError:
                rel_path = file_path
            file_size = os.path.getsize(file_path)
            print(f"  {rel_path} ({format_size(file_size)})")

    if not files_to_track:
        print("\nNothing to change.")
        return

    print(f"\nTracking {len(files_to_track)} new file(s) with git lfs...\n")

    # Track each file
    tracked_count = 0
    for file_path in files_to_track:
        if track_file_with_lfs(file_path, git_root):
            tracked_count += 1

    print(f"\nSuccessfully tracked {tracked_count}/{len(files_to_track)} files")


if __name__ == '__main__':
    main()
