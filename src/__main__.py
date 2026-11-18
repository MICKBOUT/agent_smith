import time
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import fire
import openai
import fastmcp
from fastmcp.client.transports import StdioTransport

from .api import ChatApi, getAPIkey
from .config import (
    DEFAULT_GENERATION_TIMEOUT, DEFAULT_MAX_ITERATION,
    SYSTEM_PROMPT, Provider, UserProvider
)

from .models import SolutionOutput, StepMetrics, NoneMessageError, NoCodeBlockFound, MBPPTaskInput
from .utils import check_apikeys_available, load_mbpp_question


class CLI:
    def __init__(self) -> None:
        self.provider_lst = check_apikeys_available()
        if not self.provider_lst:
            raise ValueError("No API keys are set as environment variables")

    def _addUserModel(self, model_name: str, provider_url: str) -> None:
        if model_name or provider_url:
            if not (model_name and provider_url):
                print("model_name and provider_url need to be set if you want to use a user set provider")
            else:
                provider = check_apikey(provider_url, model_name)
                if provider:
                    self.provider_lst.append(provider)

    def agent_mbpp(
        self,
        task_file: str = "datasets/mbpp/task.json",
        output: str = "output.json",
        model_name: str = "",
        provider_url: str = "",
    ) -> None:
        """Run MBPP"""
        question = load_mbpp_question(task_file)

        self._addUserModel(model_name, provider_url)
        solution = asyncio.run(generate_mbpp(self.provider_lst, question))
        try:
            solution_data = solution.model_dump()
            with open(output, "w", encoding="utf-8") as output_file:
                json.dump(solution_data, output_file, indent=2)
        except (OSError, TypeError, ValueError) as e:
            print(f"Error writing solution to '{output}': {e}")

    def agent_swebench(
        self,
        task_file: str = "datasets/swebench/task.json",
        output: str = "",
        model_name: str = "",
        provider_url: str = "",
    ) -> None:
        self._addUserModel(model_name, provider_url)
        ...


def check_apikey(provider_url: str, model_name: str) -> Optional[Provider]:
    provider = UserProvider(provider_url, model_name)
    try:
        getAPIkey(provider)
        return provider
    except ValueError:
        print(f"No key found for: {provider.NAME}")
    return None


async def generate_mbpp(provider_lst: list[Provider], question: MBPPTaskInput) -> SolutionOutput:
    chat = ChatApi(question=question, llm_provider=provider_lst[-1])

    print(
        f"Id: {question.task_id}\n"
        f"Question: {question.task_definition}"
    )

    start_time = time.monotonic()
    generation_deadline = start_time + DEFAULT_GENERATION_TIMEOUT
    error = None
    steps = []

    async with client:
        for iteration in range(1, DEFAULT_MAX_ITERATION + 1):
            remaining_time = generation_deadline - time.monotonic()
            if remaining_time < 0:
                error = "Generation timed out"
                break

            try:
                llm_generation_output = chat.generateSandboxCode(timeout=remaining_time)
                sandbox_result = await client.call_tool(
                    "run_tests",
                    {
                        "code": llm_generation_output.code,
                        "test_list": question.test_list,
                        "test_imports": question.test_imports,
                    },
                )
                test_result = json.loads(sandbox_result.data)
                if test_result["success"]:
                    steps.append(StepMetrics(
                        step=iteration,
                        input_tokens=llm_generation_output.input_tokens,
                        output_tokens=llm_generation_output.output_tokens,
                        request_time_ms=remaining_time + time.monotonic() - generation_deadline,
                        api_url=chat.llm_provider.URL,
                        model_name=chat.llm_provider.MODEL_NAME,
                        llm_output=llm_generation_output.response,
                        sandbox_input=llm_generation_output.sandbox_input,
                        sandbox_output=test_result["output"],
                        retries=0
                    ))
                    print("\033[32mDone\033[0m")
                    break

                error = test_result["output"]
                chat.addLog(error)
            except (openai.RateLimitError, openai.BadRequestError):
                provider_lst.pop()
                if len(provider_lst) == 0:
                    error = "No provider available"
                    break
                chat.setProvider(provider_lst[-1])
            except (NoneMessageError, NoCodeBlockFound):
                continue

    return SolutionOutput(
        task_id=str(question.task_id),
        benchmark="mbpp",
        success=test_result["success"] if test_result else False,
        solution=llm_generation_output.code,
        iterations=iteration,
        total_requests=iteration,
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        total_time_seconds=time.monotonic() - start_time,
        steps=steps,
        system_prompt=SYSTEM_PROMPT,
        error=error,
    )


def main() -> None:
    fire.Fire(CLI)


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    transport = StdioTransport(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_tools_mbpp.py")],
        cwd=str(PROJECT_ROOT),
    )
    client = fastmcp.Client(transport)

    main()
