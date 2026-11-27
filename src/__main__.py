import time
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import fire
import openai
import fastmcp
from fastmcp.client.transports import StdioTransport

from .api import ChatApiMbpp, ChatApiSwe
from .config import (
    GENERATION_TIMEOUT_MBPP, GENERATION_TIMEOUT_SWE,
    DEFAULT_MAX_ITERATION, SYSTEM_PROMPT_MBPP,
    Provider, UserProvider
)

from .models import SolutionOutput, StepMetrics, NoneMessageError, NoCodeBlockFound, MBPPTaskInput, SWEBenchTaskInput
from .utils import check_apikeys_available, load_mbpp_question, load_swe_question, getAPIkey
from .sandbox.swebench_repo import load_swebench_repository


class CLI:
    def __init__(self) -> None:
        self.provider_lst = check_apikeys_available()
        if not self.provider_lst:
            raise ValueError("No API keys are set as environment variables")

    @staticmethod
    def check_user_apikey(provider_url: str, model_name: str) -> Optional[Provider]:
        provider = UserProvider(provider_url, model_name)
        try:
            getAPIkey(provider)
            return provider
        except ValueError:
            pass
        return None

    def _addUserModel(self, model_name: str, provider_url: str) -> None:
        if model_name or provider_url:
            if not (model_name and provider_url):
                print("model_name and provider_url need to be set if you want to use a user set provider")
            else:
                provider = self.check_user_apikey(provider_url, model_name)
                if provider:
                    self.provider_lst.append(provider)

    def agent_mbpp(
        self,
        task_file: str = "cache/mbpp_task.json",
        output: str = "output.json",
        model_name: str = "",
        provider_url: str = "",
    ) -> None:
        """Run MBPP"""
        self._addUserModel(model_name, provider_url)
        question = load_mbpp_question(task_file)

        solution = asyncio.run(generate_mbpp(self.provider_lst, question))

        try:
            solution_data = solution.model_dump()
            with open(output, "w", encoding="utf-8") as output_file:
                json.dump(solution_data, output_file, indent=2)
        except (OSError, TypeError, ValueError) as e:
            print(f"Error writing solution to '{output}': {e}")

    def agent_swebench(
        self,
        task_file: str = "cache/swebench_task.json",
        output: str = "",
        model_name: str = "",
        provider_url: str = "",
    ) -> None:
        self._addUserModel(model_name, provider_url)
        question = load_swe_question(task_file)

        with load_swebench_repository(question.docker_image) as testbed_path:
            solution = asyncio.run(
                generate_swe(self.provider_lst, question, testbed_path)
            )

        try:
            solution_data = solution.model_dump()
            with open(output or "output.json", "w", encoding="utf-8") as output_file:
                json.dump(solution_data, output_file, indent=2)
        except (OSError, TypeError, ValueError) as e:
            print(f"Error writing solution to '{output or 'output.json'}': {e}")


# this code is entierly copy from mbpp for now, the entier code need to be addapt for a proper swe banch implementaion
async def generate_swe(
    provider_lst: list[Provider],
    question: SWEBenchTaskInput,
    testbed_path: Path,
) -> SolutionOutput:
    project_root = Path(__file__).resolve().parents[1]
    transport_swe = StdioTransport(
        command=sys.executable,
        args=[str(project_root / "mcp_tools_swebench.py")],
        cwd=str(project_root),
        env={**os.environ, "TESTBED_PATH": str(testbed_path)},
    )
    client_swe = fastmcp.Client(transport_swe)
    async with client_swe:

        tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema,
                },
            }
            for t in await client_swe.list_tools()
        ]

        chat = ChatApiSwe(question, provider_lst[-1], tools)
        start_time = time.monotonic()
        generation_deadline = start_time + GENERATION_TIMEOUT_SWE
        error, steps, tool_result = None, [], {}
        llm_generation_output = None
        solution_code = ""
        final_answer_submitted = False
        for iteration in range(1, DEFAULT_MAX_ITERATION + 1):
            remaining_time = generation_deadline - time.monotonic()
            if remaining_time < 0:
                error = "Generation timed out"
                break

            try:
                llm_generation_output = chat.generateSandboxCode(timeout=remaining_time)
                # Keep the conversation complete: the next request needs to
                # know which code produced the sandbox observation.
                chat.messages.append({
                    "role": "assistant",
                    "content": llm_generation_output.response,
                })
                code = llm_generation_output.code
                print(code)
                sandbox_result = sandbox_swe(code)
                tool_result = json.loads(sandbox_result)

                final_answer = tool_result.get("final_answer")
                if isinstance(final_answer, str) and final_answer:
                    solution_code = final_answer
                    final_answer_submitted = True
                    break

                if tool_result["success"]:
                    chat.addLogSucces(tool_result["output"])
                else:
                    error = tool_result["output"]
                    chat.addLogSandboxError(error)
                steps.append(StepMetrics(
                    step=iteration,
                    input_tokens=llm_generation_output.input_tokens,
                    output_tokens=llm_generation_output.output_tokens,
                    request_time_ms=remaining_time + time.monotonic() - generation_deadline,
                    api_url=chat.llm_provider.URL,
                    model_name=chat.llm_provider.MODEL_NAME,
                    llm_output=llm_generation_output.response,
                    sandbox_input=llm_generation_output.sandbox_input,
                    sandbox_output=tool_result["output"],
                    retries=0
                ))

            except (
                openai.RateLimitError,
                openai.BadRequestError,
                openai.InternalServerError,
                openai.NotFoundError,
                openai.APITimeoutError,
            ) as e:
                if isinstance(e, openai.NotFoundError):
                    print("[LOG]: Model Not found, please  change it in the config folder")
                provider_lst.pop()
                if len(provider_lst) == 0:
                    error = "No provider available"
                    break
                chat.setProvider(provider_lst[-1])
            except (NoneMessageError, NoCodeBlockFound) as e:
                error = str(e)
                chat.addLogDefaultError(error)
                steps.append(StepMetrics(
                    step=iteration,
                    input_tokens=llm_generation_output.input_tokens,
                    output_tokens=llm_generation_output.output_tokens,
                    request_time_ms=remaining_time + time.monotonic() - generation_deadline,
                    api_url=chat.llm_provider.URL,
                    model_name=chat.llm_provider.MODEL_NAME,
                    llm_output=llm_generation_output.response,
                ))

    return SolutionOutput(
        task_id=chat.question.instance_id,
        benchmark="swebench",
        success=final_answer_submitted,
        solution=solution_code,
        iterations=locals().get("iteration", 0),
        total_requests=locals().get("iteration", 0),
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        total_time_seconds=time.monotonic() - start_time,
        steps=steps,
        system_prompt=SYSTEM_PROMPT_MBPP,
        error=error,
    )


