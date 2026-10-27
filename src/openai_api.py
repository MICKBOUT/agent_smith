import os
import requests
import json

from openai import OpenAI
import dotenv


def checkingLimits(API_KEY: str = "") -> None:
    response = requests.get(
        url="https://openrouter.ai/api/v1/key",
        headers={
            "Authorization": f"Bearer {API_KEY}"
        }
    )
    print(json.dumps(response.json(), indent=2))


def getModelslst(API_KEY: str = "", print_lst: bool = True) -> list[str]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    models = [m.id for m in client.models.list() if m.id.endswith(":free")]
    if print_lst:
        for model in models:
            print(model)
    return models


def genText(API_KEY: str = "") -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    r = client.chat.completions.create(
        model="recursive/flint-v1.0:free",  # any model id from openrouter.ai/models
        messages=[{"role": "user", "content": "Hello"}],
        stop=["<end_code>"],
    )

    print(r.choices[0].message.content)
    if r.usage is None:
        raise ValueError("r.usage is None")
    print(
        f"prompt_tokens: {r.usage.prompt_tokens}\n"
        f"completion_tokens: {r.usage.completion_tokens}"
    )


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if OPENROUTER_API_KEY is None:
        raise ValueError("OPENROUTER_API_KEY must be set as env variable")

    # genText(OPENROUTER_API_KEY)
    # checkingLimits(OPENROUTER_API_KEY)
    getModelslst(OPENROUTER_API_KEY)
