"""Debug script to display all data for a project."""

import sys
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json
from typing import Any, Dict

from app.core.config import settings


def format_datetime(dt):
    """Format datetime for display."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


def format_value(value: Any) -> str:
    """Format a value for display."""
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, datetime):
        return format_datetime(value)
    elif isinstance(value, dict):
        return json.dumps({k: format_value(v) for k, v in value.items()}, indent=2)
    elif isinstance(value, list):
        return json.dumps([format_value(v) for v in value], indent=2)
    elif isinstance(value, str) and len(value) > 200:
        return value[:200] + "..."
    else:
        return str(value)


def print_section(title: str, level: int = 0):
    """Print a section header."""
    indent = "  " * level
    if level == 0:
        print("\n" + "="*60)
        print(title)
        print("="*60)
    elif level == 1:
        print(f"\n{indent}{title}")
        print(f"{indent}" + "-"*40)
    else:
        print(f"\n{indent}{title}:")


def print_item(label: str, value: Any, level: int = 1):
    """Print a labeled item."""
    indent = "  " * level
    formatted_value = format_value(value)
    if "\n" in formatted_value:
        print(f"{indent}{label}:")
        for line in formatted_value.split("\n"):
            print(f"{indent}  {line}")
    else:
        print(f"{indent}{label}: {formatted_value}")


def debug_project(project_id: str):
    """Display all data for a project."""

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        # Get project
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            print(f"❌ Project {project_id} not found")
            return

        # Display project info
        print_section("PROJECT INFORMATION", 0)
        print_item("ID", project["_id"])
        print_item("Title", project.get("title", "N/A"))
        print_item("Genre", project.get("genre", "N/A"))
        print_item("Status", project.get("status", "N/A"))
        print_item("Created", project.get("created_at"))
        print_item("Updated", project.get("updated_at"))
        print_item("User Input", project.get("user_input", "N/A"))
        print_item("Description", project.get("description", "N/A"))

        # Get and display characters
        print_section("CHARACTERS", 0)
        characters = list(db.characters.find({"project_id": ObjectId(project_id)}))
        print(f"Total: {len(characters)} characters")

        for i, char in enumerate(characters, 1):
            print_section(f"{i}. {char['name']}", 1)
            print_item("ID", char["_id"], 2)
            print_item("Role", char.get("role", "N/A"), 2)
            print_item("Description", char.get("description", "N/A"), 2)
            if char.get("biography"):
                print_item("Biography", char["biography"], 2)

        # Get and display chapters
        print_section("CHAPTERS", 0)
        chapters = list(db.chapters.find({"project_id": ObjectId(project_id)}).sort("chapter_number", 1))
        print(f"Total: {len(chapters)} chapters")

        for chapter in chapters:
            print_section(f"Chapter {chapter['chapter_number']}: {chapter.get('title', 'Untitled')}", 1)
            print_item("ID", chapter["_id"], 2)
            print_item("Summary", chapter.get("summary", "N/A"), 2)

            # Get scenes for this chapter
            scenes = list(db.scenes.find({"chapter_id": chapter["_id"]}).sort("scene_number", 1))
            if scenes:
                print_section(f"Scenes ({len(scenes)})", 2)

                for scene in scenes:
                    print_section(f"Scene {scene['scene_number']}: {scene.get('title', 'Untitled')}", 3)
                    print_item("ID", scene["_id"], 4)
                    print_item("Description", scene.get("description", "N/A"), 4)

                    # Get panels for this scene
                    panels = list(db.panels.find({"scene_id": scene["_id"]}).sort("panel_number", 1))
                    if panels:
                        print_item(f"Panels", f"{len(panels)} panels", 4)

                        if len(panels) <= 3:  # Show all panels if 3 or fewer
                            for panel in panels:
                                print_section(f"Panel {panel['panel_number']}", 4)
                                print_item("Shot", panel.get("shot_type", "N/A"), 5)
                                print_item("Description", panel.get("description", "N/A"), 5)
                                if panel.get("dialogue"):
                                    print_item("Dialogue", panel["dialogue"], 5)
                                if panel.get("narration"):
                                    print_item("Narration", panel["narration"], 5)
                        else:  # Summary for many panels
                            print(f"      Panel types: ", end="")
                            types = [p.get("shot_type", "unknown") for p in panels]
                            print(", ".join(types))

        # Get and display drafts
        print_section("DRAFTS", 0)
        drafts = list(db.drafts.find({"project_id": ObjectId(project_id)}).sort("created_at", -1).limit(10))
        print(f"Showing latest {len(drafts)} drafts")

        for draft in drafts:
            draft_type = draft.get("type", "unknown")
            created = format_datetime(draft.get("created_at", ""))
            status = draft.get("status", "unknown")
            print(f"  [{draft_type}] {created} - Status: {status}")

        # Get and display images if any
        print_section("IMAGES", 0)
        images = list(db.images.find({"project_id": ObjectId(project_id)}).limit(10))
        if images:
            print(f"Found {len(images)} images")
            for img in images:
                print_item("ID", img["_id"], 1)
                print_item("Type", img.get("image_type", "N/A"), 1)
                if img.get("panel_id"):
                    print_item("Panel", img["panel_id"], 1)
                if img.get("character_id"):
                    print_item("Character", img["character_id"], 1)
        else:
            print("No images found")

        # Summary statistics
        print_section("SUMMARY STATISTICS", 0)
        panel_count = db.panels.count_documents({"scene_id": {"$in": [s["_id"] for s in db.scenes.find({"chapter_id": {"$in": [c["_id"] for c in chapters]}})]}})
        scene_count = db.scenes.count_documents({"chapter_id": {"$in": [c["_id"] for c in chapters]}})

        print(f"  Total Chapters: {len(chapters)}")
        print(f"  Total Scenes: {scene_count}")
        print(f"  Total Panels: {panel_count}")
        print(f"  Total Characters: {len(characters)}")
        print(f"  Total Drafts: {db.drafts.count_documents({'project_id': ObjectId(project_id)})}")
        print(f"  Total Images: {db.images.count_documents({'project_id': ObjectId(project_id)})}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


def list_projects():
    """List all projects in the database."""

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        projects = list(db.projects.find().sort("created_at", -1))

        if not projects:
            print("No projects found in database")
            return

        print_section("AVAILABLE PROJECTS", 0)

        for project in projects:
            print(f"\nID: {project['_id']}")
            print(f"  Title: {project.get('title', 'Untitled')}")
            print(f"  Genre: {project.get('genre', 'N/A')}")
            print(f"  Status: {project.get('status', 'N/A')}")
            print(f"  Created: {format_datetime(project.get('created_at', ''))}")

            # Get counts
            chapter_count = db.chapters.count_documents({"project_id": project["_id"]})
            char_count = db.characters.count_documents({"project_id": project["_id"]})
            print(f"  Stats: {chapter_count} chapters, {char_count} characters")

        print(f"\nTotal projects: {len(projects)}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        client.close()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python debug_project.py list                    - List all projects")
        print("  python debug_project.py <project_id>           - Debug specific project")
        print("\nExample:")
        print("  python debug_project.py list")
        print("  python debug_project.py 507f1f77bcf86cd799439011")
        return

    command = sys.argv[1]

    if command == "list":
        list_projects()
    else:
        # Assume it's a project ID
        debug_project(command)


if __name__ == "__main__":
    main()