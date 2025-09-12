import os
import smtplib
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import TypedDict, List, Optional
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
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


class AutomationState(TypedDict):
    blog_url: str
    blog_content: str
    blog_summary: str
    linkedin_posts: List[SocialMediaPost]
    x_posts: List[SocialMediaPost]
    email_content: str
    validation_issues: List[str]
    error: Optional[str]


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


def generate_linkedin_posts(state: AutomationState) -> AutomationState:
    """Step 3a: Generate LinkedIn post drafts"""
    if state.get("error"):
        return state

    try:
        print("💼 Generating LinkedIn posts...")

        monday_prompt = f"""
        Create a LinkedIn teaser post based on this blog summary. 
        
        Blog Summary: {state["blog_summary"]}
        
        Requirements:
        - 150-200 words exactly
        - Engaging hook to grab attention
        - Tease the main insight without giving everything away
        - Professional LinkedIn tone
        - Include relevant hashtags
        - NO LINKS (this is a teaser)
        - End with a question or call for engagement
        
        Make it compelling enough that people want to know more.
        """

        monday_response = llm.invoke(monday_prompt)
        monday_post = SocialMediaPost(
            content=monday_response.content.strip(),
            platform="LinkedIn",
            post_type="Monday Teaser",
            scheduled_day="Monday",
            char_count=len(monday_response.content),
            validation_notes=[],
        )

        thursday_prompt = f"""
        Create a LinkedIn post that references the full blog post.
        
        Blog Summary: {state["blog_summary"]}
        Blog URL: {state["blog_url"]}
        
        Requirements:
        - 200-300 words exactly
        - Reference insights from the blog
        - Include the blog URL
        - Professional but engaging tone
        - Add relevant hashtags
        - Include a clear call-to-action to read the full post
        - Share 1-2 specific takeaways from the blog
        
        This should provide value while encouraging clicks to the full article.
        """

        thursday_response = llm.invoke(thursday_prompt)
        thursday_post = SocialMediaPost(
            content=thursday_response.content.strip(),
            platform="LinkedIn",
            post_type="Thursday Blog Reference",
            scheduled_day="Thursday",
            char_count=len(thursday_response.content),
            validation_notes=[],
        )

        state["linkedin_posts"] = [monday_post, thursday_post]
        print("✅ LinkedIn posts generated")

    except Exception as e:
        error_msg = f"Failed to generate LinkedIn posts: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def generate_x_posts(state: AutomationState) -> AutomationState:
    """Step 3b: Generate X (Twitter) post drafts"""
    if state.get("error"):
        return state

    try:
        print("🐦 Generating X posts...")

        x_prompt = f"""
        Create 3 different X (Twitter) posts based on this blog summary.
        
        Blog Summary: {state["blog_summary"]}
        
        Requirements for EACH post:
        - Maximum 280 characters (including spaces and hashtags)
        - Different angles/takeaways from the blog
        - Engaging and shareable
        - Include relevant hashtags
        - Can include the blog URL if it fits
        - Twitter-appropriate tone (more casual than LinkedIn)
        
        Create 3 distinct posts, each focusing on a different aspect:
        1. Key statistic or surprising fact
        2. Actionable tip or insight  
        3. Question or discussion starter
        
        Format: Return exactly 3 posts, numbered 1-3, each on a new line.
        """

        x_response = llm.invoke(x_prompt)
        x_content = x_response.content.strip()

        x_posts = []
        post_lines = [line.strip() for line in x_content.split("\n") if line.strip()]

        for i, line in enumerate(post_lines[:3], 1):
            clean_line = re.sub(r"^\d+[\.\)]\s*", "", line)

            x_post = SocialMediaPost(
                content=clean_line,
                platform="X",
                post_type=f"Daily Post {i}",
                scheduled_day=f"Day {i}",
                char_count=len(clean_line),
                validation_notes=[],
            )
            x_posts.append(x_post)

        state["x_posts"] = x_posts
        print(f"✅ Generated {len(x_posts)} X posts")

    except Exception as e:
        error_msg = f"Failed to generate X posts: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def validate_posts(state: AutomationState) -> AutomationState:
    """Step 4: Validate posts for length, claims, and quality"""
    if state.get("error"):
        return state

    try:
        print("🔍 Validating posts...")

        validation_issues = []

        for post in state.get("linkedin_posts", []):
            if post.post_type == "Monday Teaser":
                if not (150 <= post.char_count <= 200):
                    issue = f"LinkedIn Monday post length issue: {post.char_count} chars (should be 150-200)"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

                if state["blog_url"].lower() in post.content.lower():
                    issue = (
                        "LinkedIn Monday teaser contains link (should not have links)"
                    )
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

            elif post.post_type == "Thursday Blog Reference":
                if not (200 <= post.char_count <= 300):
                    issue = f"LinkedIn Thursday post length issue: {post.char_count} chars (should be 200-300)"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

                if state["blog_url"].lower() not in post.content.lower():
                    issue = "LinkedIn Thursday post missing blog URL"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

        for post in state.get("x_posts", []):
            if post.char_count > 280:
                issue = f"X post too long: {post.char_count} chars (max 280)"
                post.validation_notes.append(issue)
                validation_issues.append(issue)

        validation_prompt = f"""
        Review these social media posts for potentially unsupported claims or statements that need fact-checking.
        
        LinkedIn Posts:
        {[post.content for post in state.get("linkedin_posts", [])]}
        
        X Posts:
        {[post.content for post in state.get("x_posts", [])]}
        
        Flag any:
        - Specific statistics without clear sources
        - Bold claims that seem unverifiable  
        - Statements presented as facts that could be opinions
        - Exaggerated language
        
        Return a list of concerning claims that should be marked with ⚠️ for manual review.
        """

        validation_response = llm.invoke(validation_prompt)
        if (
            "⚠️" in validation_response.content
            or "concerning" in validation_response.content.lower()
        ):
            validation_issues.append(
                f"⚠️ Potential unsupported claims detected: {validation_response.content}"
            )

        state["validation_issues"] = validation_issues
        print(f"✅ Validation complete. Found {len(validation_issues)} issues.")

    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def compose_email(state: AutomationState) -> AutomationState:
    """Step 6: Compose the final email with all content"""
    if state.get("error"):
        return state

    try:
        print("📧 Composing email...")

        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        next_thursday = next_monday + timedelta(days=3)

        # Helper function to format validation notes
        def format_validation_notes(notes):
            if not notes:
                return ""
            return f'<p style="color: #e67e22;"><strong>⚠️ Issues:</strong> {", ".join(notes)}</p>'

        # Create base HTML template
        email_content = "".join(
            [
                "<html>",
                "<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>",
                "<h1 style='color: #2c3e50;'>📅 Weekly Social Media Content</h1>",
                f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
                f"<p><strong>Blog Source:</strong> <a href='{state['blog_url']}'>{state['blog_url']}</a></p>",
                "<hr style='border: 1px solid #eee; margin: 20px 0;'>",
                "<h2 style='color: #3498db;'>💼 LinkedIn Posts</h2>",
                "<div style='background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px;'>",
                f"<h3 style='color: #e74c3c;'>📅 Monday Teaser ({next_monday.strftime('%B %d')})</h3>",
                f"<p><strong>Length:</strong> {state['linkedin_posts'][0].char_count} characters</p>",
                "<div style='background: white; padding: 10px; border-left: 4px solid #3498db;'>",
                f"{state['linkedin_posts'][0].content.replace(chr(10), '<br>')}",
                "</div>",
                format_validation_notes(state["linkedin_posts"][0].validation_notes),
                "</div>",
                "<div style='background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px;'>",
                f"<h3 style='color: #27ae60;'>📅 Thursday Blog Reference ({next_thursday.strftime('%B %d')})</h3>",
                f"<p><strong>Length:</strong> {state['linkedin_posts'][1].char_count} characters</p>",
                "<div style='background: white; padding: 10px; border-left: 4px solid #27ae60;'>",
                f"{state['linkedin_posts'][1].content.replace(chr(10), '<br>')}",
                "</div>",
                format_validation_notes(state["linkedin_posts"][1].validation_notes),
                "</div>",
                "<h2 style='color: #1da1f2;'>🐦 X Posts (Daily)</h2>",
            ]
        )

        for i, post in enumerate(state.get("x_posts", []), 1):
            email_content += f"""
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h3 style="color: #1da1f2;">📅 Post {i}</h3>
                <p><strong>Length:</strong> {post.char_count}/280 characters</p>
                <div style="background: white; padding: 10px; border-left: 4px solid #1da1f2;">
                    {post.content}
                </div>
                {f'<p style="color: #e67e22;"><strong>⚠️ Issues:</strong> {", ".join(post.validation_notes)}</p>' if post.validation_notes else ""}
            </div>
            """

        if state.get("validation_issues"):
            email_content += f"""
            <h2 style="color: #e74c3c;">⚠️ Validation Notes</h2>
            <div style="background: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px;">
                <ul>
                {"".join([f"<li>{issue}</li>" for issue in state["validation_issues"]])}
                </ul>
                <p><em>Please review flagged items before posting.</em></p>
            </div>
            """

        email_content += """
        <hr style="border: 1px solid #eee; margin: 20px 0;">
        <p style="color: #7f8c8d; font-size: 0.9em;">
            <em>Generated by Social Media Automation Script</em><br>
            Remember to review all content before posting and verify any claims marked with ⚠️
        </p>
        
        </body>
        </html>
        """

        state["email_content"] = email_content
        print("✅ Email composed successfully")

    except Exception as e:
        error_msg = f"Failed to compose email: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def send_email(state: AutomationState) -> AutomationState:
    """Step 7: Send the email"""
    if state.get("error"):
        return state

    try:
        print("📤 Sending email...")

        if not all(
            [EMAIL_CONFIG["email"], EMAIL_CONFIG["password"], EMAIL_CONFIG["recipient"]]
        ):
            raise ValueError(
                "Email configuration incomplete. Please set EMAIL_ADDRESS, EMAIL_PASSWORD, and RECIPIENT_EMAIL environment variables."
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"Weekly Social Media Content - {datetime.now().strftime('%Y-%m-%d')}"
        )
        msg["From"] = EMAIL_CONFIG["email"]
        msg["To"] = EMAIL_CONFIG["recipient"]

        html_part = MIMEText(state["email_content"], "html")
        msg.attach(html_part)

        with smtplib.SMTP(
            EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]
        ) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
            server.send_message(msg)

        print("✅ Email sent successfully!")

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def create_workflow():
    """Create the LangGraph workflow"""

    workflow = StateGraph(AutomationState)

    workflow.add_node("scraper", scrape_blog_content)
    workflow.add_node("summarizer", generate_blog_summary)
    workflow.add_node("linkedin_generator", generate_linkedin_posts)
    workflow.add_node("x_generator", generate_x_posts)
    workflow.add_node("validator", validate_posts)
    workflow.add_node("email_composer", compose_email)
    workflow.add_node("email_sender", send_email)

    workflow.set_entry_point("scraper")
    workflow.add_edge("scraper", "summarizer")
    workflow.add_edge("summarizer", "linkedin_generator")
    workflow.add_edge("linkedin_generator", "x_generator")
    workflow.add_edge("x_generator", "validator")
    workflow.add_edge("validator", "email_composer")
    workflow.add_edge("email_composer", "email_sender")
    workflow.add_edge("email_sender", END)

    return workflow.compile()


