import time
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import openai
import fastmcp
from fastmcp.client.transports import StdioTransport

from agent_common.api import ChatApiMbpp, ChatApiSwe
from agent_common.config import (
    GENERATION_TIMEOUT_MBPP, GENERATION_TIMEOUT_SWE,
    DEFAULT_MAX_ITERATION, SYSTEM_PROMPT_MBPP, SYSTEM_PROMPT_SWE,
    Provider, UserProvider
)

from agent_common.models import SolutionOutput, StepMetrics, NoneMessageError, NoCodeBlockFound, MBPPTaskInput, SWEBenchTaskInput
from agent_common.utils import check_apikeys_available, load_mbpp_question, load_swe_question, getAPIkey
from agent_common.sandbox.swebench_repo import load_swebench_repository


class chikibrrr:
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
        task_file: str = "../cache/mbpp_task.json",
        output: str = "../output.json",
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
        task_file: str = "../cache/swebench_task.json",
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


async def _mcp_result_text(result: Any) -> str:
    """Convert FastMCP's typed result into text for the model conversation."""
    data = getattr(result, "data", None)
    if data is not None:
        return data if isinstance(data, str) else json.dumps(data, default=str)

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, default=str)

    blocks = getattr(result, "content", None) or []
    return "\n".join(
        block.text if isinstance(getattr(block, "text", None), str) else str(block)
        for block in blocks
    )


async def generate_swe(
    provider_lst: list[Provider],
    question: SWEBenchTaskInput,
    testbed_path: Path,
) -> SolutionOutput:
    transport_swe = StdioTransport(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_tools_swebench.py")],
        cwd=str(PROJECT_ROOT),
        env={
            **os.environ,
            "TESTBED_PATH": str(testbed_path),
            "SWEBENCH_IMAGE": question.docker_image,
        },
    )
    client_swe = fastmcp.Client(transport_swe)
    start_time = time.monotonic()
    steps: list[StepMetrics] = []
    solution_patch = ""
    error = None
    final_patch_received = False
    request_count = 0

    async with client_swe:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in await client_swe.list_tools()
        ]
        chat = ChatApiSwe(question, provider_lst[-1], tools)
        deadline = start_time + GENERATION_TIMEOUT_SWE

        for iteration in range(1, DEFAULT_MAX_ITERATION + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                error = "Generation timed out"
                break

            request_started = time.monotonic()
            try:
                request_count += 1
                generated = chat.generateSandboxCode(timeout=remaining)
                tool_observations: list[str] = []

                if generated.tool_calls:
                    assistant_message: dict[str, Any] = {
                        "role": "assistant",
                        "content": generated.response or None,
                        "tool_calls": generated.tool_calls,
                    }
                    chat.messages.append(assistant_message)

                    for call in generated.tool_calls:
                        function = call["function"]
                        arguments = function.get("arguments", "{}")
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)
                        result = await client_swe.call_tool(function["name"], arguments)
                        result_text = await _mcp_result_text(result)
                        if getattr(result, "is_error", False):
                            result_text = f"Tool error: {result_text}"
                        chat.messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": result_text,
                        })
                        tool_observations.append(f"{function['name']}: {result_text}")

                        if function["name"] == "get_patch":
                            if (
                                not getattr(result, "is_error", False)
                                and result_text
                                and not result_text.startswith("git diff failed")
                            ):
                                solution_patch = result_text
                                final_patch_received = True
                            else:
                                error = result_text or "get_patch returned an empty patch"
                            break
                else:
                    chat.messages.append({"role": "assistant", "content": generated.response})
                    chat.messages.append({
                        "role": "user",
                        "content": "Please use the available MCP function tools to inspect or change the repository. When done, call get_patch.",
                    })
                    tool_observations.append("Model response did not contain a tool call.")

                action_record = (
                    json.dumps(generated.tool_calls, ensure_ascii=False)
                    if generated.tool_calls
                    else generated.response or "No tool call returned by model"
                )
                steps.append(StepMetrics(
                    step=iteration,
                    input_tokens=generated.input_tokens,
                    output_tokens=generated.output_tokens,
                    request_time_ms=(time.monotonic() - request_started) * 1000,
                    api_url=chat.llm_provider.URL,
                    model_name=chat.llm_provider.MODEL_NAME,
                    llm_output=generated.response or action_record,
                    sandbox_input=action_record,
                    sandbox_output="\n".join(tool_observations),
                    retries=0,
                ))

                if final_patch_received or error:
                    break

            except (
                openai.RateLimitError,
                openai.BadRequestError,
                openai.InternalServerError,
                openai.NotFoundError,
                openai.APITimeoutError,
            ) as exc:
                error = f"{type(exc).__name__}: {exc}"
                if len(provider_lst) > 1:
                    provider_lst.pop()
                    chat.setProvider(provider_lst[-1])
                    error = None
                    continue
                break
            except Exception as exc:
                error = f"SWE-bench step {iteration} failed: {type(exc).__name__}: {exc}"
                break
        else:
            error = "Maximum SWE-bench iterations reached without retrieving a patch"

        # Recover a valid diff even if the model reaches its iteration limit
        # after editing but forgets the final get_patch call.
        if not final_patch_received:
            try:
                patch_result = await client_swe.call_tool("get_patch", {})
                patch_text = await _mcp_result_text(patch_result)
                if (
                    not getattr(patch_result, "is_error", False)
                    and patch_text
                    and not patch_text.startswith("git diff failed")
                ):
                    solution_patch = patch_text
                    final_patch_received = True
                    error = None
                elif not error:
                    error = patch_text or "No repository changes were produced"
            except Exception as exc:
                if not error:
                    error = f"Could not retrieve final patch: {type(exc).__name__}: {exc}"

    return SolutionOutput(
        task_id=question.instance_id,
        benchmark="swebench",
        success=final_patch_received and bool(solution_patch),
        solution=solution_patch,
        iterations=len(steps),
        total_requests=request_count,
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        total_time_seconds=time.monotonic() - start_time,
        steps=steps,
        system_prompt=SYSTEM_PROMPT_SWE,
        error=error,
    )


async def generate_mbpp(provider_lst: list[Provider], question: MBPPTaskInput) -> SolutionOutput:
    chat = ChatApiMbpp(question=question, llm_provider=provider_lst[-1])
    transport_mbpp = StdioTransport(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_tools_mbpp.py")],
        cwd=str(PROJECT_ROOT),
    )
    client_mbpp = fastmcp.Client(transport_mbpp)

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run(t: str) -> None:
    brrrbrrrr = chikibrrr()

    if t == "mbpp":
        brrrbrrrr.agent_mbpp()
    else:
        brrrbrrrr.agent_swebench()
