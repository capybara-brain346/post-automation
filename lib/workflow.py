from langgraph.graph import StateGraph, END

from .utils import (
    AutomationState,
    scrape_blog_content,
    generate_blog_summary,
    capture_idea,
    planner_agent,
    teaser_generator,
    blog_drafter,
    self_evaluator,
    recovery_agent,
)
from .obsidian import process_obsidian_content
from .social_media import (
    generate_linkedin_posts,
    generate_x_posts,
    validate_posts,
    peer_review_agent,
    content_improver_agent,
)


def should_generate_teaser(state: AutomationState) -> str:
    if not state["blog_url"] and state["phase"] == "teaser":
        return "teaser_generator"
    elif state["blog_url"] and state["phase"] == "final":
        return "scraper"
    return "planner_agent"


def should_generate_blog_draft(state: AutomationState) -> str:
    if not state["blog_url"] and state["phase"] == "draft":
        return "blog_drafter"
    elif state["blog_url"] and state["phase"] == "final":
        return "scraper"
    return "planner_agent"


def should_scrape_blog(state: AutomationState) -> str:
    if state["blog_url"] and state["phase"] == "final":
        return "scraper"
    return "END"


def should_validate_or_end(state: AutomationState) -> str:
    if state.get("error"):
        return "recovery_agent"
    if state.get("linkedin_posts") or state.get("x_posts"):
        return "validator"
    return "END"


def should_improve_or_evaluate(state: AutomationState) -> str:
    if state.get("error"):
        return "recovery_agent"

    max_iterations = 3
    current_iteration = state.get("improvement_iteration_count", 0)

    if current_iteration >= max_iterations:
        print(
            f"⚠️ Maximum improvement iterations ({max_iterations}) reached, proceeding to evaluation"
        )
        return "self_evaluator"

    if state.get("validation_issues"):
        return "peer_reviewer"
    return "self_evaluator"


def should_improve_or_end(state: AutomationState) -> str:
    if state.get("error"):
        return "recovery_agent"

    # Check if we've exceeded the maximum improvement iterations
    max_iterations = 3
    current_iteration = state.get("improvement_iteration_count", 0)

    if current_iteration >= max_iterations:
        print(
            f"⚠️ Maximum improvement iterations ({max_iterations}) reached, proceeding to evaluation"
        )
        return "self_evaluator"

    peer_feedback = state.get("peer_review_feedback", {})
    needs_improvement = any(
        feedback.get("improvement_priority") in ["medium", "high"]
        for feedback in peer_feedback.values()
    )
    if needs_improvement:
        # Increment the iteration count before proceeding to content_improver
        state["improvement_iteration_count"] = current_iteration + 1
        print(
            f"🔄 Starting improvement iteration {state['improvement_iteration_count']}/{max_iterations}"
        )
        return "content_improver"
    return "self_evaluator"


def should_loop_or_end(state: AutomationState) -> str:
    if state.get("error"):
        return "recovery_agent"
    if state.get("requires_human_review"):
        return "END"

    return "END"


def create_workflow():
    workflow = StateGraph(AutomationState)

    workflow.add_node("capture_idea", capture_idea)
    workflow.add_node("obsidian_research", process_obsidian_content)
    workflow.add_node("planner_agent", planner_agent)
    workflow.add_node("teaser_generator", teaser_generator)
    workflow.add_node("blog_drafter", blog_drafter)
    workflow.add_node("scraper", scrape_blog_content)
    workflow.add_node("summarizer", generate_blog_summary)
    workflow.add_node("final_post_generator", generate_linkedin_posts)
    workflow.add_node("x_generator", generate_x_posts)
    workflow.add_node("validator", validate_posts)
    workflow.add_node("peer_reviewer", peer_review_agent)
    workflow.add_node("content_improver", content_improver_agent)
    workflow.add_node("self_evaluator", self_evaluator)
    workflow.add_node("recovery_agent", recovery_agent)

    workflow.set_entry_point("capture_idea")

    workflow.add_edge("capture_idea", "obsidian_research")
    workflow.add_edge("obsidian_research", "planner_agent")

    workflow.add_conditional_edges(
        "planner_agent",
        should_generate_teaser,
        {
            "teaser_generator": "teaser_generator",
            "planner_agent": "planner_agent",
            "scraper": "scraper",
        },
    )

    workflow.add_conditional_edges(
        "teaser_generator",
        should_generate_blog_draft,
        {
            "blog_drafter": "blog_drafter",
            "planner_agent": "planner_agent",
            "scraper": "scraper",
        },
    )

    workflow.add_conditional_edges(
        "blog_drafter", should_scrape_blog, {"scraper": "scraper", "END": END}
    )

    workflow.add_edge("scraper", "summarizer")
    workflow.add_edge("summarizer", "final_post_generator")
    workflow.add_edge("final_post_generator", "x_generator")

    workflow.add_conditional_edges(
        "x_generator",
        should_validate_or_end,
        {"validator": "validator", "recovery_agent": "recovery_agent", "END": END},
    )

    workflow.add_conditional_edges(
        "validator",
        should_improve_or_evaluate,
        {
            "peer_reviewer": "peer_reviewer",
            "self_evaluator": "self_evaluator",
            "recovery_agent": "recovery_agent",
        },
    )

    workflow.add_conditional_edges(
        "peer_reviewer",
        should_improve_or_end,
        {
            "content_improver": "content_improver",
            "self_evaluator": "self_evaluator",
            "recovery_agent": "recovery_agent",
        },
    )

    workflow.add_edge("content_improver", "validator")

    workflow.add_conditional_edges(
        "self_evaluator",
        should_loop_or_end,
        {"validator": "validator", "recovery_agent": "recovery_agent", "END": END},
    )

    workflow.add_edge("recovery_agent", END)

    return workflow.compile()


def run_automation(
    idea_text: str, obsidian_notes: str = "", blog_url: str = "", phase: str = "idea"
):
    print("🚀 Starting Agentic Social Media Automation")
    print("=" * 50)

    initial_state: AutomationState = {
        "idea_text": idea_text,
        "obsidian_notes": obsidian_notes,
        "blog_url": blog_url,
        "phase": phase,
        "blog_content": "",
        "blog_summary": "",
        "linkedin_posts": [],
        "x_posts": [],
        "validation_issues": [],
        "peer_review_feedback": {},
        "improved_linkedin_posts": [],
        "improved_x_posts": [],
        "requires_human_review": False,
        "error": None,
        "custom_prompt": "",
        "improvement_summary": [],
        "improvement_iteration_count": 0,
    }

    app = create_workflow()
    final_state = app.invoke(initial_state)

    if final_state.get("error"):
        print(f"\n❌ Automation failed: {final_state['error']}")
    elif final_state.get("requires_human_review"):
        print("\n⚠️ Automation completed but requires human review")
    else:
        print("\n🎉 Automation completed successfully!")

    print(f"📊 Phase: {final_state.get('phase', 'unknown')}")
    if final_state.get("linkedin_posts"):
        print(f"📊 Generated {len(final_state['linkedin_posts'])} LinkedIn posts")
    if final_state.get("x_posts"):
        print(f"📊 Generated {len(final_state['x_posts'])} X posts")
    if final_state.get("validation_issues"):
        print(
            f"⚠️  Found {len(final_state['validation_issues'])} validation issues for review"
        )

    return final_state
