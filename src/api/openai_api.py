import os
import requests
import json

from openai import OpenAI
import dotenv

from ..config import SYSTEM_PROMPT_v0, TASK, OPENROUTER_URL, OPENROUTER_URL_KEY
from ..utils.random_question import getRandoMBPP


def getclient(API_KEY: str) -> OpenAI:
    return OpenAI(
        base_url=OPENROUTER_URL,
        api_key=API_KEY,
    )


def checkingLimits(API_KEY: str = "") -> None:
    response = requests.get(
        url=OPENROUTER_URL_KEY,
        headers={
            "Authorization": f"Bearer {API_KEY}"
        }
    )
    print(json.dumps(response.json(), indent=2))


def printModelslst(client: OpenAI) -> None:
    models = [m.id for m in client.models.list() if m.id.endswith(":free")]
    for model in models:
        print(model)


# def genText(client: OpenAI) -> None:
#     r = client.chat.completions.create(
#         model="poolside/laguna-s-2.1",  # any model id from openrouter.ai/models
#         messages=[{"role": "user", "content": "Write a function to find the minimum cost path to reach (m, n) from (0, 0) for the given cost matrix cost[][] and a position (m, n) in cost[][]."}],
#         stop=["<end_code>"],
#     )

#     print(r.choices[0].message.content)
#     if r.usage is None:
#         raise ValueError("r.usage is None")
#     print(
#         f"prompt_tokens: {r.usage.prompt_tokens}\n"
#         f"completion_tokens: {r.usage.completion_tokens}"
#     )


def genCode(client: OpenAI, question: str = "") -> None:
    if not question:
        random_question = getRandoMBPP()
        task_id, task_text = random_question["task_id"], random_question["text"]
    print(f"Task id: {task_id}, Question: {task_text}")

    r = client.chat.completions.create(
        model="poolside/laguna-s-2.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_v0},
            {"role": "user", "content": TASK},
        ],
        stop=["<end_code>"],
        max_tokens=1000,
        # max_tokens=1500,
        # temperature=0.2,
    )

    message = r.choices[0].message.content

    try:
        message = message[message.find("```python") + 10:]
        message = message[:message.find("```")]
    except Exception as e:
        print(message)
        raise e
    return message


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if OPENROUTER_API_KEY is None:
        raise ValueError("OPENROUTER_API_KEY must be set as env variable")

    client = getclient(OPENROUTER_API_KEY)
    # checkingLimits(OPENROUTER_API_KEY)
    # genText(client)
    # printModelslst(client)
    code = genCode(client)
    print(code)
