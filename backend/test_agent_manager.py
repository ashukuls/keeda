"""Test script for AgentManager with a small project."""

import asyncio
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from app.services.agent_manager_simple import SimpleAgentManager
from app.core.config import settings

# Load environment variables
load_dotenv()


async def test_agent_workflow():
    """Test the complete agent workflow with a small story."""

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Initialize SimpleAgentManager
    manager = SimpleAgentManager(db)

    # Test user and story
    test_user_id = str(ObjectId())
    test_story = """
    A young detective with the ability to see ghosts
    must solve a murder where the victim's spirit
    can't remember who killed them.
    """

    print("="*60)
    print("Testing Agent Manager Workflow")
    print("="*60)

    try:
        # Step 1: Generate project summary
        print("\n1. Generating project summary...")
        project_id = await manager.generate_project_summary(
            user_id=test_user_id,
            user_input=test_story.strip()
        )
        print(f"   ✓ Created project: {project_id}")

        # Fetch and display project
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        print(f"   Title: {project['title']}")
        print(f"   Genre: {project['genre']}")
        print(f"   Description preview: {project['description'][:200]}...")

        # Step 2: Generate characters
        print("\n2. Generating characters...")
        character_ids = await manager.generate_characters(
            project_id=project_id,
            num_characters=3  # Small test with 3 characters
        )
        print(f"   ✓ Created {len(character_ids)} characters")

        # Display characters
        for char_id in character_ids:
            char = db.characters.find_one({"_id": ObjectId(char_id)})
            print(f"   - {char['name']} ({char['role']})")

        # Step 3: Generate chapters
        print("\n3. Generating chapters...")
        chapter_ids = await manager.generate_chapters(
            project_id=project_id,
            num_chapters=3  # Small test with 3 chapters
        )
        print(f"   ✓ Created {len(chapter_ids)} chapters")

        # Display chapters
        for i, chapter_id in enumerate(chapter_ids, 1):
            chapter = db.chapters.find_one({"_id": ObjectId(chapter_id)})
            print(f"   Chapter {i}: {chapter['title']}")

        # Step 4: Generate scenes for first chapter only
        if chapter_ids:
            first_chapter_id = chapter_ids[0]
            print(f"\n4. Generating scenes for first chapter...")
            scene_ids = await manager.generate_scenes(
                chapter_id=first_chapter_id,
                num_scenes=2  # Small test with 2 scenes
            )
            print(f"   ✓ Created {len(scene_ids)} scenes")

            # Display scenes
            for i, scene_id in enumerate(scene_ids, 1):
                scene = db.scenes.find_one({"_id": ObjectId(scene_id)})
                print(f"   Scene {i}: {scene['title']}")

            # Step 5: Generate panels for first scene only
            if scene_ids:
                first_scene_id = scene_ids[0]
                print(f"\n5. Generating panels for first scene...")
                panel_ids = await manager.generate_panels(
                    scene_id=first_scene_id,
                    num_panels=3  # Small test with 3 panels
                )
                print(f"   ✓ Created {len(panel_ids)} panels")

                # Display panels
                for i, panel_id in enumerate(panel_ids, 1):
                    panel = db.panels.find_one({"_id": ObjectId(panel_id)})
                    print(f"   Panel {i} ({panel['shot_type']})")
                    if panel.get('dialogue'):
                        print(f"     Dialogue: {panel['dialogue'][:50]}...")

                # Step 6: Generate visual prompt for first panel
                if panel_ids:
                    first_panel_id = panel_ids[0]
                    print(f"\n6. Generating visual prompt for first panel...")
                    prompt = await manager.generate_visual_prompt(
                        target_type="panel",
                        target_id=first_panel_id
                    )
                    print(f"   ✓ Generated visual prompt")
                    print(f"   Prompt preview: {prompt['prompt'][:150]}...")

        # Step 7: Test character profile enhancement
        if character_ids:
            first_char_id = character_ids[0]
            first_char = db.characters.find_one({"_id": ObjectId(first_char_id)})
            print(f"\n7. Generating detailed profile for {first_char['name']}...")
            biography = await manager.generate_character_profile(first_char_id)
            print(f"   ✓ Generated character profile")
            print(f"   Biography preview: {biography[:200]}...")

        print("\n" + "="*60)
        print("✅ Workflow test completed successfully!")
        print("="*60)

        # Cleanup - delete test data
        print("\nCleaning up test data...")

        # Delete panels
        if 'panel_ids' in locals():
            for panel_id in panel_ids:
                db.panels.delete_one({"_id": ObjectId(panel_id)})

        # Delete scenes
        if 'scene_ids' in locals():
            for scene_id in scene_ids:
                db.scenes.delete_one({"_id": ObjectId(scene_id)})

        # Delete chapters
        if 'chapter_ids' in locals():
            for chapter_id in chapter_ids:
                db.chapters.delete_one({"_id": ObjectId(chapter_id)})

        # Delete characters
        if 'character_ids' in locals():
            for char_id in character_ids:
                db.characters.delete_one({"_id": ObjectId(char_id)})

        # Delete project
        db.projects.delete_one({"_id": ObjectId(project_id)})

        # Delete drafts
        drafts = db.drafts.find({"project_id": ObjectId(project_id)})
        for draft in drafts:
            db.drafts.delete_one({"_id": draft["_id"]})

        print("   ✓ Test data cleaned up")

    except Exception as e:
        print(f"\n❌ Error during workflow test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close MongoDB connection
        client.close()


async def main():
    """Run the test."""
    # Check for OpenAI API key
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in environment")
        print("Please set it in your .env file or environment variables")
        return

    await test_agent_workflow()


if __name__ == "__main__":
    asyncio.run(main())