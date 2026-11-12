import time
import asyncio
import json
import sys
from pathlib import Path

import openai
import fastmcp
from fastmcp.client.transports import StdioTransport

from .api import ChatApi
from .api.openai_api import getAPIkey
from .config import (
    DEFAULT_GENERATION_TIMEOUT, DEFAULT_MAX_ITERATION, DEFAULT_PROVIDER,
    SYSTEM_PROMPT, LLMProvider
)

from .models import SolutionOutput
from .utils import getRandoMBPP


def check_apikeys_available() -> list[LLMProvider]:
    provider_lst = []
    for provider in LLMProvider:
        if provider == DEFAULT_PROVIDER:
            continue
        try:
            getAPIkey(provider)
            provider_lst.append(provider)
        except ValueError:
            print(f"No key found for: {provider.value.NAME}")
    try:
        getAPIkey(DEFAULT_PROVIDER)
        provider_lst.append(DEFAULT_PROVIDER)
    except ValueError:
        print(f"No key found for: {DEFAULT_PROVIDER.value.NAME}")
    return provider_lst


async def generate_mbpp(provider_lst: list[LLMProvider]):
    question = getRandoMBPP()
    chat = ChatApi(question=question, llm_provider=provider_lst[-1])

    print(
        f"Id: {question.task_id}\n"
        f"Question: {question.task_definition}"
    )

    start_time = time.monotonic()
    generation_deadline = start_time + DEFAULT_GENERATION_TIMEOUT
    code = ""
    error = None
    iterations = 0

    async with client:
        for iteration in range(DEFAULT_MAX_ITERATION):
            iterations = iteration + 1
            remaining_time = generation_deadline - time.monotonic()
            if remaining_time < 0:
                error = "Generation timed out"
                break

            try:
                code = chat.generateSandboxCode(timeout=remaining_time)
                result = await client.call_tool(
                    "run_tests",
                    {
                        "code": code,
                        "test_list": question.test_list,
                        "test_imports": question.test_imports,
                    },
                )
                test_result = json.loads(result.data)
                if test_result["success"]:
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

    output = SolutionOutput(
        task_id=str(question.task_id),
        benchmark="mbpp",
        success=test_result["success"] if test_result else False,
        solution=code,
        iterations=iterations,
        total_requests=iterations,
        total_input_tokens=chat.total_input_tokens,
        total_output_tokens=chat.total_output_tokens,
        total_time_seconds=time.monotonic() - start_time,
        steps=[],
        system_prompt=SYSTEM_PROMPT,
        error=error,
    )
    print(output.model_dump_json(indent=2))


def main() -> None:
    provider_lst = check_apikeys_available()
    if not provider_lst:
        raise ValueError("No API keys are set as environment variables")
    asyncio.run(generate_mbpp(provider_lst))


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "src.mcp.mcp_tools_mbpp"],
        cwd=str(PROJECT_ROOT),
    )
    client = fastmcp.Client(transport)

    main()
