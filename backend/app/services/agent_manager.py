"""Agent Manager for orchestrating LLM agents with generation modes."""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone

from app.services.llm_agents.base import AgentContext
from app.services.llm_agents.project_summary import ProjectSummaryAgent
from app.services.llm_agents.character_list import CharacterListAgent
from app.services.llm_agents.chapter_list import ChapterListAgent
from app.services.llm_agents.scene_list import SceneListAgent
from app.services.llm_agents.panel_list import PanelListAgent
from app.services.llm_agents.character_profile import CharacterProfileAgent
from app.services.llm_agents.scene_summary import SceneSummaryAgent
from app.services.llm_agents.visual_prompt import VisualPromptAgent

from app.schemas.schemas import GenerationMode, ProjectGenerationSettings, AgentType
from app.db.repositories.project import ProjectRepository
from app.db.repositories.content import (
    CharacterRepository,
    ChapterRepository,
    SceneRepository,
    PanelRepository
)
from app.db.repositories.draft import DraftRepository
from app.models import (
    Project, Character, Chapter, Scene, Panel, Draft
)


def parse_user_instructions(instructions: str) -> ProjectGenerationSettings:
    """Parse user instructions to create generation settings."""
    settings = ProjectGenerationSettings(user_instructions=instructions)
    modes = {}

    # Default mode is review
    default_mode = GenerationMode.REVIEW

    # Check for mode indicators in instructions
    instructions_lower = instructions.lower()

    if "auto" in instructions_lower or "direct" in instructions_lower:
        default_mode = GenerationMode.DIRECT

    # Specific agent mode overrides
    if "review characters" in instructions_lower:
        modes[AgentType.CHARACTER_LIST.value] = GenerationMode.REVIEW
        modes[AgentType.CHARACTER_PROFILE.value] = GenerationMode.REVIEW
    if "auto generate chapters" in instructions_lower:
        modes[AgentType.CHAPTER_LIST.value] = GenerationMode.DIRECT
    if "review panels" in instructions_lower:
        modes[AgentType.PANEL_LIST.value] = GenerationMode.REVIEW

    # Set defaults for all agent types
    for agent_type in AgentType:
        if agent_type.value not in modes:
            modes[agent_type.value] = default_mode

    settings.agent_modes = modes
    return settings


