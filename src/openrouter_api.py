import os

from typing import Any
from openrouter import OpenRouter
import dotenv


def sendRequest(API_KEY: str = "") -> Any:
    with OpenRouter(api_key=API_KEY) as client:
        print("Sending Request")
        response = client.chat.send(
            model="nvidia/nemotron-3.5-super-vl:free",
            messages=[
                {"role": "user", "content": "What is the meaning of life?"}
            ],
        )

        return response.choices[0].message.content


if __name__ == "__main__":
    dotenv.load_dotenv()
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if API_KEY is None:
        raise ValueError("OPENROUTER_API_KEY must be set as env variable")

    response = sendRequest(API_KEY)
    print(response)
