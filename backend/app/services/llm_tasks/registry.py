from typing import Dict, Type, Optional, List
from app.services.llm_tasks.base import BaseTask, TaskType
import logging
import importlib
import inspect

logger = logging.getLogger(__name__)


class TaskRegistry:
    _instance = None
    _tasks: Dict[TaskType, Type[BaseTask]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, task_type: TaskType, task_class: Type[BaseTask]):
        """Register a task class with the registry"""
        if task_type in cls._tasks:
            logger.warning(f"Overwriting existing task: {task_type}")

        if not issubclass(task_class, BaseTask):
            raise ValueError(f"Task class must inherit from BaseTask")

        cls._tasks[task_type] = task_class
        logger.info(f"Registered task: {task_type} -> {task_class.__name__}")

    @classmethod
    def get(cls, task_type: TaskType) -> Optional[Type[BaseTask]]:
        """Get a task class by type"""
        return cls._tasks.get(task_type)

    @classmethod
    def list_tasks(cls) -> List[TaskType]:
        """List all registered task types"""
        return list(cls._tasks.keys())

    @classmethod
    def clear(cls):
        """Clear all registered tasks (mainly for testing)"""
        cls._tasks.clear()

    @classmethod
    def auto_discover(cls, module_path: str = "app.services.llm_tasks.tasks"):
        """Auto-discover and register tasks from a module"""
        try:
            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseTask)
                    and obj is not BaseTask
                    and hasattr(obj, 'task_type')
                ):
                    cls.register(obj.task_type, obj)

        except ImportError as e:
            logger.warning(f"Could not import tasks module: {e}")

    @classmethod
    def get_task_info(cls, task_type: TaskType) -> Optional[Dict[str, str]]:
        """Get information about a registered task"""
        task_class = cls.get(task_type)
        if task_class:
            return {
                "name": getattr(task_class, 'name', task_class.__name__),
                "description": getattr(task_class, 'description', 'No description'),
                "module": task_class.__module__,
                "class": task_class.__name__
            }
        return None

    @classmethod
    def validate_task_type(cls, task_type: str) -> bool:
        """Check if a task type string is valid"""
        try:
            task_enum = TaskType(task_type)
            return task_enum in cls._tasks
        except ValueError:
            return False


def task_decorator(task_type: TaskType):
    """Decorator to auto-register tasks"""
    def decorator(task_class: Type[BaseTask]):
        TaskRegistry.register(task_type, task_class)
        return task_class
    return decorator