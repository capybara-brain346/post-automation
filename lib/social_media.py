from .utils import AutomationState, SocialMediaPost, llm
import json
import uuid


def generate_linkedin_posts(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("💼 Generating LinkedIn posts...")

        monday_prompt = f"""
        # Create a LinkedIn teaser post based on this blog summary. 
        
        ## Blog Summary: 
        {state["blog_summary"]}
        
        ## Sample tone and style of the content for reference:
        DNS is perhaps the largest eventually consistent system in the world. A single request travels through recursive resolvers, root servers, TLDs, and authoritative name servers, with caching at every layer to make it feel instant. The fact that this happens billions of times a second, across every corner of the globe, with so many independent actors cooperating without a central authority, is wild. And don't even get me started on how the internet itself works. Packets, literally just light pulses, race across networks and switches to reach the right machines, processes, and threads in milliseconds. It almost feels magical.

        ## Requirements:
        - 1000-1200 characters total
        - Engaging hook to grab attention
        - Professional LinkedIn tone
        - Include relevant hashtags
        - NO LINKS (this is a teaser)
        - End with a question or call for engagement

        ## Preferences:
        - Do not use emojis
        - Avoid using words that statiscally more likely to appear in the text generation of gemini-2.5-flash
        - Use acscii to visualize tough parts
        - Individual practitioner voice. Avoid team pronouns ("we", "our", "us", "the team").
        - Do not explicitly state role or motives (e.g., "I'm a dev", "to grow my network").
        
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
        # Create a LinkedIn post that references the full blog post.
        
        ## Blog Summary: 
        {state["blog_summary"]}
        ## Blog URL:
        {state["blog_url"]}
        
        ## Requirements:
        - 1000-1200 characters total
        - Reference insights from the blog
        - Include the blog URL
        - Professional but engaging tone
        - Add relevant hashtags
        - Include a clear call-to-action to read the full post
        - Share 1-2 specific takeaways from the blog

        ## Preferences:
        - Do not use emojis
        - Avoid using words that statiscally more likely to appear in the text generation of gemini-2.5-flash
        - Use acscii to visualize tough parts
        - Individual practitioner voice. Avoid team pronouns ("we", "our", "us", "the team").
        - Do not explicitly state role or motives (e.g., "I'm a dev", "to grow my network").
        
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
    if state.get("error"):
        return state

    try:
        print("🐦 Generating X posts...")

        x_prompt = f"""
        # Create a complete X (Twitter) thread based on this blog summary.
        
        ## Blog Summary: 
        {state["blog_summary"]}
        
        ## Requirements:
        Create exactly 3 separate posts for a complete thread:
        
        1. **Hook Tweet**: A short, engaging tweet (under 280 chars) that hints at the topic and creates curiosity
        
        2. **Thread Starter**: A main tweet (under 280 chars) that introduces the thread topic and says "Thread 🧵" or similar
        
        3. **Thread Content**: A complete numbered thread with 6-8 tweets, each under 280 characters:
           - Format as: "1/ First insight about..."
           - Format as: "2/ Second key point..."
           - Continue with "3/", "4/", etc.
           - Include the blog URL in the final tweet
           - Each tweet should be on a new line
        
        ## Style Guidelines:
        - Twitter-appropriate tone (casual, engaging)
        - Use line breaks between numbered tweets
        - Make each tweet valuable on its own
        - Build narrative flow through the thread
        - Individual practitioner voice. Avoid team pronouns ("we", "our", "us", "the team").
        - Do not explicitly state role or motives (e.g., "I'm a dev", "to grow my network").
        
        Return the 3 posts clearly separated, with the thread content as one cohesive block.
        """

        x_response = llm.invoke(x_prompt)
        x_content = x_response.content.strip()

        x_post = SocialMediaPost(
            content=x_content,
            platform="X",
            post_type="X Thread",
            scheduled_day="",
            char_count=len(x_content),
            validation_notes=[],
        )

        x_posts = [x_post]

        state["x_posts"] = x_posts
        print(f"✅ Generated {len(x_posts)} X posts")

    except Exception as e:
        error_msg = f"Failed to generate X posts: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def validate_posts(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("🔍 Validating posts...")

        validation_issues = []

        for post in state.get("linkedin_posts", []):
            if post.post_type == "Monday Teaser":
                if not (1000 <= post.char_count <= 1200):
                    issue = f"LinkedIn Monday post length issue: {post.char_count} chars (should be 1000-1200)"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

                if state["blog_url"].lower() in post.content.lower():
                    issue = (
                        "LinkedIn Monday teaser contains link (should not have links)"
                    )
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

            elif post.post_type == "Thursday Blog Reference":
                if not (1000 <= post.char_count <= 1200):
                    issue = f"LinkedIn Thursday post length issue: {post.char_count} chars (should be 1000-1200)"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

                if state["blog_url"].lower() not in post.content.lower():
                    issue = "LinkedIn Thursday post missing blog URL"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

        for post in state.get("x_posts", []):
            thread_lines = [
                line.strip() for line in post.content.split("\n") if line.strip()
            ]
            for line_num, line in enumerate(thread_lines, 1):
                if len(line) > 280:
                    issue = f"X thread line {line_num} too long: {len(line)} chars (max 280)"
                    post.validation_notes.append(issue)
                    validation_issues.append(issue)

        banned_team_pronouns = [" we ", " our ", " us ", " the team "]
        banned_role_phrases = [
            "i'm a dev",
            "i am a dev",
            "to grow my network",
            "to increase my network",
        ]
        for post in state.get("linkedin_posts", []) + state.get("x_posts", []):
            lower = f" {post.content.lower()} "
            if any(p in lower for p in banned_team_pronouns):
                issue = (
                    "Team-voice pronouns detected (use individual practitioner voice)"
                )
                post.validation_notes.append(issue)
                validation_issues.append(issue)
            if any(phrase in lower for phrase in banned_role_phrases):
                issue = "Explicit role/motive statement detected (omit explicit self-description/motives)"
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


def peer_review_agent(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("🔍 Running peer review analysis...")

        source_type = "blog" if state.get("blog_url") else "obsidian"
        all_posts = state.get("linkedin_posts", []) + state.get("x_posts", [])

        if not all_posts:
            print("⚠️ No posts to review")
            return state

        peer_review_feedback = {}
        requires_human_review = False

        for post in all_posts:
            post_id = (
                f"{post.platform.lower()}_{post.post_type.lower().replace(' ', '_')}"
            )

            review_prompt = f"""
            You are a senior editor reviewing this {post.platform} post. Your job is to deliver surgical, concrete edits that raise clarity and specificity without changing the author's core message or structure.

            POST CONTENT:
            {post.content}

            POST DETAILS:
            - Platform: {post.platform}
            - Type: {post.post_type}
            - Length: {post.char_count} characters
            - Source: {source_type}
            - Existing validation issues: {post.validation_notes}

            CRITERIA:
            - Engagement: precise, curiosity-driven hook without hype.
            - Specificity: replace abstractions with concrete mechanisms, examples, or numbers.
            - Platform fit: {post.platform}-native formatting and constraints.
            - Accuracy: avoid unsupported claims; flag stats without sources.
            - Style: short sentences, plain language, no emojis, no exclamation points.
            - Banlist: avoid words like "unlock", "leverage", "cutting-edge", "AI-powered", "revolutionize", "game-changer", "drive impact", "elevate", "innovative" unless quoted from a source.
            - LinkedIn length: 1000–1200 characters for both teaser and blog-reference posts.
            - Voice: individual practitioner tone; avoid team pronouns ("we", "our", "us", "the team"). Do not insert explicit role/motive statements.

            WHAT TO RETURN:
            Return ONLY valid JSON (no markdown, no code fences) with this exact shape and keys:
            {{
              "overall_score": number,
              "issues": [
                {{
                  "type": string,
                  "severity": "low"|"medium"|"high",
                  "description": string,
                  "suggestion": string,
                  "example": string
                }}
              ],
              "strengths": [string],
              "actionable_edits": [
                {{
                  "target_quote": string,
                  "rationale": string,
                  "edit_text": string
                }}
              ],
              "improvement_priority": "low"|"medium"|"high",
              "needs_human_review": boolean,
              "preserve_original": true,
              "banlist_hits": [string]
            }}

            EDIT FOCUS:
            - Prefer adding one concrete example that illustrates mechanism/cause, not just naming concepts.
            - When applicable, propose one micro ASCII sketch (3-5 lines) OR one simple equation to clarify.
            - For LinkedIn: ensure <=3 relevant hashtags max; Monday teaser has no links and ends with a question.
            - For X threads: preserve numbering and per-line <280 chars; final line includes blog URL {state.get("blog_url", "")}.

            Output the JSON only.
            """

            try:
                review_response = llm.invoke(review_prompt)
                review_content = review_response.content.strip()

                if review_content.startswith("```json"):
                    review_content = (
                        review_content.replace("```json", "").replace("```", "").strip()
                    )

                feedback = json.loads(review_content)
                peer_review_feedback[post_id] = feedback

                post.peer_review_score = feedback.get("overall_score", 8.0)

                if (
                    feedback.get("needs_human_review", False)
                    or feedback.get("overall_score", 8.0) < 6.0
                ):
                    requires_human_review = True

            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Failed to parse review for {post_id}: {e}")
                peer_review_feedback[post_id] = {
                    "overall_score": 8.0,
                    "issues": [],
                    "strengths": ["Review parsing failed"],
                    "improvement_priority": "low",
                    "needs_human_review": False,
                }
                post.peer_review_score = 8.0

        state["peer_review_feedback"] = peer_review_feedback
        state["requires_human_review"] = requires_human_review

        total_posts = len(all_posts)
        avg_score = (
            sum(post.peer_review_score or 8.0 for post in all_posts) / total_posts
        )
        print(f"✅ Peer review complete. Average score: {avg_score:.1f}/10")

    except Exception as e:
        error_msg = f"Peer review failed: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def content_improver_agent(state: AutomationState) -> AutomationState:
    if state.get("error"):
        return state

    try:
        print("✨ Generating improved content...")

        peer_feedback = state.get("peer_review_feedback", {})
        if not peer_feedback:
            print("⚠️ No peer review feedback available")
            return state

        improved_linkedin_posts = []
        improved_x_posts = []
        improvement_summary = []

        def should_improve_post(post, feedback):
            score = feedback.get("overall_score", 10)
            high_priority_issues = len(
                [i for i in feedback.get("issues", []) if i.get("severity") == "high"]
            )
            return (
                score < 8.0
                or high_priority_issues > 0
                or feedback.get("improvement_priority") == "high"
            )

        for post in state.get("linkedin_posts", []):
            post_id = (
                f"{post.platform.lower()}_{post.post_type.lower().replace(' ', '_')}"
            )
            feedback = peer_feedback.get(post_id, {})

            if should_improve_post(post, feedback):
                improved_post = improve_post_content(post, feedback, state)
                if improved_post:
                    improved_linkedin_posts.append(improved_post)
                    improvement_summary.append(
                        f"Improved LinkedIn {post.post_type}: {', '.join(improved_post.improvement_notes)}"
                    )
                else:
                    improved_linkedin_posts.append(post)
            else:
                improved_linkedin_posts.append(post)

        for post in state.get("x_posts", []):
            post_id = (
                f"{post.platform.lower()}_{post.post_type.lower().replace(' ', '_')}"
            )
            feedback = peer_feedback.get(post_id, {})

            if should_improve_post(post, feedback):
                improved_post = improve_post_content(post, feedback, state)
                if improved_post:
                    improved_x_posts.append(improved_post)
                    improvement_summary.append(
                        f"Improved X {post.post_type}: {', '.join(improved_post.improvement_notes)}"
                    )
                else:
                    improved_x_posts.append(post)
            else:
                improved_x_posts.append(post)

        state["improved_linkedin_posts"] = improved_linkedin_posts
        state["improved_x_posts"] = improved_x_posts
        state["improvement_summary"] = improvement_summary

        improvements_made = len(
            [
                p
                for p in improved_linkedin_posts + improved_x_posts
                if p.is_improved_version
            ]
        )
        print(f"✅ Content improvement complete. {improvements_made} posts improved.")

    except Exception as e:
        error_msg = f"Content improvement failed: {str(e)}"
        print(f"❌ {error_msg}")
        state["error"] = error_msg

    return state


def improve_post_content(
    original_post: SocialMediaPost, feedback: dict, state: AutomationState
) -> SocialMediaPost:
    try:
        issues = feedback.get("issues", [])
        if not issues:
            return original_post

        improvement_prompt = f"""
        Improve this {original_post.platform} post based on the peer review feedback. Keep the author's core idea and structure. Make precise, minimal edits that increase specificity and clarity.

        ORIGINAL POST:
        {original_post.content}

        CONTEXT (may use for concrete examples):
        Blog summary (if available): {state.get("blog_summary", "")}

        REQUIREMENTS (platform-aware):
        - Target length: {original_post.char_count} characters (stay within ±10%).
        - Style: short sentences, plain language, no emojis, no exclamation points, avoid hype.
        - Banlist: avoid "unlock", "leverage", "cutting-edge", "AI-powered", "revolutionize", "game-changer", "drive impact", "elevate", "innovative".
        - Specificity: add 1 concrete example grounded in the topic or summary. Prefer one micro ASCII sketch (3-5 lines) OR one simple equation if it clarifies.
        - Preserve any numbered or bulleted structure present in the original.
        - Voice: individual practitioner. Avoid team pronouns ("we", "our", "us", "the team"). Do not add explicit role/motive statements.

        - If Platform = LinkedIn and Type = "Monday Teaser":
          - 1000-1200 characters, no links, end with a genuine question, <=3 relevant hashtags.
        - If Platform = LinkedIn and Type = "Thursday Blog Reference":
          - 1000-1200 characters, include the blog URL {state.get("blog_url", "")}, 1-2 concrete takeaways, clear CTA to read more, <=3 relevant hashtags.
        - If Platform = X (Twitter) and Type contains "Thread":
          - Preserve numbered thread format, each line < 280 chars, final line includes blog URL {state.get("blog_url", "")}.

        PEER REVIEW FEEDBACK (address all issues, keep strengths):
        {json.dumps(issues, indent=2)}
        Strengths to maintain: {feedback.get("strengths", [])}

        OUTPUT:
        - Return ONLY the improved post content, nothing else. No JSON, no prefixes, no backticks.
        - Keep the voice human and specific. Do not add filler or buzzwords.
        """

        response = llm.invoke(improvement_prompt)
        improved_content = response.content.strip()

        improvement_notes = [issue["type"] for issue in issues]

        improved_post = SocialMediaPost(
            content=improved_content,
            platform=original_post.platform,
            post_type=original_post.post_type,
            scheduled_day=original_post.scheduled_day,
            char_count=len(improved_content),
            validation_notes=[],
            peer_review_score=feedback.get("overall_score", 8.0) + 1.0,
            improvement_notes=improvement_notes,
            is_improved_version=True,
            original_version_id=str(uuid.uuid4()),
        )

        return improved_post

    except Exception as e:
        print(f"⚠️ Failed to improve post: {e}")
        return original_post
