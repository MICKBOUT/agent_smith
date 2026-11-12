"""MCP tools used by the MBPP agent."""

import json
import ast
import subprocess

from fastmcp import FastMCP
from ..sandbox.docker_init import Container

mcp = FastMCP("MBPP tools")
container: Container | None = None


@mcp.tool
def run_tests(code: str, test_list: list[str], test_imports: list[str] = []) -> str:
    """Run a candidate solution against MBPP assertion tests."""
    program = "\n".join([*test_imports, code, *test_list])

    # Allow only modules requested by the task, not imports added by the model.
    allowed_imports = set()
    try:
        for node in ast.walk(ast.parse("\n".join(test_imports))):
            if isinstance(node, ast.Import):
                allowed_imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                allowed_imports.add(node.module)
    except SyntaxError as exc:
        return json.dumps({"success": False, "output": f"SyntaxError: {exc}"})

    global container
    if container is None:
        container = Container()
    try:
        result = container.run([" ".join(sorted(allowed_imports)), "--single"], 10, program)
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "output": "Tests timed out."})
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return json.dumps({"success": False, "output": output.strip()})

    output = (result.stdout + result.stderr).strip()
    return json.dumps({"success": result.returncode == 0, "output": output})


if __name__ == "__main__":
    mcp.run(transport="stdio")
