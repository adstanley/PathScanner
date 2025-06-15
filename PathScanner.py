#!/usr/bin/env python3
"""
Path enumeration utilities for scanning directories and handling file operations.

This module provides functions for efficiently scanning directories and 
working with file paths across multiple scripts.
"""

import logging
from pathlib import Path
from collections import defaultdict
from typing import Union, Tuple, List, Optional

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback for when tqdm is not available
    def tqdm(iterable, **kwargs):
        return iterable

# Configure logging
logger = logging.getLogger(__name__)

PathLike = Union[Path, str]


def scan_directory(
    directory: PathLike, 
    show_progress: bool = False,
    resolve_paths: bool = False,
    include_hidden: bool = True
) -> Tuple[List[Path], List[Path]]:
    """
    Scan directory for files and folders in a single pass.
    
    Args:
        directory: Path to directory to scan
        show_progress: Show progress bar (requires tqdm)
        resolve_paths: Return resolved/absolute paths
        include_hidden: Include hidden files/folders (starting with .)
    
    Returns:
        Tuple of (files, folders) lists, both sorted
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
        PermissionError: If permission denied
    """
    path = Path(directory)
    
    # Validation
    if not path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"'{directory}' is not a directory")
    
    # Use defaultdict to collect items by type
    items = defaultdict(list)
    
    try:
        # Create iterator with optional progress bar
        iterator = path.iterdir()
        if show_progress and HAS_TQDM:
            iterator = tqdm(iterator, desc=f"Scanning {path.name}", unit="items")
        elif show_progress and not HAS_TQDM:
            logger.warning("tqdm not available, progress bar disabled")
        
        # Single iteration through directory
        for item in iterator:
            try:
                # Skip hidden files if requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Resolve path if requested
                if resolve_paths:
                    item = item.resolve()
                
                items[item.is_file()].append(item)
                
            except (PermissionError, OSError) as e:
                logger.warning(f"Skipping '{item}': {e}")
                continue
        
    except PermissionError:
        raise PermissionError(f"Permission denied accessing '{directory}'")
    
    # Extract files and folders (True key = files, False key = folders)
    files = sorted(items[True])
    folders = sorted(items[False])
    
    return files, folders


def scan_directory_simple(directory: PathLike) -> Tuple[List[Path], List[Path]]:
    """
    Simple directory scan without extra features.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        Tuple of (files, folders) lists, both sorted
    """
    return scan_directory(directory, show_progress=False, resolve_paths=False)


def scan_directory_recursive(
    directory: PathLike,
    max_depth: Optional[int] = None,
    show_progress: bool = False
) -> Tuple[List[Path], List[Path]]:
    """
    Recursively scan directory and all subdirectories.
    
    Args:
        directory: Root directory to scan
        max_depth: Maximum recursion depth (None for unlimited)
        show_progress: Show progress bar
        
    Returns:
        Tuple of (all_files, all_folders) lists
    """
    path = Path(directory)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"'{directory}' is not a directory")
    
    all_files = []
    all_folders = []
    
    def _scan_recursive(current_path: Path, current_depth: int = 0):
        if max_depth is not None and current_depth > max_depth:
            return
            
        try:
            files, folders = scan_directory_simple(current_path)
            all_files.extend(files)
            all_folders.extend(folders)
            
            # Recurse into subdirectories
            for folder in folders:
                _scan_recursive(folder, current_depth + 1)
                
        except (PermissionError, OSError) as e:
            logger.warning(f"Skipping '{current_path}': {e}")
    
    _scan_recursive(path)
    
    return sorted(all_files), sorted(all_folders)


def print_scan_results(files: List[Path], folders: List[Path], directory: PathLike) -> None:
    """
    Print formatted results of directory scan.
    
    Args:
        files: List of files found
        folders: List of folders found
        directory: Directory that was scanned
    """
    if not (files or folders):
        print(f"Directory '{directory}' is empty")
        return
    
    print(f"\nScan results for '{directory}':")
    print("-" * 40)
    
    if files:
        print(f"Files found: {len(files)}")
        if len(files) <= 10:  # Show first 10 files
            for file in files:
                print(f"  📄 {file.name}")
        else:
            for file in files[:5]:
                print(f"  📄 {file.name}")
            print(f"  ... and {len(files) - 5} more files")
    else:
        print("No files found")
    
    if folders:
        print(f"\nFolders found: {len(folders)}")
        if len(folders) <= 10:  # Show first 10 folders
            for folder in folders:
                print(f"  📁 {folder.name}")
        else:
            for folder in folders[:5]:
                print(f"  📁 {folder.name}")
            print(f"  ... and {len(folders) - 5} more folders")
    else:
        print("No folders found")
    
    print(f"\nTotal: {len(files)} files, {len(folders)} folders")


def validate_directory(directory: PathLike) -> Path:
    """
    Validate and return Path object for directory.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
    """
    path = Path(directory)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"'{directory}' is not a directory")
    
    return path


def get_directory_size(directory: PathLike) -> int:
    """
    Get total size of directory in bytes.
    
    Args:
        directory: Directory to measure
        
    Returns:
        Total size in bytes
    """
    path = validate_directory(directory)
    total_size = 0
    
    try:
        files, folders = scan_directory_recursive(path)
        
        for file in files:
            try:
                total_size += file.stat().st_size
            except (OSError, PermissionError):
                continue
                
    except (PermissionError, OSError) as e:
        logger.warning(f"Could not calculate size for '{directory}': {e}")
    
    return total_size


def filter_by_extension(files: List[Path], *extensions: str) -> List[Path]:
    """
    Filter files by extension(s).
    
    Args:
        files: List of file paths
        *extensions: Extensions to filter by (e.g., '.txt', '.py')
        
    Returns:
        Filtered list of files
    """
    if not extensions:
        return files
    
    # Normalize extensions (ensure they start with .)
    normalized_exts = []
    for ext in extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_exts.append(ext.lower())
    
    return [f for f in files if f.suffix.lower() in normalized_exts]


# Convenience functions for common use cases
def find_python_files(directory: PathLike, recursive: bool = False) -> List[Path]:
    """Find all Python files in directory."""
    if recursive:
        files, _ = scan_directory_recursive(directory)
    else:
        files, _ = scan_directory_simple(directory)
    
    return filter_by_extension(files, '.py')


def find_text_files(directory: PathLike, recursive: bool = False) -> List[Path]:
    """Find all text files in directory."""
    if recursive:
        files, _ = scan_directory_recursive(directory)
    else:
        files, _ = scan_directory_simple(directory)
    
    return filter_by_extension(files, '.txt', '.md', '.rst')


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan directory for files and folders")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--progress", "-p", action="store_true", help="Show progress bar")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursive scan")
    parser.add_argument("--python", action="store_true", help="Show only Python files")
    
    args = parser.parse_args()
    
    try:
        if args.recursive:
            files, folders = scan_directory_recursive(args.directory, show_progress=args.progress)
        else:
            files, folders = scan_directory(args.directory, show_progress=args.progress)
        
        if args.python:
            files = filter_by_extension(files, '.py')
            folders = []  # Don't show folders when filtering
        
        print_scan_results(files, folders, args.directory)
        
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"Error: {e}")
        exit(1)