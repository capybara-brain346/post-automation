import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import TypedDict, List, Optional, Dict, Any
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass, field

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email": os.getenv("EMAIL_ADDRESS"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "recipient": os.getenv("RECIPIENT_EMAIL"),
}

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
    blog_url: str
    blog_content: str
    blog_summary: str
    obsidian_notes: str
    custom_prompt: str
    linkedin_posts: List[SocialMediaPost]
    x_posts: List[SocialMediaPost]
    validation_issues: List[str]
    error: Optional[str]
    peer_review_feedback: Dict[str, Any]
    improved_linkedin_posts: List[SocialMediaPost]
    improved_x_posts: List[SocialMediaPost]
    improvement_summary: List[str]
    requires_human_review: bool


def scrape_blog_content(state: AutomationState) -> AutomationState:
    """Step 1: Scrape blog content from URL"""
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
    """Step 2: Generate key insights and summary"""
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
