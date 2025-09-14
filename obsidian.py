import os
import re

from utils import AutomationState


def read_obsidian_notes(file_path: str) -> str:
    """Read and process Obsidian markdown notes"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Obsidian file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        content = re.sub(r"\[\[(.*?)\]\]", r"\1", content)
        content = re.sub(r"!\[\[(.*?)\]\]", "", content)
        content = re.sub(r"#\w+", "", content)
        content = re.sub(r"\s+", " ", content).strip()

        return content

    except Exception as e:
        raise Exception(f"Failed to read Obsidian notes: {str(e)}")


def process_obsidian_content(state: AutomationState) -> AutomationState:
    """Process Obsidian notes if provided"""
    if not state.get("obsidian_notes"):
        return state

    try:
        print("📝 Processing Obsidian notes...")

        notes_content = state["obsidian_notes"]
        if state.get("blog_content"):
            combined_content = (
                f"{state['blog_content']}\n\nAdditional Notes:\n{notes_content}"
            )
        else:
            combined_content = f"Notes Content:\n{notes_content}"

        state["blog_content"] = combined_content
        print("✅ Obsidian notes integrated")

    except Exception as e:
        error_msg = f"Failed to process Obsidian notes: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state
