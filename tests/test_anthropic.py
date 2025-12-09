"""
Example: Structured output with Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
using LangChain's ChatAnthropic + native JSON-schema structured output.

Run:
  python sonnet45_structured_output.py
"""

from __future__ import annotations

import json
import os
from typing import Optional

from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()


# 1) Define the schema for the structured output
class Joke(BaseModel):
    """Joke to tell user."""
    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline of the joke")
    rating: Optional[int] = Field(
        default=None,
        description="How funny the joke is, from 1 to 10",
    )


def main() -> None:
    # Fail fast if the key is missing
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise RuntimeError("Please set the ANTHROPIC_API_KEY environment variable first.")

    # Claude Sonnet 4.5
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
        max_tokens=256,
    )

    # Wrap with native JSON-schema structured output
    structured_model = model.with_structured_output(
        Joke,
        method="json_schema",
    )

    # ✅ System instructions THEN user message
    messages = [
        (
            "system",
            (
                "You are a helpful assistant that ONLY returns valid JSON "
                "matching the given schema. The joke must be short and safe "
                "for work. Do not add any extra text."
            ),
        ),
        (
            "human",
            "Give me a joke about the weather.",
        ),
    ]

    # Call with message list
    result: Joke = structured_model.invoke(messages)
    
    import json
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    print("--------------------------------")


if __name__ == "__main__":
    main()
