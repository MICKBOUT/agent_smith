"""MCP tools used by the MBPP agent."""

import subprocess
import json
import glob

from pathlib import Path
from itertools import islice
from fastmcp import FastMCP

from src.models import SandboxConfig, SandboxError
from src.sandbox.sandbox import Sandbox
from src.utils import sanitizeImport, createProgram

mcp = FastMCP("MBPP tools")
sandbox: Sandbox | None = None


@mcp.tool
def run_tests(code: str, test_list: list[str], test_imports: list[str] | None = None) -> str:
    """Run a candidate solution against MBPP assertion tests."""
    program = createProgram(code, test_list, test_imports)

    global sandbox
    if sandbox is None or sandbox.authorized_imports != sanitizeImport(test_imports):
        sandbox = Sandbox(SandboxConfig(
            authorized_imports=sanitizeImport(test_imports)
        ))
    try:
        result = None
        result = sandbox.execute(program)
        if result.returncode != 0:
            raise SandboxError(result.stderr)

    except SandboxError:
        if result:
            return json.dumps({"success": False, "output": result.stderr})
        return json.dumps({"success": False, "output": "SandBoxtime out"})

    return json.dumps({"success": result.returncode == 0, "output": result.stderr})

# File System Tools


@mcp.tool
def read_file(filepath: str, start_line: int, end_line: int) -> str:
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
        str: content of the file | Error
    """
    if start_line <= 0 or end_line <= 0:
        raise "ValueError: start_line and end_line must be non-nul positive integers."

    if start_line > end_line:
        return "ValueError: end_line must be greater or equal to start_line!"

    file_path = Path(filepath)

    if not file_path.exists():
        return f"FileNotFoundError: {filepath} not found!"

    if not file_path.is_file():
        return "FileNotFoundError: file_path must be a correct file."

    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = list(islice(f, start_line-1, end_line))
            result = ""
            for i, line in enumerate(lines, start=start_line):
                result += f"{i:>6}\t{line}"

            return result
    except OSError as e:
        return "OSError: ", e


@mcp.tool
def edit_file(filepath: str, old_str: str, new_str: str) -> str:
    """
    This function replace a string by another string in a file.
    it returns an empty string or an error message.

    Args:
        filepath: the path of the file to be edited.
        old_str: the target pattern to be replaced.
        new_str: the new string.

    Returns:
        str: empty string or an error message.
    """
    file = Path(filepath)

    # todo validation
    content = file.read_text(encoding="utf-8")

    count = content.count(old_str)

    if count == 0:
        return f"ValueError: pattern not found in '{filepath}'."
    if count > 1:
        return (
            f"ValueError Ambiguous : '{old_str}' appear"
            " {count} times. Please add more context."
        )

    new_content = content.replace(old_str, new_str, 1)
    file.write_text(new_content, encoding="utf-8")

    return ""


@mcp.tool
def list_files(directory: str, pattern: str) -> str:
    """
    This functions take a target directory and return all the files in,
    according to the glob pattern.

    Args:
        directory: the path of the directory.
        pattern: glob pattern.

    Returns:
        str: all the files | Error message
    """
    directory = Path(directory)

    # todo validation
    try:
        files = glob.glob(pattern)
        resolved = [str(Path(file).resolve()) for file in files]
    except Exception as e:
        return e
    else:
        return "".join(file for file in resolved)

# Code Search Tools


@mcp.tool
def search_code(pattern: str, file_pattern: str):
    ...


@mcp.tool
def search_function_or_class_definition_in_code(name: str):
    ...


@mcp.tool
def find_references(name: str, filepath: str, line):
    ...


@mcp.tool
def run_command(command: str, workdir: str) -> str:
    """
    Execute a shell command in the specified working directory.
    Returns the command stdout, stderr, and exit code.

    Args:
        command: unix command.
        workdir: working directory.
    
    Returns:
        str: stdout + stderr + exit code.
    """
    workdir = Path(workdir)
    # todo validation
    target = f"cd {workdir};"
    result = subprocess.run(target + command, shell=True)
    return (
        result.stdout if result.stdout else "" +
        result.stderr if result.stderr else "" +
        str(result.returncode)
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

    # print(read_file("Makefile", 1, 5))
    # print(list_files(".", "*.py"))
    # run_command("ls -a", "/tmp")
