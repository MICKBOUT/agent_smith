"""MCP tools used by the MBPP agent."""

import json

from fastmcp import FastMCP

from src.models import SandboxConfig, SandboxError
from src.sandbox.sandbox import Sandbox
from src.utils import sanitizeImport


mcp = FastMCP("MBPP tools")
sandbox: Sandbox | None = None


@mcp.tool
def run_tests(code: str, test_list: list[str], test_imports: list[str] | None = None) -> str:
    """Run a candidate solution against MBPP assertion tests."""
    test_imports = test_imports or []
    program = "\n".join([*test_imports, code, *test_list])

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


if __name__ == "__main__":
    mcp.run(transport="stdio")
