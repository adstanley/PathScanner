# PathScanner

A Python module for efficient directory scanning and file path operations.

## Overview

PathScanner provides utilities for scanning directories and handling file operations with features like:
- Single-pass directory scanning
- Recursive directory traversal
- File filtering by extension and size
- Progress bar support (with `tqdm`)
- Caching and state tracking
- Error handling for permissions and invalid paths

The module includes both a class-based interface (`PathScanner`) and standalone functions for flexible usage.

## Installation

```bash
pip install pathscanner
```

Or clone the repository and install locally:

```bash
git clone https://github.com/username/pathscanner.git
cd pathscanner
pip install .
```

### Requirements
- Python 3.6+
- Optional: `tqdm` for progress bar support

## Usage

### Basic Directory Scanning
```python
from pathscanner import scan_directory

# Scan a directory
files, folders = scan_directory("/path/to/directory")
for file in files:
    print(file.name)
```

### Using PathScanner Class
```python
from pathscanner import PathScanner

# Initialize scanner with custom settings
scanner = PathScanner(show_progress=True, include_hidden=False)

# Scan with filters
scanner.add_extension_filter('.py', '.txt')
scanner.add_size_filter(min_size=1000)  # Files > 1KB
files, folders = scanner.scan_directory("/path/to/directory")

# Print results and statistics
scanner.print_results(files, folders, "/path/to/directory")
scanner.print_stats()
```

### Recursive Scanning
```python
from pathscanner import scan_directory_recursive

# Recursive scan with max depth
files, folders = scan_directory_recursive("/path/to/directory", max_depth=2)
```

### Command Line Interface
```bash
python -m pathscanner /path/to/directory --progress --recursive
python -m pathscanner /path/to/directory --python  # Show only Python files
```

## Features

- **Efficient Scanning**: Single-pass directory iteration
- **Flexible Filtering**: Filter by extension, size, or custom functions
- **Progress Feedback**: Optional progress bars with `tqdm`
- **Caching**: Cache scan results for improved performance
- **Error Handling**: Robust handling of permissions and invalid paths
- **State Tracking**: Maintains scan history and statistics
- **Method Chaining**: Fluent interface for filter configuration

## API Reference

### PathScanner Class
- `__init__(show_progress, resolve_paths, include_hidden, enable_cache)`: Initialize scanner
- `scan_directory(directory, ...)`: Scan a single directory
- `scan_recursive(directory, max_depth, ...)`: Recursive directory scan
- `add_extension_filter(*extensions)`: Filter by file extensions
- `add_size_filter(min_size, max_size)`: Filter by file size
- `add_custom_filter(filter_func)`: Add custom filter function
- `clear_filters()`: Remove all filters
- `clear_cache()`: Clear cached results
- `get_stats()`: Get scanning statistics
- `get_scan_history()`: Get list of scanned directories
- `print_stats()`: Print formatted statistics

### Standalone Functions
- `scan_directory(directory, show_progress, resolve_paths, include_hidden)`: Scan directory
- `scan_directory_simple(directory)`: Simple directory scan
- `scan_directory_recursive(directory, max_depth, show_progress)`: Recursive scan
- `print_scan_results(files, folders, directory)`: Print formatted results
- `validate_directory(directory)`: Validate directory path
- `get_directory_size(directory)`: Calculate total directory size
- `filter_by_extension(files, *extensions)`: Filter files by extension
- `find_python_files(directory, recursive)`: Find Python files
- `find_text_files(directory, recursive)`: Find text files

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Built with Python's `pathlib` for robust path handling
- Optional `tqdm` integration for progress visualization