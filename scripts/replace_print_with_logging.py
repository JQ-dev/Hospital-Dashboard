"""
Script to replace print() statements with proper logging calls.

This script:
1. Finds all Python files with print statements
2. Adds logging import if not present
3. Replaces print() calls with appropriate logging level
4. Creates a backup of original files
"""

import re
import os
from pathlib import Path
import shutil


def determine_log_level(print_content):
    """
    Determine appropriate logging level based on print content.

    Args:
        print_content: Content of the print statement

    Returns:
        str: Logging level ('debug', 'info', 'warning', 'error')
    """
    content_lower = print_content.lower()

    if any(word in content_lower for word in ['error', 'exception', 'failed', 'failure']):
        return 'error'
    elif any(word in content_lower for word in ['warn', 'warning', 'missing', 'not found']):
        return 'warning'
    elif any(word in content_lower for word in ['debug', '[debug]', 'trace']):
        return 'debug'
    else:
        return 'info'


def extract_print_content(print_statement):
    """
    Extract content from print statement.

    Args:
        print_statement: Full print statement line

    Returns:
        str: Content to be logged
    """
    # Match print(...) and extract content
    match = re.search(r'print\s*\((.*)\)', print_statement, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def convert_print_to_logging(print_content, log_level='info'):
    """
    Convert print content to logging call.

    Args:
        print_content: Content from print statement
        log_level: Logging level to use

    Returns:
        str: Logging statement
    """
    # Handle f-strings and format strings
    return f'logger.{log_level}({print_content})'


def process_file(file_path, dry_run=False):
    """
    Process a single Python file to replace print statements.

    Args:
        file_path: Path to Python file
        dry_run: If True, don't modify files (just report)

    Returns:
        tuple: (num_replacements, modified_lines)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_lines = []
    num_replacements = 0
    has_logging_import = False
    has_logger_declaration = False

    # Check if file already has logging
    for line in lines:
        if re.search(r'import logging', line):
            has_logging_import = True
        if re.search(r'from utils\.logging_config import get_logger', line):
            has_logging_import = True
        if re.search(r'logger = ', line):
            has_logger_declaration = True

    for i, line in enumerate(lines):
        # Skip if line is a comment or string
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            modified_lines.append(line)
            continue

        # Match print statements
        if re.search(r'^\s*print\s*\(', line):
            print_content = extract_print_content(line)
            if print_content:
                log_level = determine_log_level(print_content)
                indent = re.match(r'(\s*)', line).group(1)
                new_line = indent + convert_print_to_logging(print_content, log_level) + '\n'
                modified_lines.append(new_line)
                num_replacements += 1
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    # Add logging import if needed
    if num_replacements > 0 and not has_logging_import:
        # Find where to insert import (after existing imports)
        insert_pos = 0
        for i, line in enumerate(modified_lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_pos = i + 1
            elif insert_pos > 0 and not (line.strip().startswith('import ') or line.strip().startswith('from ')):
                break

        modified_lines.insert(insert_pos, '\n')
        modified_lines.insert(insert_pos + 1, 'from utils.logging_config import get_logger\n')

    # Add logger declaration if needed
    if num_replacements > 0 and not has_logger_declaration:
        # Insert after imports
        insert_pos = 0
        for i, line in enumerate(modified_lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_pos = i + 1

        modified_lines.insert(insert_pos, '\n')
        modified_lines.insert(insert_pos + 1, 'logger = get_logger(__name__)\n')

    if not dry_run and num_replacements > 0:
        # Create backup
        backup_path = str(file_path) + '.bak'
        shutil.copy2(file_path, backup_path)

        # Write modified file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)

    return num_replacements, modified_lines


def main():
    """Main function to process all Python files."""
    project_root = Path(__file__).parent.parent
    target_dirs = [
        project_root / 'callbacks',
        project_root / 'pages',
        project_root / 'components',
        project_root / 'data_loaders',
    ]

    # Also process main files
    main_files = [
        project_root / 'dashboard.py',
        project_root / 'app_with_auth.py',
        project_root / 'app.py',
    ]

    print("=== Replacing print() statements with logging ===\n")

    total_replacements = 0
    files_modified = 0

    # Process directories
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue

        print(f"\nProcessing directory: {target_dir}")
        for py_file in target_dir.glob('*.py'):
            if py_file.name.startswith('__'):
                continue

            num_replacements, _ = process_file(py_file, dry_run=False)
            if num_replacements > 0:
                print(f"  ✓ {py_file.name}: {num_replacements} print statements replaced")
                total_replacements += num_replacements
                files_modified += 1

    # Process main files
    print(f"\nProcessing main files:")
    for py_file in main_files:
        if py_file.exists():
            num_replacements, _ = process_file(py_file, dry_run=False)
            if num_replacements > 0:
                print(f"  ✓ {py_file.name}: {num_replacements} print statements replaced")
                total_replacements += num_replacements
                files_modified += 1

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files modified: {files_modified}")
    print(f"  Total print statements replaced: {total_replacements}")
    print(f"  Backups created with .bak extension")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
