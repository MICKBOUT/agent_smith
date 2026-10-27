import os
import requests
import json

from openai import OpenAI
import dotenv


from ..config import SYSTEM_PROMPT_v0
from ..utils.random_question import getRandoMBPP
from ..utils.enum import LLMProvider


def getAPIkey(provider: LLMProvider) -> str:
    API_KEY = os.getenv(provider.value.API_KEY_NAME)
    if API_KEY is None:
        raise ValueError(f"{provider.value.API_KEY_NAME} must be set as env variable")
    return API_KEY


def getclient(provider: LLMProvider) -> OpenAI:
    return OpenAI(
        base_url=provider.value.URL,
        api_key=getAPIkey(provider),
    )


def printModelslst(client: OpenAI) -> None:
    models = [m.id for m in client.models.list()]
    for model in models:
        print(model)


def genCode(client: OpenAI, llm_provider: LLMProvider, question: str = "") -> None:
    if not question:
        random_question = getRandoMBPP()
        task_id, task_text = random_question["task_id"], random_question["text"]
    else:
        task_id, task_text = None, question
    print(f"Task id: {task_id}, Question: {task_text}")

    r = client.chat.completions.create(
        model=llm_provider.value.DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_v0},
            {"role": "user", "content": task_text},
        ],
        stop=["<end_code>"],
        max_tokens=1000,
        temperature=0.2,
    )

    message = r.choices[0].message.content
    if not isinstance(message, str):
        raise ValueError("The model returned an empty or non-text response")

    start = message.find("```python")
    if start >= 0:
        start += len("```python")
        if message[start:start + 2] == "\r\n":
            start += 2
        elif message[start:start + 1] == "\n":
            start += 1
        message = message[start:]
        end = message.find("```")
        if end >= 0:
            message = message[:end]
    return message.strip()


if __name__ == "__main__":
    dotenv.load_dotenv()

    llm_provider = LLMProvider.GROQ
    client = getclient(llm_provider)

    # checkingLimits(OPENROUTER_API_KEY)
    # genText(client)
    # printModelslst(client)
    code = genCode(client, llm_provider)
    print(code)
