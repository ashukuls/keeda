from typing import Dict, Any, Optional, List, Union
from app.services.llm_tasks.base import (
    BaseTask, TaskType, TaskContext, TaskParameters, TaskResult, TaskPriority
)
from app.services.llm_tasks.registry import TaskRegistry
from app.services.llm_tasks.context import ContextManager
import asyncio
import logging
from datetime import datetime, timezone
from collections import deque

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Service for executing LLM tasks with queue management and concurrency control"""

    def __init__(
        self,
        db_client,
        llm_client,
        cache_client=None,
        max_concurrent_tasks: int = 3
    ):
        self.db = db_client
        self.llm_client = llm_client
        self.cache = cache_client
        self.context_manager = ContextManager(db_client, cache_client)

        # Task queue management
        self.task_queue: deque = deque()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent = max_concurrent_tasks

        # Task results cache
        self.results_cache: Dict[str, TaskResult] = {}

    async def submit_task(
        self,
        task_type: Union[TaskType, str],
        context: TaskContext,
        parameters: Optional[TaskParameters] = None,
        execute_immediately: bool = False
    ) -> str:
        """Submit a task for execution"""
        # Convert string to TaskType if needed
        if isinstance(task_type, str):
            task_type = TaskType(task_type)

        # Get task class from registry
        task_class = TaskRegistry.get(task_type)
        if not task_class:
            raise ValueError(f"Task type not registered: {task_type}")

        # Create task instance
        task = task_class(
            db_client=self.db,
            llm_client=self.llm_client,
            context=context,
            parameters=parameters or TaskParameters()
        )

        # Create generation record and get ID
        generation_id = await task.create_generation_record()

        if execute_immediately:
            # Execute immediately and wait for result
            result = await self._execute_task(task)
            self.results_cache[generation_id] = result
            return generation_id

        # Add to queue based on priority
        priority_value = self._get_priority_value(parameters.priority if parameters else TaskPriority.MEDIUM)
        self.task_queue.append((priority_value, generation_id, task))

        # Sort queue by priority
        self.task_queue = deque(sorted(self.task_queue, key=lambda x: x[0], reverse=True))

        # Process queue if we have capacity
        asyncio.create_task(self._process_queue())

        return generation_id

    async def execute_task(
        self,
        task_type: Union[TaskType, str],
        context: TaskContext,
        parameters: Optional[TaskParameters] = None
    ) -> TaskResult:
        """Execute a task and return the result immediately"""
        generation_id = await self.submit_task(
            task_type=task_type,
            context=context,
            parameters=parameters,
            execute_immediately=True
        )
        return self.results_cache.get(generation_id)

    async def _execute_task(self, task: BaseTask) -> TaskResult:
        """Internal method to execute a single task"""
        try:
            # Build full context if needed
            if task.parameters.include_context:
                full_context = await self.context_manager.build_hierarchical_context(
                    project_id=task.context.project_id,
                    chapter_id=task.context.additional_context.get("chapter_id"),
                    scene_id=task.context.additional_context.get("scene_id"),
                    panel_id=task.context.additional_context.get("panel_id")
                )
                task.context.additional_context.update(full_context)

            # Execute the task
            result = await task.execute()

            # Cache successful result
            if result.success and result.generation_id:
                self.results_cache[result.generation_id] = result

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e),
                generation_id=task.generation_id
            )

    async def _process_queue(self):
        """Process tasks from the queue"""
        while len(self.active_tasks) < self.max_concurrent and self.task_queue:
            # Get highest priority task
            priority, generation_id, task = self.task_queue.popleft()

            # Create task coroutine
            task_coro = self._execute_task(task)

            # Create asyncio task and track it
            async_task = asyncio.create_task(task_coro)
            self.active_tasks[generation_id] = async_task

            # Clean up when done
            async_task.add_done_callback(
                lambda t: self.active_tasks.pop(generation_id, None)
            )

    def _get_priority_value(self, priority: TaskPriority) -> int:
        """Convert priority enum to numeric value"""
        priority_map = {
            TaskPriority.LOW: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.CRITICAL: 4
        }
        return priority_map.get(priority, 2)

    async def get_task_status(self, generation_id: str) -> Dict[str, Any]:
        """Get the status of a task"""
        # Check if task is active
        if generation_id in self.active_tasks:
            return {
                "status": "in_progress",
                "generation_id": generation_id
            }

        # Check if task is queued
        for _, gid, _ in self.task_queue:
            if gid == generation_id:
                return {
                    "status": "queued",
                    "generation_id": generation_id
                }

        # Check if we have cached results
        if generation_id in self.results_cache:
            result = self.results_cache[generation_id]
            return {
                "status": "completed" if result.success else "failed",
                "generation_id": generation_id,
                "result": result.dict()
            }

        # Query database for generation status
        from bson import ObjectId
        generation = await self.db.generations.find_one({"_id": ObjectId(generation_id)})

        if generation:
            return {
                "status": generation.get("status", "unknown"),
                "generation_id": generation_id,
                "error": generation.get("error_message"),
                "completed_at": generation.get("completed_at")
            }

        return {
            "status": "not_found",
            "generation_id": generation_id
        }

    async def cancel_task(self, generation_id: str) -> bool:
        """Cancel a task if it's queued or running"""
        # Check if task is active
        if generation_id in self.active_tasks:
            task = self.active_tasks[generation_id]
            task.cancel()
            return True

        # Check if task is queued and remove it
        new_queue = deque()
        cancelled = False

        for priority, gid, task in self.task_queue:
            if gid != generation_id:
                new_queue.append((priority, gid, task))
            else:
                cancelled = True

        self.task_queue = new_queue
        return cancelled

    async def get_queue_info(self) -> Dict[str, Any]:
        """Get information about the task queue"""
        return {
            "queued_tasks": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "max_concurrent": self.max_concurrent,
            "cached_results": len(self.results_cache)
        }

    async def batch_execute(
        self,
        tasks: List[Dict[str, Any]],
        max_parallel: Optional[int] = None
    ) -> List[TaskResult]:
        """Execute multiple tasks in batch"""
        max_parallel = max_parallel or self.max_concurrent

        # Create task instances
        task_instances = []
        for task_config in tasks:
            task_type = TaskType(task_config["task_type"])
            context = TaskContext(**task_config["context"])
            parameters = TaskParameters(**task_config.get("parameters", {}))

            task_class = TaskRegistry.get(task_type)
            if not task_class:
                logger.warning(f"Task type not registered: {task_type}")
                continue

            task = task_class(
                db_client=self.db,
                llm_client=self.llm_client,
                context=context,
                parameters=parameters
            )
            task_instances.append(task)

        # Execute in batches
        results = []
        for i in range(0, len(task_instances), max_parallel):
            batch = task_instances[i:i + max_parallel]
            batch_results = await asyncio.gather(
                *[self._execute_task(task) for task in batch],
                return_exceptions=True
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(TaskResult(
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)

        return results

    def clear_cache(self):
        """Clear the results cache"""
        self.results_cache.clear()

    async def cleanup(self):
        """Clean up resources"""
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(
                *self.active_tasks.values(),
                return_exceptions=True
            )

        # Clear queues and caches
        self.task_queue.clear()
        self.active_tasks.clear()
        self.results_cache.clear()