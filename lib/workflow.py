from langgraph.graph import StateGraph, END

from .utils import (
    AutomationState,
    scrape_blog_content,
    generate_blog_summary,
)
from .obsidian import process_obsidian_content
from .social_media import (
    generate_linkedin_posts,
    generate_x_posts,
    validate_posts,
    peer_review_agent,
    content_improver_agent,
)


def create_workflow():
    """Create the LangGraph workflow"""

    workflow = StateGraph(AutomationState)

    workflow.add_node("scraper", scrape_blog_content)
    workflow.add_node("obsidian_processor", process_obsidian_content)
    workflow.add_node("summarizer", generate_blog_summary)
    workflow.add_node("linkedin_generator", generate_linkedin_posts)
    workflow.add_node("x_generator", generate_x_posts)
    workflow.add_node("validator", validate_posts)
    workflow.add_node("peer_reviewer", peer_review_agent)
    workflow.add_node("content_improver", content_improver_agent)

    workflow.set_entry_point("scraper")
    workflow.add_edge("scraper", "obsidian_processor")
    workflow.add_edge("obsidian_processor", "summarizer")
    workflow.add_edge("summarizer", "linkedin_generator")
    workflow.add_edge("linkedin_generator", "x_generator")
    workflow.add_edge("x_generator", "validator")
    workflow.add_edge("validator", "peer_reviewer")
    workflow.add_edge("peer_reviewer", "content_improver")
    workflow.add_edge("content_improver", END)

    return workflow.compile()


def run_automation(blog_url: str, obsidian_notes: str = "", custom_prompt: str = ""):
    """Main function to run the social media automation"""
    print("🚀 Starting Social Media Content Automation")
    print("=" * 50)

    initial_state: AutomationState = {
        "blog_url": blog_url,
        "blog_content": "",
        "blog_summary": "",
        "obsidian_notes": obsidian_notes,
        "custom_prompt": custom_prompt,
        "linkedin_posts": [],
        "x_posts": [],
        "validation_issues": [],
        "error": None,
        "peer_review_feedback": {},
        "improved_linkedin_posts": [],
        "improved_x_posts": [],
        "improvement_summary": [],
        "requires_human_review": False,
    }

    app = create_workflow()
    final_state = app.invoke(initial_state)

    if final_state.get("error"):
        print(f"\n❌ Automation failed: {final_state['error']}")
    else:
        print("\n🎉 Automation completed successfully!")
        print(
            f"📊 Generated {len(final_state['linkedin_posts'])} LinkedIn posts and {len(final_state['x_posts'])} X posts"
        )
        if final_state["validation_issues"]:
            print(
                f"⚠️  Found {len(final_state['validation_issues'])} validation issues for review"
            )

    return final_state
