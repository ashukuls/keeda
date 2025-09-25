from app.services.llm_tasks.tasks.scene_summary import SceneSummaryTask
from app.services.llm_tasks.tasks.character_profile import CharacterProfileTask
from app.services.llm_tasks.tasks.visual_prompt import VisualPromptTask

# Import all task implementations here to auto-register them
__all__ = [
    "SceneSummaryTask",
    "CharacterProfileTask",
    "VisualPromptTask"
]

# Auto-register tasks on import
from app.services.llm_tasks.registry import TaskRegistry

# Tasks are auto-registered via the @task_decorator