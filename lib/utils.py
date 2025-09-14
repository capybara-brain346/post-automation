import os
import requests
from dotenv import load_dotenv
from typing import TypedDict, List, Optional, Dict, Any
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass, field

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7
)


@dataclass
class SocialMediaPost:
    content: str
    platform: str
    post_type: str
    scheduled_day: str
    char_count: int
    validation_notes: List[str]
    peer_review_score: Optional[float] = None
    improvement_notes: List[str] = field(default_factory=list)
    is_improved_version: bool = False
    original_version_id: Optional[str] = None


class AutomationState(TypedDict):
    idea_text: str
    obsidian_notes: str
    blog_url: str
    phase: str
    blog_content: str
    blog_summary: str
    linkedin_posts: List[SocialMediaPost]
    x_posts: List[SocialMediaPost]
    validation_issues: List[str]
    peer_review_feedback: Dict[str, Any]
    improved_linkedin_posts: List[SocialMediaPost]
    improved_x_posts: List[SocialMediaPost]
    requires_human_review: bool
    error: Optional[str]
    custom_prompt: str
    improvement_summary: List[str]


def scrape_blog_content(state: AutomationState) -> AutomationState:
    try:
        print(f"🌐 Scraping blog content from: {state['blog_url']}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(state["blog_url"], headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        content_selectors = [
            "article",
            "main",
            ".post-content",
            ".entry-content",
            ".content",
            "#content",
            ".post-body",
            ".article-content",
        ]

        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text()
                break

        if not content:
            content = soup.get_text()

        content = re.sub(r"\s+", " ", content).strip()

        title_elem = soup.find("title") or soup.find("h1")
        title = title_elem.get_text().strip() if title_elem else "Blog Post"

        state["blog_content"] = f"Title: {title}\n\nContent: {content}"
        print(f"✅ Successfully scraped {len(content)} characters")

    except Exception as e:
        error_msg = f"Failed to scrape blog content: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def generate_blog_summary(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("📝 Generating blog summary and key insights...")

        summary_prompt = f"""
        Analyze this blog post and extract key insights for social media content creation.
        
        Blog Content:
        {state["blog_content"][:4000]}  # Truncate for token limits
        
        Please provide:
        1. A concise summary (100-150 words)
        2. 3-5 key takeaways/insights
        3. Main topic/theme
        4. Target audience
        5. Key statistics or claims that need validation
        
        Format your response clearly with sections.
        """

        response = llm.invoke(summary_prompt)
        state["blog_summary"] = response.content
        print("✅ Blog summary generated")

    except Exception as e:
        error_msg = f"Failed to generate summary: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def capture_idea(state: AutomationState) -> AutomationState:
    print("💡 Capturing initial idea...")
    print(f"✅ Idea captured: {state['idea_text'][:100]}...")
    return state


def planner_agent(state: AutomationState) -> AutomationState:
    print("🎯 Planning next step based on current state...")

    if not state["blog_url"] and state["phase"] == "idea":
        state["phase"] = "teaser"
        print("📅 Planning: Generate teaser posts for Monday")
    elif not state["blog_url"] and state["phase"] == "teaser":
        state["phase"] = "draft"
        print("📝 Planning: Create blog draft for Thursday")
    elif state["blog_url"] and state["phase"] == "draft":
        state["phase"] = "final"
        print("🌐 Planning: Blog is published, generate final posts")
    elif state["blog_url"] and state["phase"] == "final":
        print("🌐 Planning: Ready to scrape blog and generate final posts")
    else:
        print("✅ Planning complete")

    return state


def teaser_generator(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("🎭 Generating teaser posts...")

        teaser_prompt = f"""
        Create engaging teaser posts based on this idea and research notes.
        
        Idea: {state["idea_text"]}
        Research Notes: {state["obsidian_notes"][:2000] if state["obsidian_notes"] else "None"}
        
        Generate:
        1. A LinkedIn teaser post (1000-1200 characters) that creates curiosity without revealing everything
        2. An X thread teaser (3-4 tweets) that hints at the upcoming content
        
        Requirements:
        - NO LINKS (this is a teaser before the blog is published)
        - Create anticipation for the full content coming later
        - Individual practitioner voice
        - No emojis or exclamation points
        """

        response = llm.invoke(teaser_prompt)

        # For now, create placeholder posts - this would need proper parsing
        linkedin_teaser = SocialMediaPost(
            content=response.content[:1200],
            platform="LinkedIn",
            post_type="Monday Teaser",
            scheduled_day="Monday",
            char_count=len(response.content[:1200]),
            validation_notes=[],
        )

        x_teaser = SocialMediaPost(
            content=response.content[1200:2400]
            if len(response.content) > 1200
            else response.content,
            platform="X",
            post_type="X Teaser",
            scheduled_day="Monday",
            char_count=len(response.content[1200:2400])
            if len(response.content) > 1200
            else len(response.content),
            validation_notes=[],
        )

        state["linkedin_posts"] = [linkedin_teaser]
        state["x_posts"] = [x_teaser]
        print("✅ Teaser posts generated")

    except Exception as e:
        error_msg = f"Failed to generate teaser posts: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def blog_drafter(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("📝 Creating blog draft...")

        draft_prompt = f"""
        Create a comprehensive blog post draft based on the initial idea and research notes.
        
        Initial Idea: {state["idea_text"]}
        Research Notes: {state["obsidian_notes"]}
        
        Create a well-structured blog post with:
        - Compelling title
        - Introduction that hooks the reader
        - Main content sections with clear headings
        - Concrete examples and explanations
        - Conclusion with key takeaways
        
        Style: Technical but accessible, individual practitioner voice, no hype words.
        """

        response = llm.invoke(draft_prompt)

        # Store the draft in blog_content for now (in real implementation, this would be saved to a file)
        state["blog_content"] = response.content
        print("✅ Blog draft created (ready for manual publishing)")

    except Exception as e:
        error_msg = f"Failed to create blog draft: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def self_evaluator(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("🔍 Self-evaluating content quality...")

        all_posts = state.get("improved_linkedin_posts", []) + state.get(
            "improved_x_posts", []
        )
        if not all_posts:
            all_posts = state.get("linkedin_posts", []) + state.get("x_posts", [])

        if not all_posts:
            print("⚠️ No posts to evaluate")
            return state

        total_score = 0
        post_count = 0

        for post in all_posts:
            score = getattr(post, "peer_review_score", 7.0)
            total_score += score
            post_count += 1

        average_score = total_score / post_count if post_count > 0 else 7.0
        threshold = 8.0

        if average_score < threshold:
            print(
                f"⚠️ Average quality score {average_score:.1f} below threshold {threshold}"
            )
            state["requires_human_review"] = True
        else:
            print(f"✅ Quality evaluation passed: {average_score:.1f}/10")

    except Exception as e:
        error_msg = f"Self-evaluation failed: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def recovery_agent(state: AutomationState) -> AutomationState:
    print("🚨 Recovery agent activated")

    if state.get("error"):
        print(f"❌ Handling error: {state['error']}")

        # Attempt basic recovery
        if (
            "timeout" in state["error"].lower()
            or "connection" in state["error"].lower()
        ):
            print("🔄 Network error detected - marking for retry")
        elif "api" in state["error"].lower():
            print("🔑 API error detected - check credentials")
        else:
            print("❓ Unknown error - marking for human review")

        state["requires_human_review"] = True

    print("✅ Recovery processing complete")
    return state
