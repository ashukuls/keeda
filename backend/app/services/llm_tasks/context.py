from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    def __init__(self, db_client, cache_client=None):
        self.db = db_client
        self.cache = cache_client

    async def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Fetch project-level context including settings and instructions"""
        project = await self.db.projects.find_one({"_id": ObjectId(project_id)})

        if not project:
            raise ValueError(f"Project not found: {project_id}")

        instructions = await self.db.project_instructions.find(
            {"project_id": ObjectId(project_id), "level": "project"}
        ).to_list(None)

        return {
            "project": project,
            "instructions": instructions,
            "style_guide": project.get("style_guide", {}),
            "settings": project.get("settings", {})
        }

    async def get_chapter_context(
        self,
        chapter_id: str,
        include_scenes: bool = False
    ) -> Dict[str, Any]:
        """Fetch chapter context with optional scenes"""
        chapter = await self.db.chapters.find_one({"_id": ObjectId(chapter_id)})

        if not chapter:
            raise ValueError(f"Chapter not found: {chapter_id}")

        context = {"chapter": chapter}

        if include_scenes:
            scenes = await self.db.scenes.find(
                {"chapter_id": ObjectId(chapter_id)}
            ).sort("scene_number", 1).to_list(None)
            context["scenes"] = scenes

        instructions = await self.db.project_instructions.find({
            "chapter_id": ObjectId(chapter_id),
            "level": "chapter"
        }).to_list(None)

        context["instructions"] = instructions

        return context

    async def get_scene_context(
        self,
        scene_id: str,
        include_panels: bool = False,
        include_previous: bool = True
    ) -> Dict[str, Any]:
        """Fetch scene context with optional panels and previous scene"""
        scene = await self.db.scenes.find_one({"_id": ObjectId(scene_id)})

        if not scene:
            raise ValueError(f"Scene not found: {scene_id}")

        context = {"scene": scene}

        if include_panels:
            panels = await self.db.panels.find(
                {"scene_id": ObjectId(scene_id)}
            ).sort("panel_number", 1).to_list(None)
            context["panels"] = panels

        if include_previous and scene.get("scene_number", 0) > 1:
            previous_scene = await self.db.scenes.find_one({
                "chapter_id": scene["chapter_id"],
                "scene_number": scene["scene_number"] - 1
            })
            if previous_scene:
                context["previous_scene"] = previous_scene

        instructions = await self.db.project_instructions.find({
            "scene_id": ObjectId(scene_id),
            "level": "scene"
        }).to_list(None)

        context["instructions"] = instructions

        return context

    async def get_panel_context(
        self,
        panel_id: str,
        include_neighbors: bool = True
    ) -> Dict[str, Any]:
        """Fetch panel context with optional neighboring panels"""
        panel = await self.db.panels.find_one({"_id": ObjectId(panel_id)})

        if not panel:
            raise ValueError(f"Panel not found: {panel_id}")

        context = {"panel": panel}

        if include_neighbors:
            panel_number = panel.get("panel_number", 0)

            previous_panel = await self.db.panels.find_one({
                "scene_id": panel["scene_id"],
                "panel_number": panel_number - 1
            })
            if previous_panel:
                context["previous_panel"] = previous_panel

            next_panel = await self.db.panels.find_one({
                "scene_id": panel["scene_id"],
                "panel_number": panel_number + 1
            })
            if next_panel:
                context["next_panel"] = next_panel

        images = await self.db.images.find(
            {"panel_id": ObjectId(panel_id)}
        ).to_list(None)
        context["images"] = images

        return context

    async def get_character_context(
        self,
        character_id: str,
        include_appearances: bool = False
    ) -> Dict[str, Any]:
        """Fetch character context with optional appearances"""
        character = await self.db.characters.find_one({"_id": ObjectId(character_id)})

        if not character:
            raise ValueError(f"Character not found: {character_id}")

        context = {"character": character}

        images = await self.db.images.find(
            {"character_id": ObjectId(character_id)}
        ).to_list(None)
        context["reference_images"] = images

        if include_appearances:
            panel_ids = await self.db.panels.find(
                {"character_ids": ObjectId(character_id)},
                {"_id": 1}
            ).to_list(None)
            context["appearances_count"] = len(panel_ids)

        return context

    async def get_location_context(self, location_id: str) -> Dict[str, Any]:
        """Fetch location context"""
        location = await self.db.locations.find_one({"_id": ObjectId(location_id)})

        if not location:
            raise ValueError(f"Location not found: {location_id}")

        images = await self.db.images.find(
            {"location_id": ObjectId(location_id)}
        ).to_list(None)

        return {
            "location": location,
            "reference_images": images
        }

    async def get_drafts_for_entity(
        self,
        entity_id: str,
        entity_type: str,
        draft_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch existing drafts for an entity"""
        query = {
            f"{entity_type}_id": ObjectId(entity_id)
        }

        if draft_type:
            query["draft_type"] = draft_type

        if status:
            query["status"] = status

        drafts = await self.db.drafts.find(query).sort("created_at", -1).to_list(None)

        return drafts

    async def build_hierarchical_context(
        self,
        project_id: str,
        chapter_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        panel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build complete hierarchical context from project down to panel"""
        context = {}

        context.update(await self.get_project_context(project_id))

        if chapter_id:
            context.update(await self.get_chapter_context(chapter_id))

        if scene_id:
            context.update(await self.get_scene_context(scene_id))

        if panel_id:
            context.update(await self.get_panel_context(panel_id))

        return context

    async def get_recent_generations(
        self,
        project_id: str,
        task_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent generation history for learning patterns"""
        query = {"project_id": ObjectId(project_id)}

        if task_type:
            query["task_type"] = task_type

        generations = await self.db.generations.find(query).sort(
            "created_at", -1
        ).limit(limit).to_list(None)

        return generations

    def calculate_context_size(self, context: Dict[str, Any]) -> int:
        """Estimate the size of context in tokens (rough approximation)"""
        import json
        context_str = json.dumps(context, default=str)
        return len(context_str) // 4

    async def trim_context(
        self,
        context: Dict[str, Any],
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Trim context to fit within token limits"""
        current_size = self.calculate_context_size(context)

        if current_size <= max_tokens:
            return context

        trimmed = dict(context)

        trim_order = [
            "reference_images",
            "images",
            "previous_scene",
            "scenes",
            "panels",
            "instructions"
        ]

        for key in trim_order:
            if key in trimmed and current_size > max_tokens:
                if isinstance(trimmed[key], list) and len(trimmed[key]) > 1:
                    original_length = len(trimmed[key])
                    trimmed[key] = trimmed[key][:max(1, original_length // 2)]
                else:
                    del trimmed[key]

                current_size = self.calculate_context_size(trimmed)

        return trimmed

    async def cache_context(
        self,
        key: str,
        context: Dict[str, Any],
        ttl: int = 300
    ):
        """Cache context in Redis if available"""
        if self.cache:
            import json
            await self.cache.set(
                f"context:{key}",
                json.dumps(context, default=str),
                ex=ttl
            )

    async def get_cached_context(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached context if available"""
        if self.cache:
            import json
            cached = await self.cache.get(f"context:{key}")
            if cached:
                return json.loads(cached)
        return None