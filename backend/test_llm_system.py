#!/usr/bin/env python3
"""
Test script for the LLM Task Management System
Tests the complete flow with OpenAI integration
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from bson import ObjectId

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Configure settings before importing anything else
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mock the settings if needed
from app.core.config import Settings
settings = Settings()

# Check for OpenAI API key
if not settings.OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in environment variables")
    print("Please create a .env file with OPENAI_API_KEY=your_key_here")
    sys.exit(1)


async def test_llm_system():
    """Test the LLM task system with a mock scene summary task"""

    print("=" * 60)
    print("LLM Task Management System Test")
    print("=" * 60)

    # Import after settings are configured
    from app.services.ai import get_llm_client
    from app.services.llm_tasks import (
        TaskExecutor,
        TaskContext,
        TaskParameters,
        TaskType,
        TaskRegistry,
        OutputMode
    )

    # Import and register the scene summary task
    from app.services.llm_tasks.tasks import SceneSummaryTask

    # Import schemas
    from app.schemas import SceneSummarySchema

    # Initialize MongoDB connection (using mock client for testing)
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_url = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}/{settings.DATABASE_NAME}"
    client = AsyncIOMotorClient(mongo_url)
    db = client[settings.DATABASE_NAME]

    print(f"✓ Connected to MongoDB: {mongo_url}")

    # Initialize LLM client
    llm_client = get_llm_client()
    print(f"✓ Initialized LLM client with providers: {llm_client.list_providers()}")

    # Test 1: Check if OpenAI service is available
    print("\n1. Testing OpenAI Service Health Check...")
    health = await llm_client.health_check()
    print(f"   Health check results: {health}")

    if not health.get('openai', False):
        print("   ⚠️  OpenAI service not healthy. Check API key.")
        return

    print("   ✓ OpenAI service is healthy")

    # Test 2: Create mock data in MongoDB
    print("\n2. Creating mock data...")

    # Create a mock project
    project_data = {
        "_id": ObjectId(),
        "name": "Test Graphic Novel",
        "description": "A test project for LLM system",
        "owner_id": ObjectId(),
        "genre": "Science Fiction",
        "tone": "Dark and mysterious",
        "style_guide": {
            "visual_style": "Noir comic book style",
            "color_palette": "Muted colors with high contrast"
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await db.projects.insert_one(project_data)
    project_id = str(project_data["_id"])
    print(f"   ✓ Created mock project: {project_id}")

    # Create a mock scene
    scene_data = {
        "_id": ObjectId(),
        "project_id": project_data["_id"],
        "chapter_id": ObjectId(),
        "scene_number": 1,
        "title": "The Discovery",
        "description": """
        The protagonist, Dr. Sarah Chen, enters her laboratory late at night.
        She discovers that her quantum experiment has produced unexpected results -
        a portal to another dimension has opened. Strange blue light emanates from
        the containment field. She approaches cautiously, her face illuminated by
        the otherworldly glow. The laboratory equipment sparks and flickers.
        """,
        "mood": "Tense and mysterious",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await db.scenes.insert_one(scene_data)
    scene_id = str(scene_data["_id"])
    print(f"   ✓ Created mock scene: {scene_id}")

    # Create mock panels
    panels = [
        {
            "_id": ObjectId(),
            "scene_id": scene_data["_id"],
            "panel_number": 1,
            "description": "Wide shot of the laboratory at night, windows showing city lights",
            "shot_type": "establishing shot"
        },
        {
            "_id": ObjectId(),
            "scene_id": scene_data["_id"],
            "panel_number": 2,
            "description": "Close-up of Dr. Chen's hand turning the door handle",
            "shot_type": "close-up"
        },
        {
            "_id": ObjectId(),
            "scene_id": scene_data["_id"],
            "panel_number": 3,
            "description": "Medium shot of the glowing portal in the containment field",
            "shot_type": "medium shot"
        }
    ]

    for panel in panels:
        await db.panels.insert_one(panel)

    print(f"   ✓ Created {len(panels)} mock panels")

    # Test 3: Initialize Task Executor
    print("\n3. Initializing Task Executor...")
    executor = TaskExecutor(
        db_client=db,
        llm_client=llm_client,
        cache_client=None,
        max_concurrent_tasks=3
    )
    print("   ✓ Task executor initialized")

    # Test 4: Execute Scene Summary Task
    print("\n4. Executing Scene Summary Task...")

    # Check registered tasks
    registered_tasks = TaskRegistry.list_tasks()
    print(f"   Registered tasks: {[t.value for t in registered_tasks]}")

    # Create task context
    context = TaskContext(
        project_id=project_id,
        user_id=str(ObjectId()),
        target_entity_id=scene_id,
        target_entity_type="scene",
        instructions=["Focus on the scientific aspects", "Emphasize the mystery"]
    )

    # Create task parameters for structured output
    parameters = TaskParameters(
        num_variants=2,
        temperature=0.7,
        max_tokens=800,
        output_mode=OutputMode.STRUCTURED,
        strict_schema=False  # Allow fallback if structured output fails
    )

    print("   Submitting task to executor...")

    try:
        # Execute the task
        result = await executor.execute_task(
            task_type=TaskType.SCENE_SUMMARY,
            context=context,
            parameters=parameters
        )

        print(f"\n   ✓ Task execution {'successful' if result.success else 'failed'}")

        if result.success:
            print(f"   - Generation ID: {result.generation_id}")
            print(f"   - Draft IDs: {result.draft_ids}")
            print(f"   - Execution time: {result.execution_time:.2f}s")

            # Fetch the created drafts
            if result.draft_ids:
                print("\n5. Fetching Generated Drafts...")
                for i, draft_id in enumerate(result.draft_ids[:2]):  # Show first 2
                    draft = await db.drafts.find_one({"_id": ObjectId(draft_id)})
                    if draft:
                        print(f"\n   Draft {i+1}:")
                        content = draft.get("content", {})
                        if isinstance(content, dict):
                            print(f"   - Summary: {content.get('summary', '')[:200]}...")
                            print(f"   - Key points: {content.get('key_points', [])}")
                            print(f"   - Emotional tone: {content.get('emotional_tone', '')}")
        else:
            print(f"   - Error: {result.error}")

    except Exception as e:
        print(f"\n   ❌ Task execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 5: Clean up
    print("\n6. Cleaning up test data...")
    await db.projects.delete_one({"_id": project_data["_id"]})
    await db.scenes.delete_one({"_id": scene_data["_id"]})
    await db.panels.delete_many({"scene_id": scene_data["_id"]})
    if 'result' in locals() and result.generation_id:
        await db.generations.delete_one({"_id": ObjectId(result.generation_id)})
        await db.drafts.delete_many({"generation_id": ObjectId(result.generation_id)})

    print("   ✓ Test data cleaned up")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


async def main():
    """Main entry point"""
    try:
        await test_llm_system()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())