def run_automation(blog_url: str):
    """Main function to run the social media automation"""
    print("🚀 Starting Social Media Content Automation")
    print("=" * 50)

    initial_state: AutomationState = {
        "blog_url": blog_url,
        "blog_content": "",
        "blog_summary": "",
        "linkedin_posts": [],
        "x_posts": [],
        "email_content": "",
        "validation_issues": [],
        "error": None,
    }

    app = create_workflow()
    final_state = app.invoke(initial_state)

    if final_state.get("error"):
        print(f"\n❌ Automation failed: {final_state['error']}")
        return False
    else:
        print("\n🎉 Automation completed successfully!")
        print(
            f"📊 Generated {len(final_state['linkedin_posts'])} LinkedIn posts and {len(final_state['x_posts'])} X posts"
        )
        if final_state["validation_issues"]:
            print(
                f"⚠️  Found {len(final_state['validation_issues'])} validation issues for review"
            )
        return True


if __name__ == "__main__":
    BLOG_URL = input("Enter the blog URL to process: ").strip()

    if not BLOG_URL:
        print("❌ Please provide a valid blog URL")
        exit(1)

    required_vars = [
        "GEMINI_API_KEY",
        "EMAIL_ADDRESS",
        "EMAIL_PASSWORD",
        "RECIPIENT_EMAIL",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"export {var}='your_value_here'")
        exit(1)

    success = run_automation(BLOG_URL)

    if success:
        print("\n📧 Check your email for the generated content!")
    else:
        print("\n❌ Automation failed. Please check the logs above.")