from src.models import SandboxConfig, SandboxError
from src.sandbox.sandbox import Sandbox
from src.utils import sanitizeImport

sandbox: Sandbox | None = None


def sandbox_swe(code):
    """Run a candidate solution against MBPP assertion tests."""
    global sandbox
    if sandbox is None:
        sandbox = Sandbox(SandboxConfig())
    try:
        result = None
        result = sandbox.execute(code)
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


async def generate_mbpp(provider_lst: list[Provider], question: MBPPTaskInput) -> SolutionOutput:
    chat = ChatApiMbpp(question=question, llm_provider=provider_lst[-1])

    async with client_mbpp:
        start_time = time.monotonic()
        generation_deadline = start_time + GENERATION_TIMEOUT_MBPP
        error, steps, tool_result = None, [], {}
        llm_generation_output = None
        solution_code = ""
        final_answer_submitted = False
        for iteration in range(1, DEFAULT_MAX_ITERATION + 1):
            remaining_time = generation_deadline - time.monotonic()
            if remaining_time < 0:
                error = "Generation timed out"
                break

            try:
                llm_generation_output = chat.generateSandboxCode(timeout=remaining_time)
                # Keep the conversation complete: the next request needs to
                # know which code produced the sandbox observation.
                chat.messages.append({
                    "role": "assistant",
                    "content": llm_generation_output.response,
                })
                sandbox_result = await client_mbpp.call_tool(
                    "run_tests",
                    {
                        "code": llm_generation_output.code,
                        "test_list": question.test_list,
                        "test_imports": question.test_imports,
                    },
                )
                tool_result = json.loads(sandbox_result.data)
                final_answer = tool_result.get("final_answer")
                if isinstance(final_answer, str) and final_answer:
                    solution_code = final_answer
                    final_answer_submitted = True
                    break

                if tool_result["success"]:
                    chat.addLogSucces(tool_result["output"])
                else:
                    error = tool_result["output"]
                    chat.addLogSandboxError(error)
                steps.append(StepMetrics(
                    step=iteration,
                    input_tokens=llm_generation_output.input_tokens,
                    output_tokens=llm_generation_output.output_tokens,
                    request_time_ms=remaining_time + time.monotonic() - generation_deadline,
                    api_url=chat.llm_provider.URL,
                    model_name=chat.llm_provider.MODEL_NAME,
                    llm_output=llm_generation_output.response,
                    sandbox_input=llm_generation_output.sandbox_input,
                    sandbox_output=tool_result["output"],
                    retries=0
                ))

            except (
                openai.RateLimitError,
                openai.BadRequestError,
                openai.InternalServerError,
                openai.NotFoundError,
                openai.APITimeoutError,
            ) as e:
                if isinstance(e, openai.NotFoundError):
                    print("[LOG]: Model Not found, please  change it in the config folder")
                provider_lst.pop()
                if len(provider_lst) == 0:
                    error = "No provider available"
                    break
                chat.setProvider(provider_lst[-1])
            except (NoneMessageError, NoCodeBlockFound) as e:
                error = str(e)
                chat.addLogDefaultError(error)
                steps.append(StepMetrics(
                    step=iteration,
                    input_tokens=llm_generation_output.input_tokens,
                    output_tokens=llm_generation_output.output_tokens,
                    request_time_ms=remaining_time + time.monotonic() - generation_deadline,
                    api_url=chat.llm_provider.URL,
                    model_name=chat.llm_provider.MODEL_NAME,
                    llm_output=llm_generation_output.response,
                ))

    return SolutionOutput(
        task_id=str(question.task_id),
        benchmark="mbpp",
        success=final_answer_submitted,
        solution=solution_code,
        iterations=locals().get("iteration", 0),
        total_requests=locals().get("iteration", 0),
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        total_time_seconds=time.monotonic() - start_time,
        steps=steps,
        system_prompt=SYSTEM_PROMPT_MBPP,
        error=error,
    )


def main() -> None:
    fire.Fire(CLI)


async def get_tools():
    async with Client("mcp_tools_swebench.py") as mcp:  # or "http://localhost:9000/mcp"
        tools = [{"type": "function", "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema}} for t in await mcp.list_tools()]
    return tools


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    transport_mbpp = StdioTransport(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_tools_mbpp.py")],
        cwd=str(PROJECT_ROOT),
    )
    client_mbpp = fastmcp.Client(transport_mbpp)

    main()
