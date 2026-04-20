"""Example 04 — Custom agent using OpenAI SDK behind Tsukuyomi."""
import os

from openai import OpenAI


def main() -> int:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "placeholder-will-be-rewritten"),
        base_url="http://localhost:9999/v1",
        default_headers={"User-Agent": "custom-agent/0.1"},
    )

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
    )
    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
