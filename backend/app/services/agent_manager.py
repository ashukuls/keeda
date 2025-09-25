"""Agent Manager for orchestrating LLM agents and database operations."""

from typing import List, Optional
from bson import ObjectId

from app.services.llm_agents.base import AgentContext
from app.services.llm_agents.project_summary import ProjectSummaryAgent
from app.services.llm_agents.character_list import CharacterListAgent
from app.services.llm_agents.chapter_list import ChapterListAgent
from app.services.llm_agents.scene_list import SceneListAgent
from app.services.llm_agents.panel_list import PanelListAgent
from app.services.llm_agents.character_profile import CharacterProfileAgent
from app.services.llm_agents.scene_summary import SceneSummaryAgent
from app.services.llm_agents.visual_prompt import VisualPromptAgent

from app.db.repositories.project_repository import ProjectRepository
from app.db.repositories.character_repository import CharacterRepository
from app.db.repositories.chapter_repository import ChapterRepository
from app.db.repositories.scene_repository import SceneRepository
from app.db.repositories.panel_repository import PanelRepository
from app.db.repositories.draft_repository import DraftRepository


class AgentManager:
    """Orchestrates agent execution and database operations."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.project_repo = ProjectRepository(db)
        self.character_repo = CharacterRepository(db)
        self.chapter_repo = ChapterRepository(db)
        self.scene_repo = SceneRepository(db)
        self.panel_repo = PanelRepository(db)
        self.draft_repo = DraftRepository(db)

    async def generate_project_summary(
        self, user_id: str, user_input: str
    ) -> str:
        """Generate project summary from user input."""
        # Create context
        context = AgentContext(
            project_id="",  # Will be set after creation
            user_id=user_id,
            data={"user_input": user_input}
        )

        # Execute agent
        agent = ProjectSummaryAgent(context)
        summary = await agent.execute()

        # Save to database
        project_data = {
            "user_id": ObjectId(user_id),
            "title": summary.title,
            "genre": summary.genre,
            "description": summary.description,
            "user_input": user_input,  # Store original input
            "status": "draft"
        }
        project_id = await self.project_repo.create(project_data)

        # Save as draft for versioning
        await self._save_draft(
            project_id, "project_summary", summary.dict()
        )

        return str(project_id)

    async def generate_characters(
        self, project_id: str, num_characters: int = 5
    ) -> List[str]:
        """Generate characters for a project."""
        # Load project from database
        project = await self.project_repo.get(ObjectId(project_id))
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Create context with database data
        context = AgentContext(
            project_id=project_id,
            user_id=str(project["user_id"]),
            data={
                "user_input": project.get("user_input", ""),
                "project_summary": {
                    "title": project["title"],
                    "genre": project["genre"],
                    "description": project["description"]
                },
                "num_characters": num_characters
            }
        )

        # Execute agent
        agent = CharacterListAgent(context)
        character_list = await agent.execute()

        # Save each character to database
        character_ids = []
        for char in character_list.characters:
            char_data = {
                "project_id": ObjectId(project_id),
                "name": char.name,
                "role": char.role,
                "description": char.description
            }
            char_id = await self.character_repo.create(char_data)
            character_ids.append(str(char_id))

        # Save as draft
        await self._save_draft(
            project_id, "character_list", character_list.dict()
        )

        return character_ids

    async def generate_chapters(
        self, project_id: str, num_chapters: int = 10
    ) -> List[str]:
        """Generate chapters for a project."""
        # Load project and characters from database
        project = await self.project_repo.get(ObjectId(project_id))
        if not project:
            raise ValueError(f"Project {project_id} not found")

        characters = await self.character_repo.find_by_project(
            ObjectId(project_id)
        )

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=str(project["user_id"]),
            data={
                "project_summary": {
                    "title": project["title"],
                    "genre": project["genre"],
                    "description": project["description"]
                },
                "character_list": {
                    "characters": [
                        {
                            "name": char["name"],
                            "role": char["role"],
                            "description": char["description"]
                        }
                        for char in characters
                    ]
                },
                "num_chapters": num_chapters
            }
        )

        # Execute agent
        agent = ChapterListAgent(context)
        chapter_list = await agent.execute()

        # Save each chapter to database
        chapter_ids = []
        for chapter in chapter_list.chapters:
            chapter_data = {
                "project_id": ObjectId(project_id),
                "chapter_number": chapter.number,
                "title": chapter.title,
                "summary": chapter.summary
            }
            chapter_id = await self.chapter_repo.create(chapter_data)
            chapter_ids.append(str(chapter_id))

        # Save as draft
        await self._save_draft(
            project_id, "chapter_list", chapter_list.dict()
        )

        return chapter_ids

    async def generate_scenes(
        self, chapter_id: str, num_scenes: int = 8
    ) -> List[str]:
        """Generate scenes for a chapter."""
        # Load chapter and related data
        chapter = await self.chapter_repo.get(ObjectId(chapter_id))
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        project = await self.project_repo.get(chapter["project_id"])
        characters = await self.character_repo.find_by_project(
            chapter["project_id"]
        )

        # Create context
        context = AgentContext(
            project_id=str(chapter["project_id"]),
            user_id=str(project["user_id"]),
            data={
                "project_summary": {
                    "title": project["title"],
                    "genre": project["genre"]
                },
                "character_list": {
                    "characters": [
                        {
                            "name": char["name"],
                            "role": char["role"],
                            "description": char["description"]
                        }
                        for char in characters
                    ]
                },
                "chapter": {
                    "number": chapter["chapter_number"],
                    "title": chapter["title"],
                    "summary": chapter["summary"]
                },
                "num_scenes": num_scenes
            }
        )

        # Execute agent
        agent = SceneListAgent(context)
        scene_list = await agent.execute()

        # Save each scene to database
        scene_ids = []
        for scene in scene_list.scenes:
            scene_data = {
                "chapter_id": ObjectId(chapter_id),
                "scene_number": scene.number,
                "title": scene.title,
                "description": scene.description
            }
            scene_id = await self.scene_repo.create(scene_data)
            scene_ids.append(str(scene_id))

        # Save as draft
        await self._save_draft(
            str(chapter["project_id"]), "scene_list", scene_list.dict()
        )

        return scene_ids

    async def generate_panels(
        self, scene_id: str, num_panels: int = 6
    ) -> List[str]:
        """Generate panels for a scene."""
        # Load scene and related data
        scene = await self.scene_repo.get(ObjectId(scene_id))
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        chapter = await self.chapter_repo.get(scene["chapter_id"])
        project = await self.project_repo.get(chapter["project_id"])
        characters = await self.character_repo.find_by_project(
            chapter["project_id"]
        )

        # Create context
        context = AgentContext(
            project_id=str(chapter["project_id"]),
            user_id=str(project["user_id"]),
            data={
                "character_list": {
                    "characters": [
                        {
                            "name": char["name"],
                            "role": char["role"],
                            "description": char["description"]
                        }
                        for char in characters
                    ]
                },
                "chapter": {
                    "number": chapter["chapter_number"],
                    "title": chapter["title"]
                },
                "scene": {
                    "number": scene["scene_number"],
                    "title": scene["title"],
                    "description": scene["description"]
                },
                "num_panels": num_panels
            }
        )

        # Execute agent
        agent = PanelListAgent(context)
        panel_list = await agent.execute()

        # Save each panel to database
        panel_ids = []
        for panel in panel_list.panels:
            panel_data = {
                "scene_id": ObjectId(scene_id),
                "panel_number": panel.number,
                "shot_type": panel.shot_type,
                "description": panel.description,
                "dialogue": panel.dialogue,
                "narration": panel.narration
            }
            panel_id = await self.panel_repo.create(panel_data)
            panel_ids.append(str(panel_id))

        # Save as draft
        await self._save_draft(
            str(chapter["project_id"]), "panel_list", panel_list.dict()
        )

        return panel_ids

    async def generate_character_profile(
        self, character_id: str
    ) -> str:
        """Generate detailed profile for a character."""
        # Load character and related data
        character = await self.character_repo.get(ObjectId(character_id))
        if not character:
            raise ValueError(f"Character {character_id} not found")

        project = await self.project_repo.get(character["project_id"])
        all_characters = await self.character_repo.find_by_project(
            character["project_id"]
        )

        # Create context
        context = AgentContext(
            project_id=str(character["project_id"]),
            user_id=str(project["user_id"]),
            data={
                "project_summary": {
                    "title": project["title"],
                    "genre": project["genre"],
                    "description": project["description"]
                },
                "character": {
                    "name": character["name"],
                    "role": character["role"],
                    "description": character["description"]
                },
                "character_list": {
                    "characters": [
                        {
                            "name": char["name"],
                            "role": char["role"],
                            "description": char["description"]
                        }
                        for char in all_characters
                    ]
                }
            }
        )

        # Execute agent
        agent = CharacterProfileAgent(context)
        profile = await agent.execute()

        # Update character with biography
        await self.character_repo.update(
            ObjectId(character_id),
            {"biography": profile.biography}
        )

        # Save as draft
        await self._save_draft(
            str(character["project_id"]),
            "character_profile",
            profile.dict()
        )

        return profile.biography

    async def generate_visual_prompt(
        self,
        target_type: str,
        target_id: str,
        visual_style: str = "comic book art"
    ) -> dict:
        """Generate visual prompt for panel, character, or location."""
        project_id = None
        user_id = None
        data = {"target_type": target_type, "visual_style": visual_style}

        if target_type == "panel":
            panel = await self.panel_repo.get(ObjectId(target_id))
            if not panel:
                raise ValueError(f"Panel {target_id} not found")

            scene = await self.scene_repo.get(panel["scene_id"])
            chapter = await self.chapter_repo.get(scene["chapter_id"])
            project = await self.project_repo.get(chapter["project_id"])

            project_id = str(chapter["project_id"])
            user_id = str(project["user_id"])

            data.update({
                "panel": {
                    "number": panel["panel_number"],
                    "shot_type": panel["shot_type"],
                    "description": panel["description"]
                },
                "scene": {
                    "title": scene["title"],
                    "description": scene["description"]
                },
                "project_summary": {
                    "genre": project["genre"]
                }
            })

        elif target_type == "character":
            character = await self.character_repo.get(ObjectId(target_id))
            if not character:
                raise ValueError(f"Character {target_id} not found")

            project = await self.project_repo.get(character["project_id"])
            project_id = str(character["project_id"])
            user_id = str(project["user_id"])

            data.update({
                "character": {
                    "name": character["name"],
                    "role": character["role"],
                    "description": character["description"]
                },
                "character_profile": {
                    "biography": character.get("biography", "")
                },
                "project_summary": {
                    "genre": project["genre"]
                }
            })

        else:
            raise ValueError(f"Unsupported target type: {target_type}")

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=user_id,
            data=data
        )

        # Execute agent
        agent = VisualPromptAgent(context)
        prompt = await agent.execute()

        # Save as draft
        await self._save_draft(
            project_id,
            f"visual_prompt_{target_type}",
            prompt.dict()
        )

        return prompt.dict()

    async def _save_draft(
        self, project_id: str, draft_type: str, content: dict
    ) -> str:
        """Save agent output as draft."""
        draft_data = {
            "project_id": ObjectId(project_id),
            "type": draft_type,
            "content": content,
            "status": "pending"
        }
        return await self.draft_repo.create(draft_data)