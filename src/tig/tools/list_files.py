import os
import time
from pathlib import Path
from textwrap import dedent
from typing import Dict

import pathspec
from ordered_set import OrderedSet


def _are_paths_equal(path1: Path, path2: Path) -> bool:
    """Checks if two paths point to the same location, resolving symlinks."""
    try:
        # Resolve both paths to handle symlinks, .., ., and case-insensitivity (on Windows)
        return path1.resolve(strict=True) == path2.resolve(strict=True)
    except FileNotFoundError:
        # If either path doesn't exist, they can't be equal in the resolved sense
        return False
    except Exception:
        # Catch other potential errors during resolution (e.g., permission issues)
        # Fallback to comparing absolute paths directly if resolution fails broadly
        try:
            abs1 = path1.absolute()
            abs2 = path2.absolute()
            return abs1 == abs2
        except Exception:  # Final fallback
            return False


def load_gitignore(path="."):
    default_patterns = [
        "node_modules",
        "__pycache__",
        "env",
        "venv",
        ".venv",  # Common Python venv name
        "target/dependency",  # Rust/Java?
        "build/dependencies",  # Gradle?
        "dist",
        "out",
        "build",  # General build dir
        "bin",  # Common compiled output dir
        "obj",  # Common compiled output dir
        "bundle",
        "vendor",
        "tmp",
        "temp",
        "deps",
        "pkg",
        "Pods",  # iOS Cocoapods
        ".git",  # Git internal directory
        ".hg",  # Mercurial
        ".svn",  # Subversion
        ".vscode",  # VSCode settings
        ".idea",  # JetBrains IDE settings
        ".DS_Store",  # macOS metadata
    ]
    gitignore_patterns = []
    gitignore_path = Path(path) / ".gitignore"
    if gitignore_path.exists():
        with gitignore_path.open() as f:
            gitignore_patterns = f.read().splitlines()
    return pathspec.PathSpec.from_lines(
        "gitwildmatch", gitignore_patterns + default_patterns
    )


def list_files_recursively_respecting_gitignore(root_dir=".", timeout_sec=10.0):
    root_dir_path = Path(root_dir)
    spec = load_gitignore(root_dir)
    all_files: OrderedSet[str] = OrderedSet([])
    start_time = time.monotonic()
    for dirpath, sub_dirs, filenames in os.walk(root_dir_path):
        if time.monotonic() - start_time > timeout_sec:
            print(
                f"\nWarning: Globbing timed out after {timeout_sec} seconds, returning partial results.\n",
            )
            break
        sub_dirs[:] = [
            d for d in sub_dirs if spec is None or not spec.match_file(str(d))
        ]
        sub_dirs[:] = [d for d in sub_dirs if not d.startswith(".")]
        for filename in filenames:
            filepath = Path(dirpath) / filename
            rel_path = filepath.relative_to(root_dir_path)
            rel_dir_path = Path(dirpath).relative_to(root_dir_path)
            if spec is None or not spec.match_file(str(rel_path)):
                all_files.append(str(rel_dir_path) + "/")
                all_files.append(str(rel_path))
    return all_files


def list_files_non_recursively_respecting_gitignore(root_dir="."):
    root_dir_path = Path(root_dir)
    spec = load_gitignore(root_dir)
    all_files: OrderedSet[str] = OrderedSet([])
    for item in root_dir_path.iterdir():
        if item.is_dir():
            rel_path = item.relative_to(root_dir_path)
            if spec is None or not spec.match_file(str(rel_path)):
                all_files.append(str(rel_path) + "/")
        else:
            rel_path = item.relative_to(root_dir_path)
            if spec is None or not spec.match_file(str(rel_path)):
                all_files.append(str(rel_path))
    return all_files


def format_list_files(
    dir_path: str, file_paths: OrderedSet[str], limit_reached: bool
) -> str:
    """
    Formats the list of file paths for output.

    Args:
        file_paths: A list of file paths.
        limit_reached: A boolean indicating if the limit was reached.

    Returns:
        A string containing the formatted file paths.
    """
    if len(file_paths) == 0:
        return f"No files found in {dir_path}."
    formatted_files_list = f'Files and directories in "{dir_path}":\n'
    formatted_files_list += "\n".join(file_paths)
    if limit_reached:
        formatted_files_list += "\n(File list truncated. Use list_files on specific subdirectories if you need to explore further.)"
    return formatted_files_list


def list_files(arguments: Dict) -> str:
    """
    Lists files and directories within a given path with options for recursion,
    ignoring patterns, and limits.

    Args:
        dir_path: The starting directory path.
        recursive: Whether to list files recursively.

    Returns:
        A string containing:
        - A list of absolute file/directory paths (directories end with '/').
    """
    if "path" not in arguments:
        return "Error: Missing 'path' argument."
    if "recursive" not in arguments:
        return "Error: Missing 'recursive' argument."

    dir_path = arguments["path"]
    recursive = arguments["recursive"]
    limit = 200

    try:
        # Use pathlib for easier path manipulation
        # Resolve the path to make it absolute and handle symlinks/../.
        # strict=True ensures the path exists
        absolute_path = Path(dir_path).resolve(strict=True)
    except FileNotFoundError:
        return f"Error: Directory not found: {dir_path}"
    except Exception as e:
        return f"Error resolving path {dir_path}: {e}"

    if not absolute_path.is_dir():
        return f"Error: Path is not a directory: {absolute_path}"

    # --- Security Checks: Prevent listing root or home ---
    root_path = Path(absolute_path.anchor)
    home_dir_path = Path.home().resolve()  # Resolve home dir for robust comparison

    if _are_paths_equal(absolute_path, root_path):
        return "Error: Listing the root directory is not allowed."

    if _are_paths_equal(absolute_path, home_dir_path):
        return "Error: Listing the home directory is not allowed."

    # --- Perform Listing ---
    if recursive:
        file_paths = list_files_recursively_respecting_gitignore(str(absolute_path))

    else:
        file_paths = list_files_non_recursively_respecting_gitignore(str(absolute_path))

    return format_list_files(dir_path, file_paths, len(file_paths) > limit)
