import os
from dotenv import load_dotenv
from lib.workflow import run_automation
from lib.obsidian import read_obsidian_notes

load_dotenv()

IDEA_TEXT = """
Exploring the fascinating world of distributed systems and how eventual consistency works in practice. 
DNS is perhaps the largest eventually consistent system in the world, with billions of queries happening every second across multiple layers of caching and resolution.
"""

OBSIDIAN_FILE_PATH = "/home/capybara/Documents/Obsidian/DNS-Research.md"

BLOG_URL = "https://www.piyushchoudhari.me/blog/SHAP-values-for-GBTs"


def display_results(final_state):
    print("\n" + "=" * 60)
    print("📋 AUTOMATION RESULTS")
    print("=" * 60)

    print(f"📊 Current Phase: {final_state.get('phase', 'unknown')}")
    print(f"🔗 Blog URL: {final_state.get('blog_url') or 'Not yet published'}")
    print(
        f"⚠️  Requires Human Review: {final_state.get('requires_human_review', False)}"
    )

    if final_state.get("linkedin_posts"):
        print(f"\n📱 LinkedIn Posts: {len(final_state['linkedin_posts'])}")
        for i, post in enumerate(final_state["linkedin_posts"], 1):
            print(f"\n--- LinkedIn Post {i} ({post.post_type}) ---")
            print(f"Length: {post.char_count} characters")
            print(f"Scheduled: {post.scheduled_day}")
            print("Content:")
            print(
                post.content[:200] + "..." if len(post.content) > 200 else post.content
            )
            if post.validation_notes:
                print(f"⚠️ Issues: {', '.join(post.validation_notes)}")

    if final_state.get("x_posts"):
        print(f"\n🐦 X Posts: {len(final_state['x_posts'])}")
        for i, post in enumerate(final_state["x_posts"], 1):
            print(f"\n--- X Post {i} ({post.post_type}) ---")
            print(f"Length: {post.char_count} characters")
            print("Content:")
            print(
                post.content[:200] + "..." if len(post.content) > 200 else post.content
            )
            if post.validation_notes:
                print(f"⚠️ Issues: {', '.join(post.validation_notes)}")

    if final_state.get("improvement_summary"):
        print(f"\n✨ Improvements Made: {len(final_state['improvement_summary'])}")
        for improvement in final_state["improvement_summary"]:
            print(f"  • {improvement}")

    if final_state.get("validation_issues"):
        print(f"\n⚠️ Validation Issues: {len(final_state['validation_issues'])}")
        for issue in final_state["validation_issues"]:
            print(f"  • {issue}")


def main():
    print("🚀 Agentic Social Media Automation")
    print("Based on SPEC.md - Idea → Teaser → Blog → Final Posts")
    print("=" * 60)

    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"export {var}='your_value_here'")
        return

    print("✅ Environment variables configured")
    print(f"💡 Idea: {IDEA_TEXT[:100]}...")
    print(f"📝 Obsidian File: {OBSIDIAN_FILE_PATH}")
    print(f"🌐 Blog URL: {BLOG_URL or 'Not yet published'}")

    try:
        obsidian_notes = read_obsidian_notes(OBSIDIAN_FILE_PATH)
        print(
            f"✅ Successfully read {len(obsidian_notes)} characters from Obsidian file"
        )
    except FileNotFoundError:
        print(
            f"⚠️ Obsidian file not found at {OBSIDIAN_FILE_PATH}, proceeding without notes"
        )
        obsidian_notes = ""
    except Exception as e:
        print(f"⚠️ Error reading Obsidian file: {str(e)}, proceeding without notes")
        obsidian_notes = ""

    if BLOG_URL:
        phase = "final"
        print("\n🎯 Running final post generation (blog is published)")
    else:
        phase = "idea"
        print("\n🎯 Starting from idea phase (no blog URL provided)")

    try:
        final_state = run_automation(
            idea_text=IDEA_TEXT,
            obsidian_notes=obsidian_notes,
            blog_url=BLOG_URL,
            phase=phase,
        )

        display_results(final_state)

        if final_state.get("error"):
            print("\n❌ Workflow completed with errors")
            return 1
        elif final_state.get("requires_human_review"):
            print("\n⚠️ Workflow completed but requires human review")
            return 2
        else:
            print("\n🎉 Workflow completed successfully!")
            return 0

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
