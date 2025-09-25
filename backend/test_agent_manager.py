"""Test script for AgentManager with generation modes."""

import asyncio
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from app.services.agent_manager import AgentManager
from app.schemas.schemas import GenerationMode
from app.core.config import settings
from app.core.observability import setup_tracing

# Load environment variables
load_dotenv()


async def test_direct_mode_workflow():
    """Test the complete agent workflow in direct mode (no review)."""

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Initialize AgentManager
    manager = AgentManager(db)

    # Test user and story
    test_user_id = str(ObjectId())
    test_story = """
    A young detective with the ability to see ghosts
    must solve a murder where the victim's spirit
    can't remember who killed them.
    """

    # User instructions for direct mode
    user_instructions = "auto generate everything directly"

    print("="*60)
    print("Testing Agent Manager - DIRECT MODE")
    print("="*60)
    print("Instructions:", user_instructions)
    print("This will generate everything without review")
    print()

    try:
        # Step 1: Generate project summary
        print("1. Generating project summary...")
        result = await manager.generate_project_summary(
            user_id=test_user_id,
            user_input=test_story.strip(),
            user_instructions=user_instructions,
            mode=GenerationMode.DIRECT  # Explicit direct mode
        )

        project_id = result["project_id"]
        print(f"   ✓ Created project directly: {project_id}")
        print(f"   Title: {result['data']['title']}")
        print(f"   Genre: {result['data']['genre']}")

        # Step 2: Generate characters
        print("\n2. Generating characters...")
        result = await manager.generate_characters(
            project_id=project_id,
            num_characters=3
        )

        character_ids = result["character_ids"]
        print(f"   ✓ Created {len(character_ids)} characters directly")
        for char in result['data']['characters']:
            print(f"   - {char['name']} ({char['role']})")

        # Step 3: Generate chapters
        print("\n3. Generating chapters...")
        result = await manager.generate_chapters(
            project_id=project_id,
            num_chapters=2
        )

        chapter_ids = result["chapter_ids"]
        print(f"   ✓ Created {len(chapter_ids)} chapters directly")
        for i, chapter in enumerate(result['data']['chapters'], 1):
            print(f"   Chapter {i}: {chapter['title']}")

        # Step 4: Generate scenes for first chapter
        if chapter_ids:
            first_chapter_id = chapter_ids[0]
            print(f"\n4. Generating scenes for first chapter...")
            result = await manager.generate_scenes(
                chapter_id=first_chapter_id,
                num_scenes=2
            )

            scene_ids = result["scene_ids"]
            print(f"   ✓ Created {len(scene_ids)} scenes directly")
            for scene in result['data']['scenes']:
                print(f"   Scene {scene['number']}: {scene['title']}")

            # Step 5: Generate panels for first scene
            if scene_ids:
                first_scene_id = scene_ids[0]
                print(f"\n5. Generating panels for first scene...")
                result = await manager.generate_panels(
                    scene_id=first_scene_id,
                    num_panels=3
                )

                panel_ids = result["panel_ids"]
                print(f"   ✓ Created {len(panel_ids)} panels directly")
                for panel in result['data']['panels']:
                    print(f"   Panel {panel['number']} ({panel['shot_type']})")

        # Get project status
        print("\n6. Project Status:")
        status = await manager.get_project_status(project_id)
        print(f"   Title: {status['project']['title']}")
        print(f"   Characters: {status['statistics']['characters']}")
        print(f"   Chapters: {status['statistics']['chapters']}")
        print(f"   Pending Drafts: {status['statistics']['pending_drafts']}")

        print("\n" + "="*60)
        print("✅ Direct mode workflow completed successfully!")
        print("All content saved directly to database without review")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error during workflow test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close MongoDB connection
        client.close()


async def test_review_mode_workflow():
    """Test the workflow in review mode (with drafts)."""

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Initialize AgentManager
    manager = AgentManager(db)

    # Test user and story
    test_user_id = str(ObjectId())
    test_story = "A space detective story"

    # User instructions for review mode
    user_instructions = "review characters and panels before saving"

    print("\n" + "="*60)
    print("Testing Agent Manager - REVIEW MODE")
    print("="*60)
    print("Instructions:", user_instructions)
    print("Characters and panels will require review")
    print()

    try:
        # Step 1: Generate project summary
        print("1. Generating project summary...")
        result = await manager.generate_project_summary(
            user_id=test_user_id,
            user_input=test_story.strip(),
            user_instructions=user_instructions
        )

        if result["mode"] == "review":
            draft_id = result["draft_id"]
            print(f"   ✓ Created draft: {draft_id}")
            print(f"   Title: {result['data']['title']}")
            print(f"   Message: {result['message']}")

            # Approve the draft
            print("   Approving project draft...")
            project_id = await manager.approve_project_draft(draft_id)
            print(f"   ✓ Project approved: {project_id}")
        else:
            project_id = result["project_id"]
            print(f"   ✓ Created project directly: {project_id}")

        # Step 2: Generate characters (should be in review mode)
        print("\n2. Generating characters...")
        result = await manager.generate_characters(
            project_id=project_id,
            num_characters=2
        )

        if result["mode"] == "review":
            draft_id = result["draft_id"]
            print(f"   ✓ Created draft: {draft_id}")
            print(f"   Message: {result['message']}")

            # Provide feedback and regenerate
            print("   Providing feedback...")
            feedback_result = await manager.update_draft(
                draft_id=draft_id,
                feedback="Make the antagonist more mysterious",
                regenerate=True
            )

            new_draft_id = feedback_result["draft_id"]
            print(f"   ✓ Regenerated with feedback: {new_draft_id}")

            # Approve the new draft
            print("   Approving character draft...")
            character_ids = await manager.approve_character_draft(new_draft_id)
            print(f"   ✓ Characters approved: {len(character_ids)} created")
        else:
            print(f"   ✓ Created {len(result['character_ids'])} characters directly")

        print("\n" + "="*60)
        print("✅ Review mode workflow completed successfully!")
        print("Drafts were created and reviewed before saving")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error during workflow test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close MongoDB connection
        client.close()


async def main():
    """Run the tests."""
    # Initialize tracing FIRST
    setup_tracing(
        service_name="keeda-backend",
        jaeger_host="localhost",
        jaeger_port=4317,
        enabled=True
    )
    print("✅ Tracing enabled - Check Jaeger UI at http://localhost:16686")
    print()

    # Check for OpenAI API key
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in environment")
        print("Please set it in your .env file or environment variables")
        return

    print("Select test mode:")
    print("1. Direct Mode (no review)")
    print("2. Review Mode (with drafts)")
    print("3. Both")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        await test_direct_mode_workflow()
    elif choice == "2":
        await test_review_mode_workflow()
    elif choice == "3":
        await test_direct_mode_workflow()
        await test_review_mode_workflow()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())