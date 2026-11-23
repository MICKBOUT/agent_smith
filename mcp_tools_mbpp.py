"""MCP tools used by the MBPP agent."""

import json
from fastmcp import FastMCP

from src.models import SandboxConfig, SandboxError
from src.sandbox.sandbox import Sandbox
from src.utils import sanitizeImport, createProgram

mcp = FastMCP("MBPP tools")
sandbox: Sandbox | None = None


# To-do: Warning, the subject ask for 2 agrs but test_imports is added, else the mbpp can run test that arn't imported
@mcp.tool
def run_tests(code: str, test_list: list[str], test_imports: list[str]) -> str:
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
        return json.dumps({
            "success": False,
            "output": result.stderr if result else "SandBoxtime out",
            "final_answer": None
        })

    return json.dumps({
        "success": result.returncode == 0,
        "output": result.stdout or result.stderr,
        "final_answer": getattr(result, "final_answer", None),
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
