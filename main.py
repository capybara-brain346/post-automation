import os
import streamlit as st
from dotenv import load_dotenv

from workflow import run_automation
from obsidian import read_obsidian_notes
from datetime import datetime, timedelta

load_dotenv()


def display_results_in_streamlit(final_state):
    """Display the generated content directly in Streamlit"""
    st.success("🎉 Content generation completed successfully!")

    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    next_thursday = next_monday + timedelta(days=3)

    has_improved_posts = final_state.get("improved_linkedin_posts") or final_state.get(
        "improved_x_posts"
    )

    if has_improved_posts:
        post_version = st.radio(
            "Select version to display:",
            ["✨ Improved Posts (Recommended)", "📝 Original Posts"],
            index=0,
        )
        show_improved = post_version.startswith("✨")
    else:
        show_improved = False

    st.markdown("---")

    # LinkedIn Posts Section
    st.header("💼 LinkedIn Posts")

    linkedin_posts_to_show = (
        final_state.get("improved_linkedin_posts", [])
        if show_improved
        else final_state.get("linkedin_posts", [])
    )

    if linkedin_posts_to_show and len(linkedin_posts_to_show) >= 2:
        # Monday Teaser
        with st.container():
            st.subheader(f"📅 Monday Teaser ({next_monday.strftime('%B %d')})")
            monday_post = linkedin_posts_to_show[0]

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Length:** {monday_post.char_count} characters")
            with col2:
                if (
                    hasattr(monday_post, "peer_review_score")
                    and monday_post.peer_review_score
                ):
                    st.metric(
                        "Quality Score", f"{monday_post.peer_review_score:.1f}/10"
                    )
            with col3:
                if st.button("📋 Copy", key="copy_monday"):
                    st.success("Copied!")

            st.text_area(
                "Content:", monday_post.content, height=150, key="monday_content"
            )

            if monday_post.validation_notes:
                st.warning(f"⚠️ Issues: {', '.join(monday_post.validation_notes)}")

            if (
                hasattr(monday_post, "is_improved_version")
                and monday_post.is_improved_version
            ):
                st.success(f"✨ Improved: {', '.join(monday_post.improvement_notes)}")

        st.markdown("---")

        # Thursday Blog Reference
        with st.container():
            st.subheader(
                f"📅 Thursday Blog Reference ({next_thursday.strftime('%B %d')})"
            )
            thursday_post = linkedin_posts_to_show[1]

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Length:** {thursday_post.char_count} characters")
            with col2:
                if (
                    hasattr(thursday_post, "peer_review_score")
                    and thursday_post.peer_review_score
                ):
                    st.metric(
                        "Quality Score", f"{thursday_post.peer_review_score:.1f}/10"
                    )
            with col3:
                if st.button("📋 Copy", key="copy_thursday"):
                    st.success("Copied!")

            st.text_area(
                "Content:", thursday_post.content, height=200, key="thursday_content"
            )

            if thursday_post.validation_notes:
                st.warning(f"⚠️ Issues: {', '.join(thursday_post.validation_notes)}")

            if (
                hasattr(thursday_post, "is_improved_version")
                and thursday_post.is_improved_version
            ):
                st.success(f"✨ Improved: {', '.join(thursday_post.improvement_notes)}")

    st.markdown("---")

    # X Thread Section
    st.header("🐦 X Thread")

    x_posts_to_show = (
        final_state.get("improved_x_posts", [])
        if show_improved
        else final_state.get("x_posts", [])
    )

    if x_posts_to_show and len(x_posts_to_show) > 0:
        post = x_posts_to_show[0]

        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Length:** {post.char_count} characters total")
            with col2:
                if hasattr(post, "peer_review_score") and post.peer_review_score:
                    st.metric("Quality Score", f"{post.peer_review_score:.1f}/10")
            with col3:
                if st.button("📋 Copy", key="copy_x_thread"):
                    st.success("Copied!")

            st.text_area(
                "X Thread Content:",
                post.content,
                height=400,
                key="x_thread_content",
            )

            if post.validation_notes:
                st.warning(f"⚠️ Issues: {', '.join(post.validation_notes)}")

            if hasattr(post, "is_improved_version") and post.is_improved_version:
                st.success(f"✨ Improved: {', '.join(post.improvement_notes)}")

    # Peer Review & Improvements Section
    if final_state.get("improvement_summary"):
        st.markdown("---")
        st.header("🔄 Peer Review & Improvements")

        with st.expander("View improvement details", expanded=False):
            for improvement in final_state["improvement_summary"]:
                st.success(f"✨ {improvement}")

            if final_state.get("requires_human_review"):
                st.warning("⚠️ Some posts require human review due to quality concerns")

    # Validation Issues Section
    if final_state.get("validation_issues"):
        st.markdown("---")
        st.header("⚠️ Validation Notes")

        with st.expander("Review flagged items", expanded=True):
            for issue in final_state["validation_issues"]:
                st.warning(issue)
            st.info("Please review flagged items before posting.")

    # Generation Info
    st.markdown("---")
    with st.expander("ℹ️ Generation Details"):
        st.markdown(f"""
        **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
        **Blog Source:** {final_state.get("blog_url", "N/A")}  
        **LinkedIn Posts:** {len(final_state.get("linkedin_posts", []))}  
        **X Thread Parts:** {len(final_state.get("x_posts", []))}  
        **Validation Issues:** {len(final_state.get("validation_issues", []))}  
        **Improvements Made:** {len(final_state.get("improvement_summary", []))}
        """)

        if final_state.get("custom_prompt"):
            st.markdown("**Custom Instructions Used:** ✅")
        if final_state.get("obsidian_notes"):
            st.markdown("**Obsidian Notes Integrated:** ✅")


