import asyncio
from collections.abc import Mapping
from datetime import datetime
from typing import Any, List

from openai.types.responses.web_search_tool_param import UserLocation
from openai.types.shared.reasoning import Reasoning
from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, Runner, RunConfig, WebSearchTool
from dotenv import load_dotenv
load_dotenv()


class PlatformUpdate(BaseModel):
    """Represents a single platform update."""
    title: str = Field(description="Brief title of the update")
    description: str = Field(description="Summary of what changed or was announced")
    date: str = Field(description="When the update was released (if available)")
    source_url: str = Field(description="URL to the source article or announcement")


class PlatformUpdatesSummary(BaseModel):
    """Structured output for OpenAI Platform updates summary."""
    summary: str = Field(description="Overall summary of recent platform updates")
    updates: List[PlatformUpdate] = Field(description="List of specific platform updates")
    key_themes: List[str] = Field(description="Main themes or categories of updates")


def _get_field(obj: Any, key: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


async def main():
    agent = Agent(
        name="WebOAI website searcher",
        model="gpt-5-nano",
        instructions="""You are a helpful agent that searches for and summarizes OpenAI Platform updates.
        
When researching updates, look for:
- New API features and endpoints
- Model releases and improvements
- SDK updates
- Documentation changes
- Developer tool enhancements

Provide accurate dates and source URLs for each update found.""",
        tools=[
            WebSearchTool(
                search_context_size="low",
                user_location=UserLocation(
                    type="approximate",
                ),
            )
        ],
        output_type=PlatformUpdatesSummary,  # Enable structured output
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="low"),
            verbosity="low",
            response_include=["web_search_call.action.sources"],
        ),
    )

    today = datetime.now().strftime("%Y-%m-%d")
    query = f"Find and summarize the latest OpenAI Platform updates for developers in the last few weeks (today is {today})."
    result = await Runner.run(agent, query, run_config=RunConfig(tracing_disabled=True))

    # Extract sources from web search tool calls
    sources_list = []
    for item in result.new_items:
        if item.type != "tool_call_item":
            continue

        raw_call = item.raw_item
        call_type = _get_field(raw_call, "type")
        if call_type != "web_search_call":
            continue

        action = _get_field(raw_call, "action")
        sources = _get_field(action, "sources") if action else None
        if not sources:
            continue

        for source in sources:
            url = getattr(source, "url", None)
            if url is None and isinstance(source, Mapping):
                url = source.get("url")
            if url:
                sources_list.append(url)

    print()
    print("### Structured Output ###")
    print()
    
    # Access the structured output
    output: PlatformUpdatesSummary = result.final_output
    
    print(f"Summary: {output.summary}")
    print()
    print(f"Key Themes: {', '.join(output.key_themes)}")
    print()
    print("Updates:")
    for i, update in enumerate(output.updates, 1):
        print(f"\n{i}. {update.title}")
        print(f"   Date: {update.date}")
        print(f"   Description: {update.description}")
        print(f"   Source: {update.source_url}")
    
    print()
    print("### Web Search Sources ###")
    print()
    for url in sources_list:
        print(f"- {url}")


if __name__ == "__main__":
    asyncio.run(main())