class AgentManager:
    """Orchestrates agent execution with generation modes."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db

        # Initialize repositories
        self.project_repo = ProjectRepository()
        self.character_repo = CharacterRepository()
        self.chapter_repo = ChapterRepository()
        self.scene_repo = SceneRepository()
        self.panel_repo = PanelRepository()
        self.draft_repo = DraftRepository()

        # Set database collections directly
        self.project_repo._collection = db.projects
        self.character_repo._collection = db.characters
        self.chapter_repo._collection = db.chapters
        self.scene_repo._collection = db.scenes
        self.panel_repo._collection = db.panels
        self.draft_repo._collection = db.drafts

    async def generate_project_summary(
        self,
        user_id: str,
        user_input: str,
        user_instructions: str = "",
        mode: Optional[GenerationMode] = None
    ) -> Dict[str, Any]:
        """Generate project summary from user input."""
        # Determine mode
        settings = parse_user_instructions(user_instructions)
        generation_mode = mode or settings.get_mode(AgentType.PROJECT_SUMMARY)

        # Create context
        context = AgentContext(
            project_id="",
            user_id=user_id,
            data={"user_input": user_input}
        )

        # Execute agent
        agent = ProjectSummaryAgent(context)
        summary = await agent.execute()

        if generation_mode == GenerationMode.DIRECT:
            # Save directly to database
            project = Project(
                user_id=ObjectId(user_id),
                title=summary.title,
                genre=summary.genre,
                description=summary.description,
                user_input=user_input,
                generation_settings=settings,
                status="draft"
            )
            created_project = await self.project_repo.create(project)

            return {
                "mode": "direct",
                "project_id": str(created_project.id),
                "data": summary.dict()
            }
        else:
            # Save to drafts for review
            draft = Draft(
                project_id=None,  # No project yet
                entity_type="project_summary",
                entity_id=None,
                type="project_summary",
                content=summary.dict(),
                metadata={
                    "user_id": user_id,
                    "user_input": user_input,
                    "user_instructions": user_instructions
                },
                status="pending"
            )
            created_draft = await self.draft_repo.create(draft)

            return {
                "mode": "review",
                "draft_id": str(created_draft.id),
                "data": summary.dict(),
                "message": "Project summary generated. Please review and approve."
            }

    async def approve_project_draft(self, draft_id: str) -> str:
        """Approve a project draft and create the project."""
        draft = await self.draft_repo.get(draft_id)
        if not draft or draft.type != "project_summary":
            raise ValueError(f"Invalid project draft: {draft_id}")

        # Create project from draft
        content = draft.content
        metadata = draft.metadata

        project = Project(
            user_id=ObjectId(metadata["user_id"]),
            title=content["title"],
            genre=content["genre"],
            description=content["description"],
            user_input=metadata.get("user_input", ""),
            generation_settings=parse_user_instructions(metadata.get("user_instructions", "")),
            status="draft"
        )
        created_project = await self.project_repo.create(project)

        # Update draft status
        await self.draft_repo.update(draft_id, {
            "status": "selected",
            "project_id": created_project.id
        })

        return str(created_project.id)

    async def generate_characters(
        self,
        project_id: str,
        num_characters: int = 5,
        mode: Optional[GenerationMode] = None
    ) -> Dict[str, Any]:
        """Generate characters for a project."""
        # Load project
        project = await self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Determine mode
        settings = project.generation_settings or ProjectGenerationSettings()
        generation_mode = mode or settings.get_mode(AgentType.CHARACTER_LIST)

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=str(project.user_id),
            data={
                "user_input": project.user_input,
                "project_summary": {
                    "title": project.title,
                    "genre": project.genre,
                    "description": project.description
                },
                "num_characters": num_characters
            }
        )

        # Execute agent
        agent = CharacterListAgent(context)
        character_list = await agent.execute()

        if generation_mode == GenerationMode.DIRECT:
            # Save characters directly
            character_ids = []
            for char_data in character_list.characters:
                character = Character(
                    project_id=ObjectId(project_id),
                    name=char_data.name,
                    role=char_data.role,
                    description=char_data.description
                )
                created = await self.character_repo.create(character)
                character_ids.append(str(created.id))

            return {
                "mode": "direct",
                "character_ids": character_ids,
                "data": character_list.dict()
            }
        else:
            # Save to draft for review
            draft = Draft(
                project_id=ObjectId(project_id),
                entity_type="character_list",
                entity_id=None,
                type="character_list",
                content=character_list.dict(),
                metadata={"num_characters": num_characters},
                status="pending"
            )
            created_draft = await self.draft_repo.create(draft)

            return {
                "mode": "review",
                "draft_id": str(created_draft.id),
                "data": character_list.dict(),
                "message": f"Generated {len(character_list.characters)} characters. Please review."
            }

    async def approve_character_draft(self, draft_id: str) -> List[str]:
        """Approve character draft and create characters."""
        draft = await self.draft_repo.get(draft_id)
        if not draft or draft.type != "character_list":
            raise ValueError(f"Invalid character draft: {draft_id}")

        # Create characters from draft
        character_ids = []
        for char_data in draft.content["characters"]:
            character = Character(
                project_id=draft.project_id,
                name=char_data["name"],
                role=char_data["role"],
                description=char_data["description"]
            )
            created = await self.character_repo.create(character)
            character_ids.append(str(created.id))

        # Update draft status
        await self.draft_repo.update(draft_id, {"status": "selected"})

        return character_ids

    async def generate_chapters(
        self,
        project_id: str,
        num_chapters: int = 10,
        mode: Optional[GenerationMode] = None
    ) -> Dict[str, Any]:
        """Generate chapters for a project."""
        # Load project and characters
        project = await self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        characters = await self.character_repo.get_project_characters(project_id)

        # Determine mode
        settings = project.generation_settings or ProjectGenerationSettings()
        generation_mode = mode or settings.get_mode(AgentType.CHAPTER_LIST)

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=str(project.user_id),
            data={
                "project_summary": {
                    "title": project.title,
                    "genre": project.genre,
                    "description": project.description
                },
                "character_list": {
                    "characters": [
                        {
                            "name": char.name,
                            "role": char.role,
                            "description": char.description
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

        if generation_mode == GenerationMode.DIRECT:
            # Save chapters directly
            chapter_ids = []
            for chap_data in chapter_list.chapters:
                chapter = Chapter(
                    project_id=ObjectId(project_id),
                    chapter_number=chap_data.number,
                    title=chap_data.title,
                    summary=chap_data.summary
                )
                created = await self.chapter_repo.create(chapter)
                chapter_ids.append(str(created.id))

            return {
                "mode": "direct",
                "chapter_ids": chapter_ids,
                "data": chapter_list.dict()
            }
        else:
            # Save to draft for review
            draft = Draft(
                project_id=ObjectId(project_id),
                entity_type="chapter_list",
                entity_id=None,
                type="chapter_list",
                content=chapter_list.dict(),
                metadata={"num_chapters": num_chapters},
                status="pending"
            )
            created_draft = await self.draft_repo.create(draft)

            return {
                "mode": "review",
                "draft_id": str(created_draft.id),
                "data": chapter_list.dict(),
                "message": f"Generated {len(chapter_list.chapters)} chapters. Please review."
            }

    async def generate_scenes(
        self,
        chapter_id: str,
        num_scenes: int = 8,
        mode: Optional[GenerationMode] = None
    ) -> Dict[str, Any]:
        """Generate scenes for a chapter."""
        # Load chapter and related data
        chapter = await self.chapter_repo.get(chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        project_id = str(chapter.project_id)
        project = await self.project_repo.get(project_id)
        characters = await self.character_repo.get_project_characters(project_id)

        # Determine mode
        settings = project.generation_settings or ProjectGenerationSettings()
        generation_mode = mode or settings.get_mode(AgentType.SCENE_LIST)

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=str(project.user_id),
            data={
                "project_summary": {
                    "title": project.title,
                    "genre": project.genre
                },
                "character_list": {
                    "characters": [
                        {
                            "name": char.name,
                            "role": char.role,
                            "description": char.description
                        }
                        for char in characters
                    ]
                },
                "chapter": {
                    "number": chapter.chapter_number,
                    "title": chapter.title,
                    "summary": chapter.summary
                },
                "num_scenes": num_scenes
            }
        )

        # Execute agent
        agent = SceneListAgent(context)
        scene_list = await agent.execute()

        if generation_mode == GenerationMode.DIRECT:
            # Save scenes directly
            scene_ids = []
            for scene_data in scene_list.scenes:
                scene = Scene(
                    project_id=ObjectId(project_id),
                    chapter_id=ObjectId(chapter_id),
                    scene_number=scene_data.number,
                    title=scene_data.title,
                    description=scene_data.description
                )
                created = await self.scene_repo.create(scene)
                scene_ids.append(str(created.id))

            return {
                "mode": "direct",
                "scene_ids": scene_ids,
                "data": scene_list.dict()
            }
        else:
            # Save to draft for review
            draft = Draft(
                project_id=chapter.project_id,
                entity_type="scene_list",
                entity_id=ObjectId(chapter_id),
                type="scene_list",
                content=scene_list.dict(),
                metadata={
                    "chapter_id": chapter_id,
                    "num_scenes": num_scenes
                },
                status="pending"
            )
            created_draft = await self.draft_repo.create(draft)

            return {
                "mode": "review",
                "draft_id": str(created_draft.id),
                "data": scene_list.dict(),
                "message": f"Generated {len(scene_list.scenes)} scenes. Please review."
            }

    async def generate_panels(
        self,
        scene_id: str,
        num_panels: int = 6,
        mode: Optional[GenerationMode] = None
    ) -> Dict[str, Any]:
        """Generate panels for a scene."""
        # Load scene and related data
        scene = await self.scene_repo.get(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        chapter = await self.chapter_repo.get(str(scene.chapter_id))
        project_id = str(chapter.project_id)
        project = await self.project_repo.get(project_id)
        characters = await self.character_repo.get_project_characters(project_id)

        # Determine mode
        settings = project.generation_settings or ProjectGenerationSettings()
        generation_mode = mode or settings.get_mode(AgentType.PANEL_LIST)

        # Create context
        context = AgentContext(
            project_id=project_id,
            user_id=str(project.user_id),
            data={
                "character_list": {
                    "characters": [
                        {
                            "name": char.name,
                            "role": char.role,
                            "description": char.description
                        }
                        for char in characters
                    ]
                },
                "chapter": {
                    "number": chapter.chapter_number,
                    "title": chapter.title
                },
                "scene": {
                    "number": scene.scene_number,
                    "title": scene.title,
                    "description": scene.description
                },
                "num_panels": num_panels
            }
        )

        # Execute agent
        agent = PanelListAgent(context)
        panel_list = await agent.execute()

        if generation_mode == GenerationMode.DIRECT:
            # Save panels directly
            panel_ids = []
            for panel_data in panel_list.panels:
                panel = Panel(
                    project_id=ObjectId(chapter.project_id),
                    chapter_id=ObjectId(scene.chapter_id),
                    scene_id=ObjectId(scene_id),
                    panel_number=panel_data.number,
                    shot_type=panel_data.shot_type,
                    description=panel_data.description,
                    dialogue=panel_data.dialogue,
                    narration=panel_data.narration
                )
                created = await self.panel_repo.create(panel)
                panel_ids.append(str(created.id))

            return {
                "mode": "direct",
                "panel_ids": panel_ids,
                "data": panel_list.dict()
            }
        else:
            # Save to draft for review
            draft = Draft(
                project_id=chapter.project_id,
                entity_type="panel_list",
                entity_id=ObjectId(scene_id),
                type="panel_list",
                content=panel_list.dict(),
                metadata={
                    "scene_id": scene_id,
                    "num_panels": num_panels
                },
                status="pending"
            )
            created_draft = await self.draft_repo.create(draft)

            return {
                "mode": "review",
                "draft_id": str(created_draft.id),
                "data": panel_list.dict(),
                "message": f"Generated {len(panel_list.panels)} panels. Please review."
            }

    async def update_draft(
        self,
        draft_id: str,
        feedback: str,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Update a draft based on user feedback."""
        draft = await self.draft_repo.get(draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        if regenerate:
            # Store feedback in metadata and regenerate
            if "feedback" not in draft.metadata:
                draft.metadata["feedback"] = []
            draft.metadata["feedback"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": feedback
            })
            await self.draft_repo.update(draft_id, {"metadata": draft.metadata})

            # Regenerate based on type
            if draft.type == "character_list":
                return await self._regenerate_characters(draft, feedback)
            elif draft.type == "chapter_list":
                return await self._regenerate_chapters(draft, feedback)
            # Add more regeneration handlers as needed

            return {"message": "Regeneration not implemented for this type"}
        else:
            # Just update the draft with feedback
            draft.feedback = draft.feedback or []
            draft.feedback.append({
                "timestamp": datetime.now(timezone.utc),
                "message": feedback
            })
            await self.draft_repo.update(draft_id, {"status": "selected"})

            return {
                "message": "Draft updated with feedback",
                "draft_id": draft_id
            }

    async def _regenerate_characters(
        self,
        draft: Draft,
        feedback: str
    ) -> Dict[str, Any]:
        """Regenerate characters based on feedback."""
        # Get project
        project = await self.project_repo.get(str(draft.project_id))

        # Create context with feedback
        context = AgentContext(
            project_id=str(draft.project_id),
            user_id=str(project.user_id),
            data={
                "user_input": project.user_input,
                "project_summary": {
                    "title": project.title,
                    "genre": project.genre,
                    "description": project.description
                },
                "num_characters": draft.metadata.get("num_characters", 5),
                "feedback": feedback  # Include feedback in context
            }
        )

        # Execute agent
        agent = CharacterListAgent(context)
        character_list = await agent.execute()

        # Create new draft
        new_draft = Draft(
            project_id=draft.project_id,
            entity_type="character_list",
            entity_id=None,
            type="character_list",
            content=character_list.dict(),
            metadata=draft.metadata,
            status="pending"
        )
        created_draft = await self.draft_repo.create(new_draft)

        return {
            "mode": "review",
            "draft_id": str(created_draft.id),
            "data": character_list.dict(),
            "message": "Characters regenerated based on feedback."
        }

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get complete status of a project."""
        project = await self.project_repo.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get counts
        character_count = len(await self.character_repo.get_project_characters(project_id))
        chapters = await self.chapter_repo.get_project_chapters(project_id)
        chapter_count = len(chapters)

        # Get pending drafts
        pending_drafts = await self.draft_repo.list(
            filter={
                "project_id": ObjectId(project_id),
                "status": "pending"
            }
        )

        return {
            "project": {
                "id": str(project.id),
                "title": project.title,
                "genre": project.genre,
                "status": project.status
            },
            "statistics": {
                "characters": character_count,
                "chapters": chapter_count,
                "pending_drafts": len(pending_drafts)
            },
            "pending_drafts": [
                {
                    "id": str(draft.id),
                    "type": draft.type,
                    "created_at": draft.created_at
                }
                for draft in pending_drafts
            ]
        }