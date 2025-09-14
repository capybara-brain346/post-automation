from utils import AutomationState, SocialMediaPost, llm
import json
import uuid


def generate_linkedin_posts(state: AutomationState) -> AutomationState:
    """Step 3a: Generate LinkedIn post drafts"""
    if state.get("error"):
        return state

    try:
        print("💼 Generating LinkedIn posts...")

        custom_instructions = ""
        if state.get("custom_prompt"):
            custom_instructions = f"""
        ## Custom Instructions:
        {state["custom_prompt"]}
        """

        monday_prompt = f"""
        # Create a LinkedIn teaser post based on this blog summary. 
        
        ## Blog Summary: 
        {state["blog_summary"]}
        
        ## Sample tone and style of the content for reference:
        DNS is perhaps the largest eventually consistent system in the world. A single request travels through recursive resolvers, root servers, TLDs, and authoritative name servers, with caching at every layer to make it feel instant. The fact that this happens billions of times a second, across every corner of the globe, with so many independent actors cooperating without a central authority, is wild. And don't even get me started on how the internet itself works. Packets, literally just light pulses, race across networks and switches to reach the right machines, processes, and threads in milliseconds. It almost feels magical.

        ## Requirements:
        - 150-200 words exactly
        - Engaging hook to grab attention
        - Professional LinkedIn tone
        - Include relevant hashtags
        - NO LINKS (this is a teaser)
        - End with a question or call for engagement

        ## Preferences:
        - Do not use emojis
        - Avoid using words that statiscally more likely to appear in the text generation of gemini-2.5-flash
        - Use acscii to visualize tough parts
        {custom_instructions}
        
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
        - 200-300 words exactly
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
        {custom_instructions}
        
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

        custom_instructions = ""
        if state.get("custom_prompt"):
            custom_instructions = f"""
        ## Custom Instructions:
        {state["custom_prompt"]}
        """

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
        {custom_instructions}
        
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
            thread_lines = [
                line.strip() for line in post.content.split("\n") if line.strip()
            ]
            for line_num, line in enumerate(thread_lines, 1):
                if len(line) > 280:
                    issue = f"X thread line {line_num} too long: {len(line)} chars (max 280)"
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
    """Peer review agent that analyzes posts and provides improvement feedback"""
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
            You are an expert social media strategist reviewing this {post.platform} post for improvement opportunities.
            
            POST CONTENT:
            {post.content}
            
            POST DETAILS:
            - Platform: {post.platform}
            - Type: {post.post_type}
            - Length: {post.char_count} characters
            - Source: {source_type}
            - Existing validation issues: {post.validation_notes}
            
            REVIEW CRITERIA:
            1. ENGAGEMENT: Hook strength, curiosity gap, emotional appeal
            2. PLATFORM FIT: {post.platform}-specific best practices and formatting
            3. CLARITY: Message clarity, readability, flow
            4. VALUE: Educational/entertainment value for audience
            5. ACTION: Clear call-to-action or engagement prompt
            6. BRAND VOICE: Professional yet approachable tone
            
            Provide your analysis as a JSON object with this exact structure:
            {{
                "overall_score": 7.5,
                "issues": [
                    {{
                        "type": "engagement",
                        "severity": "medium",
                        "description": "Hook could be stronger to create more curiosity",
                        "suggestion": "Start with a surprising statistic or counterintuitive statement",
                        "example": "Most developers think DNS is simple. They're wrong."
                    }}
                ],
                "strengths": ["Good length", "Clear call to action"],
                "improvement_priority": "medium",
                "needs_human_review": false
            }}
            
            SEVERITY LEVELS: "low", "medium", "high"
            IMPROVEMENT PRIORITY: "low", "medium", "high"
            OVERALL SCORE: 1-10 (10 being perfect)
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
    """Content improver agent that generates improved versions based on peer review feedback"""
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
    """Generate improved version of a single post based on feedback"""
    try:
        issues = feedback.get("issues", [])
        if not issues:
            return original_post

        custom_instructions = ""
        if state.get("custom_prompt"):
            custom_instructions = f"""
        ## Custom Instructions:
        {state["custom_prompt"]}
        """

        improvement_prompt = f"""
        Improve this {original_post.platform} post based on the peer review feedback.
        
        ORIGINAL POST:
        {original_post.content}
        
        POST REQUIREMENTS:
        - Platform: {original_post.platform}
        - Type: {original_post.post_type}
        - Target length: {original_post.char_count} characters (maintain similar length)
        
        PEER REVIEW FEEDBACK:
        Issues to address: {json.dumps(issues, indent=2)}
        Strengths to maintain: {feedback.get("strengths", [])}
        
        IMPROVEMENT GUIDELINES:
        1. Address the specific issues mentioned in the feedback
        2. Maintain the core message and key insights
        3. Preserve the strengths identified
        4. Keep the same platform-appropriate formatting
        5. Maintain professional yet engaging tone
        {custom_instructions}
        
        Return ONLY the improved post content, nothing else.
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
