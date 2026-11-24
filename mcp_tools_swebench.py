from pathlib import Path
from fastmcp import FastMCP
from itertools import islice

import fnmatch
import re
import subprocess
import glob
import os

mcp = FastMCP("SWE tools")

raw_workdir = os.environ.get("TESTBED_PATH")
if raw_workdir is None:
    raise OSError("TESTBED_PATH var not found!")
WORKDIR = Path(raw_workdir).resolve()
if not WORKDIR.is_dir():
    raise NotADirectoryError(f"TESTBED_PATH is not a directory: {WORKDIR}")


def validate_mcp_paths(path_str: str, file: bool = True) -> Path:
    """
    This function validate a path.

    Args:
        path: The path to be validated.
        file: flag if the target path must be a file.

    Returns:
        Path: the absolute path.

    Raises:
        FileNotFoundError: If the file is not found.
        OSError: If the path can't be resolved.
        ValueError: If the path is not valid.
    """

    path = WORKDIR / Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"File {path_str} not found!")

    try:
        if path != path.resolve():
            path = path.resolve()
    except OSError as err:
        raise err

    if file and not path.is_file():
        raise ValueError(f"Expected a file for {path_str}")
    elif not file and not path.is_dir():
        raise ValueError(f"Expected a directory. for {path_str}")

    return path


@mcp.tool
def read_file(filepath: str, start_line: int, end_line: int) -> str | None:
    """
    This function take a file path and return the lines between
    start_line and end_line included with index start a 1.
    The format is the same than cat -e.
    if end_line too big, max index is used.

    Args:
        filepath: the path of the file to be read.
        start_line: first line.
        end_line: end line.

    Returns:
        str: content of the file
        None: Error

    Raises:
        ValueError: start_line or end_line not valid
        OSError: For sys calls errors
    """
    if start_line <= 0 or end_line <= 0:
        raise ValueError("start_line and end_line must be non-nul positive integers.")

    if start_line > end_line:
        raise ValueError("end_line must be greater or equal to start_line!")

    file_path = validate_mcp_paths(filepath)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = list(islice(f, start_line-1, end_line))
            result = ""
            for i, line in enumerate(lines, start=start_line):
                result += f"{i:>6}\t{line}"

            return result
    except OSError:
        raise


@mcp.tool
def edit_file(filepath: str, old_str: str, new_str: str) -> None:
    """
    This function replace a string by another string in a file.

    Args:
        filepath: the path of the file to be edited.
        old_str: the target pattern to be replaced.
        new_str: the new string.

    Raises:
        ValueError: invalid pattern.
        OSError: sys calls errors
    """
    path_file = validate_mcp_paths(filepath)
    content = path_file.read_text(encoding="utf-8")

    count = content.count(old_str)

    if count == 0:
        raise ValueError("pattern not found in '{filepath}'.")
    if count > 1:
        raise ValueError(
            f"Ambiguous : '{old_str}' appear"
            f" {count} times. Please add more context."
        )

    new_content = content.replace(old_str, new_str, 1)
    path_file.write_text(new_content, encoding="utf-8")


@mcp.tool
def list_files(directory_str: str, pattern: str) -> str | None:
    """
    This functions take a target directory and return all the files in,
    according to the glob pattern.

    Args:
        directory: the path of the directory.
        pattern: glob pattern.

    Returns:
        str: all the files | Error message
    """
    directory = validate_mcp_paths(directory_str, file=False)

    files = glob.glob(pattern, root_dir=directory)
    resolved = [str(Path(file).resolve()) for file in files]

    return "\n".join(file for file in resolved)


@mcp.tool
def search_code(pattern: str, file_pattern: str) -> str:
    """
    Perform a grep-like search in the codebase.

    Args:
        pattern: the pattern expression to find in.
        file_pattern: expected files.

    Returns:
        str: /absolute/path_to_file.py:<line_number> <line_content>
    """
    black_list = {".git", ".venv", "__pycache__", ".mypy_cache"}
    matches = ""
    for path in WORKDIR.rglob('*'):
        if any(part in black_list for part in path.parts):
            continue

        if path.is_file() and fnmatch.fnmatch(path, file_pattern):
            with open(path, "r") as f:
                for i, line in enumerate(f.readlines(), start=1):
                    if re.search(pattern, line):
                        absolute = path.resolve()
                        matches += f"{absolute}:{i} {line}"
    return matches


@mcp.tool
def search_function_or_class_definition_in_code(name: str) -> str:
    """
    Find the definition of a function or a class.

    Args:
        name: the name of the class or function to search.

    Returns:
        str: the matches.
    """
    return search_code(f"class {name}", "*.py") + search_code(f"def {name}", "*.py")


@mcp.tool
def find_references(name: str, filepath: str, line: int) -> str:
    """
    Find all usages of a symbol (function or class).
    The output format must be similar to search_code format.
    """
    return search_code(f"{name}", "*.py")


@mcp.tool
def run_command(command: str, workdir_str: str) -> tuple[str, str, int]:
    """
    Execute a shell command in the specified working directory.
    Returns the command stdout, stderr, and exit code.

    Args:
        command: unix command.
        workdir: working directory.

    Returns:
        str: stdout + stderr + exit code.
    """
    workdir = validate_mcp_paths(workdir_str, file=False)
    target = f"cd {workdir};"
    result = subprocess.run(target + command, shell=True, capture_output=True, text=True)
    return (
        str(result.stdout) if result.stdout else "",
        str(result.stderr) if result.stderr else "",
        result.returncode
    )


@mcp.tool
def get_patch() -> tuple[str, str, int]:
    """
    This funcion run 'git --no-pager diff' and return the result.

    Returns:
        tuple[str, str, int] : Stdout, Stderr and exit code.
    """
    return run_command("git --no-pager diff", WORKDIR)


if __name__ == "__main__":
    mcp.run(transport="stdio")
