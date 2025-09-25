"""Test the new simplified agent system."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_agents.base import AgentContext, AgentParameters
from app.services.llm_agents.project_summary import ProjectSummaryAgent
from app.services.llm_agents.character_list import CharacterListAgent
from app.core.config import settings


async def test_workflow():
    """Test the complete workflow from user input to characters."""

    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not configured")
        return

    # User provides story idea
    user_input = """
    A noir detective story set in a cyberpunk future where memories can be
    extracted and sold. The protagonist is a memory detective who discovers
    their own memories have been tampered with.
    """

    print("=" * 60)
    print("1. USER INPUT")
    print("=" * 60)
    print(user_input)

    # Step 1: Generate project summary
    print("\n" + "=" * 60)
    print("2. GENERATING PROJECT SUMMARY")
    print("=" * 60)

    context = AgentContext(
        project_id="test_project",
        user_id="test_user",
        data={"user_input": user_input}
    )

    project_agent = ProjectSummaryAgent(
        context=context,
        parameters=AgentParameters(temperature=0.8)
    )

    try:
        project_summary = await project_agent.execute()
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    print(f"Title: {project_summary.title}")
    print(f"Genre: {project_summary.genre}")
    print(f"Themes: {', '.join(project_summary.themes)}")
    print(f"Visual Style: {project_summary.visual_style}")
    print(f"\nDescription:\n{project_summary.description}")

    # Step 2: Generate character list
    print("\n" + "=" * 60)
    print("3. GENERATING CHARACTER LIST")
    print("=" * 60)

    context = AgentContext(
        project_id="test_project",
        user_id="test_user",
        data={
            "user_input": user_input,
            "project_summary": project_summary.model_dump(),
            "num_characters": 4
        }
    )

    character_agent = CharacterListAgent(
        context=context,
        parameters=AgentParameters(temperature=0.8)
    )

    try:
        character_list = await character_agent.execute()
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    print(f"\nGenerated {len(character_list.characters)} characters:\n")

    for char in character_list.characters:
        print(f"• {char.name} ({char.role})")
        print(f"  {char.brief}")
        if char.relationships:
            print(f"  Relationships: {json.dumps(char.relationships, indent=4)}")
        print()

    print("✅ Workflow completed successfully!")


async def main():
    print("\n" + "=" * 60)
    print("NEW AGENT SYSTEM TEST")
    print("=" * 60 + "\n")

    await test_workflow()


if __name__ == "__main__":
    asyncio.run(main())