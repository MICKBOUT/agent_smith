import os
import json

from openrouter import OpenRouter
import dotenv


def sendRequest(API_KEY: str = "") -> str:
    with OpenRouter(api_key=API_KEY) as client:
        print("Sending Request")
        response = client.chat.send(
            model="nvidia/nemotron-3.5-super-vl:free",
            messages=[
                {"role": "user", "content": "What is the meaning of life? in just one sentence"}
            ],
        )

        print(dir(response))
        return response.choices[0].message.content


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    # print(OPENROUTER_API_KEY)
    response = sendRequest(OPENROUTER_API_KEY)
    print(response)
