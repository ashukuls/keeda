"""Quick test for enum and tracing updates."""

import asyncio
import os
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Setup environment
os.environ['MONGODB_URL'] = 'mongodb://localhost:27017/'
os.environ['DATABASE_NAME'] = 'keeda_test'

from app.core.observability import setup_tracing
from app.services.agent_manager import AgentManager
from app.schemas.schemas import GenerationMode
from app.services.ai.base import LLMModel


async def main():
    print("Testing LLMModel enum and tracing...")
    print(f"Using model: {LLMModel.GPT_5_NANO.value}")

    # Initialize tracing
    setup_tracing(
        service_name="keeda-enum-test",
        jaeger_host="localhost",
        jaeger_port=4317,
        enabled=True
    )
    print("Tracing enabled")

    # Setup database and agent manager
    client = AsyncIOMotorClient(os.environ['MONGODB_URL'])
    db = client[os.environ['DATABASE_NAME']]
    manager = AgentManager(db)

    # Try to generate something simple (will fail without API key but that's ok)
    try:
        result = await manager.generate_project_summary(
            user_id=str(ObjectId()),
            user_input="A simple test story",
            user_instructions="auto generate everything directly",
            mode=GenerationMode.DIRECT
        )
        print(f"Success! Project: {result['project_id']}")
    except Exception as e:
        print(f"Expected error (no API key): {e}")

    print("\n✅ Test completed - Check Jaeger for traces with full prompt/response")
    print("Service: 'keeda-enum-test' in Jaeger UI")


if __name__ == "__main__":
    asyncio.run(main())