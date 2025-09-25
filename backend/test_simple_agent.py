"""Simple test for a single agent."""

import asyncio
from dotenv import load_dotenv

from app.services.llm_agents.base import AgentContext
from app.services.llm_agents.project_summary import ProjectSummaryAgent
from app.core.config import settings

# Load environment variables
load_dotenv()


async def test_project_summary():
    """Test just the project summary agent."""

    print("Testing ProjectSummaryAgent...")
    print(f"Using model: gpt-4o-mini")
    print(f"API Key configured: {bool(settings.OPENAI_API_KEY)}")

    # Create context
    context = AgentContext(
        project_id="test",
        user_id="test_user",
        data={
            "user_input": "A detective story with ghosts"
        }
    )

    try:
        # Create and execute agent
        agent = ProjectSummaryAgent(context)
        print("\nExecuting agent...")

        result = await agent.execute()

        print("\n✅ Success! Generated project summary:")
        print(f"Title: {result.title}")
        print(f"Genre: {result.genre}")
        print(f"Description: {result.description[:200]}...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_project_summary())