st.set_page_config(
    page_title="Social Media Content Automation", page_icon="🚀", layout="wide"
)

st.title("🚀 Social Media Content Automation")
st.markdown(
    "Generate LinkedIn and X posts from blog content with optional Obsidian notes integration"
)

required_vars = [
    "GEMINI_API_KEY",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    st.info("Please set the following environment variables:")
    for var in missing_vars:
        st.code(f"export {var}='your_value_here'")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🌐 Blog URL", "📝 Obsidian Notes", "🎯 Custom Prompt"])

blog_url = ""
obsidian_content = ""
custom_prompt = ""

with tab1:
    st.header("Blog URL Input")
    blog_url = st.text_input(
        "Enter the blog URL to process:",
        placeholder="https://example.com/blog-post",
        help="Paste the URL of the blog post you want to generate social media content from",
    )

    if blog_url:
        st.success(f"✅ Blog URL set: {blog_url}")

with tab2:
    st.header("Obsidian Notes Integration")

    input_method = st.radio(
        "Choose input method:",
        ["Upload file", "Enter file path", "Paste content directly"],
    )

    if input_method == "Upload file":
        uploaded_file = st.file_uploader(
            "Choose an Obsidian markdown file",
            type=["md"],
            help="Upload your .md file from Obsidian",
        )

        if uploaded_file is not None:
            obsidian_content = str(uploaded_file.read(), "utf-8")
            st.success(f"✅ File uploaded: {uploaded_file.name}")

            with st.expander("Preview content"):
                st.text_area(
                    "Content preview:",
                    obsidian_content[:500] + "..."
                    if len(obsidian_content) > 500
                    else obsidian_content,
                    height=200,
                    disabled=True,
                )

    elif input_method == "Enter file path":
        file_path = st.text_input(
            "Enter the full path to your Obsidian note:",
            placeholder="/path/to/your/obsidian/vault/note.md",
            help="Enter the absolute path to your Obsidian markdown file",
        )

        if file_path and st.button("Load file"):
            try:
                obsidian_content = read_obsidian_notes(file_path)
                st.success(f"✅ File loaded: {file_path}")

                with st.expander("Preview content"):
                    st.text_area(
                        "Content preview:",
                        obsidian_content[:500] + "..."
                        if len(obsidian_content) > 500
                        else obsidian_content,
                        height=200,
                        disabled=True,
                    )

            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")

    else:
        obsidian_content = st.text_area(
            "Paste your Obsidian note content:",
            height=300,
            placeholder="Paste your markdown content here...",
            help="Copy and paste the content from your Obsidian note",
        )

        if obsidian_content:
            st.success(f"✅ Content pasted ({len(obsidian_content)} characters)")

with tab3:
    st.header("Custom Prompt Instructions")
    st.markdown("""
    **Customize the AI's behavior** by adding your own instructions. These will be applied to both LinkedIn and X post generation.
    """)

    with st.expander("💡 Prompt Examples", expanded=False):
        st.markdown("""
        **Tone & Style:**
        - "Write in a conversational, friendly tone"
        - "Use technical language suitable for software engineers"
        - "Adopt a motivational, inspiring writing style"
        
        **Content Focus:**
        - "Focus on practical applications and real-world examples"
        - "Emphasize the business value and ROI"
        - "Include specific metrics and data points when possible"
        
        **Format & Structure:**
        - "Use bullet points for key takeaways"
        - "Include a compelling story or anecdote"
        - "End with actionable next steps"
        
        **Industry-Specific:**
        - "Target startup founders and entrepreneurs"
        - "Focus on enterprise-level considerations"
        - "Emphasize security and compliance aspects"
        """)

    custom_prompt = st.text_area(
        "Enter your custom instructions:",
        height=200,
        placeholder="Example: Write in a conversational tone, focus on practical applications, and include specific examples that resonate with software engineers...",
        help="These instructions will be added to the AI prompts for generating social media content",
    )

    if custom_prompt:
        st.success(f"✅ Custom prompt added ({len(custom_prompt)} characters)")

        with st.expander("Preview custom instructions"):
            st.text_area(
                "Your custom prompt:", custom_prompt, height=100, disabled=True
            )

st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button(
        "🚀 Generate Social Media Content", type="primary", use_container_width=True
    ):
        if not blog_url and not obsidian_content:
            st.error("❌ Please provide either a blog URL or Obsidian notes content")
        else:
            with st.spinner("🔄 Processing content and generating posts..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.text("🌐 Scraping blog content...")
                    progress_bar.progress(20)

                    status_text.text("📝 Processing notes and generating summary...")
                    progress_bar.progress(40)

                    status_text.text("💼 Creating LinkedIn posts...")
                    progress_bar.progress(60)

                    status_text.text("🐦 Generating X posts...")
                    progress_bar.progress(70)

                    status_text.text("🔍 Validating content...")
                    progress_bar.progress(80)

                    status_text.text("🔍 Running peer review...")
                    progress_bar.progress(90)

                    status_text.text("✨ Improving content...")
                    progress_bar.progress(95)

                    final_state = run_automation(
                        blog_url or "", obsidian_content, custom_prompt
                    )

                    progress_bar.progress(100)
                    status_text.empty()

                    if final_state and not final_state.get("error"):
                        st.balloons()
                        display_results_in_streamlit(final_state)
                    else:
                        error_msg = (
                            final_state.get("error", "Unknown error occurred")
                            if final_state
                            else "Automation failed"
                        )
                        st.error(f"❌ Content generation failed: {error_msg}")

                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()

st.markdown("---")
st.markdown("**💡 Tips:**")
st.markdown("""
- **Blog URL**: Works with most blog platforms and news sites
- **Obsidian Notes**: Can be used alone or combined with blog content
- **File Upload**: Drag and drop your .md files directly
- **File Path**: Use absolute paths like `/Users/yourname/Documents/Obsidian/note.md`
- **Direct Paste**: Copy content directly from Obsidian and paste here
- **Custom Prompt**: Add specific instructions to customize tone, style, and focus
- **Prompt Examples**: Use the expandable section for inspiration and best practices
""")

with st.sidebar:
    st.header("📋 Configuration")
    st.info("Environment variables are loaded from .env file")

    st.markdown("**Required Variables:**")
    for var in required_vars:
        status = "✅" if os.getenv(var) else "❌"
        st.markdown(f"{status} `{var}`")

    st.markdown("---")
    st.markdown("**🔧 Features:**")
    st.markdown("""
    - Blog content scraping
    - Obsidian notes integration
    - Custom prompt injection
    - LinkedIn post generation
    - X (Twitter) thread creation
    - Content validation
    - 🆕 AI peer review analysis
    - 🆕 Automated content improvement
    - Interactive results display
    """)
