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

class PathScanner:
    """
    Class-based interface for path scanning with state management and configuration.
    
    Provides an object-oriented interface to the module-level functions with
    additional features like caching, state tracking, and method chaining.
    """
    
    def __init__(
        self,
        show_progress: bool = False,
        resolve_paths: bool = False,
        include_hidden: bool = True,
        enable_cache: bool = True
    ):
        """
        Initialize PathScanner with default settings.
        
        Args:
            show_progress: Default progress bar setting
            resolve_paths: Default path resolution setting
            include_hidden: Default hidden file inclusion setting
            enable_cache: Enable result caching
        """
        self.show_progress = show_progress
        self.resolve_paths = resolve_paths
        self.include_hidden = include_hidden
        self.enable_cache = enable_cache
        
        # State tracking
        self._cache = {} if enable_cache else None
        self._stats = {"scans": 0, "files_found": 0, "folders_found": 0, "cache_hits": 0}
        self._scan_history = []
        self._filters = []
    
    def scan_directory(
        self,
        directory: PathLike,
        show_progress: Optional[bool] = None,
        resolve_paths: Optional[bool] = None,
        include_hidden: Optional[bool] = None,
        use_cache: bool = True
    ) -> Tuple[List[Path], List[Path]]:
        """
        Scan directory using instance defaults, with optional overrides.
        
        Args:
            directory: Directory to scan
            show_progress: Override default progress setting
            resolve_paths: Override default path resolution
            include_hidden: Override default hidden file inclusion
            use_cache: Use cached results if available
            
        Returns:
            Tuple of (files, folders) lists
        """
        # Use instance defaults unless overridden
        _show_progress = show_progress if show_progress is not None else self.show_progress
        _resolve_paths = resolve_paths if resolve_paths is not None else self.resolve_paths
        _include_hidden = include_hidden if include_hidden is not None else self.include_hidden
        
        # Check cache first
        if self.enable_cache and use_cache and self._cache is not None:
            cache_key = (str(Path(directory).resolve()), _resolve_paths, _include_hidden)
            if cache_key in self._cache:
                self._stats["cache_hits"] += 1
                return self._cache[cache_key]
        
        # Perform scan using module function
        files, folders = scan_directory(
            directory,
            show_progress=_show_progress,
            resolve_paths=_resolve_paths,
            include_hidden=_include_hidden
        )
        
        # Apply any filters
        for filter_func in self._filters:
            files = filter_func(files)
        
        # Update stats
        self._stats["scans"] += 1
        self._stats["files_found"] += len(files)
        self._stats["folders_found"] += len(folders)
        self._scan_history.append(directory)
        
        # Cache results
        if self.enable_cache and self._cache is not None:
            cache_key = (str(Path(directory).resolve()), _resolve_paths, _include_hidden)
            self._cache[cache_key] = (files, folders)
        
        return files, folders
    
    def scan_recursive(
        self,
        directory: PathLike,
        max_depth: Optional[int] = None,
        show_progress: Optional[bool] = None
    ) -> Tuple[List[Path], List[Path]]:
        """Recursive scan using instance settings."""
        _show_progress = show_progress if show_progress is not None else self.show_progress
        
        files, folders = scan_directory_recursive(directory, max_depth, _show_progress)
        
        # Apply filters
        for filter_func in self._filters:
            files = filter_func(files)
        
        # Update stats
        self._stats["scans"] += 1
        self._stats["files_found"] += len(files)
        self._stats["folders_found"] += len(folders)
        self._scan_history.append(directory)
        
        return files, folders
    
    def add_extension_filter(self, *extensions: str) -> 'PathScanner':
        """
        Add extension filter to scanner.
        
        Args:
            *extensions: File extensions to include (e.g., '.py', '.txt')
            
        Returns:
            Self for method chaining
        """
        def ext_filter(files: List[Path]) -> List[Path]:
            return filter_by_extension(files, *extensions)
        
        self._filters.append(ext_filter)
        return self
    
    def add_size_filter(self, min_size: Optional[int] = None, max_size: Optional[int] = None) -> 'PathScanner':
        """
        Add file size filter.
        
        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            
        Returns:
            Self for method chaining
        """
        def size_filter(files: List[Path]) -> List[Path]:
            result = []
            for file in files:
                try:
                    size = file.stat().st_size
                    if min_size and size < min_size:
                        continue
                    if max_size and size > max_size:
                        continue
                    result.append(file)
                except (OSError, PermissionError):
                    continue
            return result
        
        self._filters.append(size_filter)
        return self
    
    def add_custom_filter(self, filter_func) -> 'PathScanner':
        """
        Add custom filter function.
        
        Args:
            filter_func: Function that takes List[Path] and returns List[Path]
            
        Returns:
            Self for method chaining
        """
        self._filters.append(filter_func)
        return self
    
    def clear_filters(self) -> 'PathScanner':
        """Clear all filters."""
        self._filters.clear()
        return self
    
    def clear_cache(self) -> 'PathScanner':
        """Clear the results cache."""
        if self._cache:
            self._cache.clear()
        return self
    
    def get_stats(self) -> dict:
        """Get scanning statistics."""
        return self._stats.copy()
    
    def get_scan_history(self) -> List[PathLike]:
        """Get list of directories that have been scanned."""
        return self._scan_history.copy()
    
    def print_stats(self) -> None:
        """Print formatted statistics."""
        stats = self.get_stats()
        print("\nPathScanner Statistics:")
        print("-" * 25)
        print(f"Directories scanned: {stats['scans']}")
        print(f"Total files found: {stats['files_found']}")
        print(f"Total folders found: {stats['folders_found']}")
        if self.enable_cache:
            print(f"Cache hits: {stats['cache_hits']}")
        print(f"Filters active: {len(self._filters)}")
    
    # Convenience methods that delegate to module functions
    def find_python_files(self, directory: PathLike, recursive: bool = False) -> List[Path]:
        """Find Python files using scanner settings."""
        if recursive:
            files, _ = self.scan_recursive(directory)
        else:
            files, _ = self.scan_directory(directory)
        return filter_by_extension(files, '.py')
    
    def find_text_files(self, directory: PathLike, recursive: bool = False) -> List[Path]:
        """Find text files using scanner settings."""
        if recursive:
            files, _ = self.scan_recursive(directory)
        else:
            files, _ = self.scan_directory(directory)
        return filter_by_extension(files, '.txt', '.md', '.rst')
    
    def print_results(self, files: List[Path], folders: List[Path], directory: PathLike) -> None:
        """Print scan results using module function."""
        print_scan_results(files, folders, directory)

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