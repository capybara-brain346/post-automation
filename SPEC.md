# 📄 Technical Specification: Agentic Social Media Automation

## 1. Objective

Automate the lifecycle of content creation from **idea → teaser → blog → final posts** using an **agentic workflow**.
The system adapts to context (phase of content, blog status) and loops through validation, peer review, and improvement until posts are ready for publishing.

---

## 2. Functional Requirements

### Inputs

- **Hard-coded constants**:

  - `IDEA_TEXT`: seed idea.
  - `OBSIDIAN_NOTES`: research + draft material.
  - `BLOG_URL`: empty until blog is published, then filled with the live link.

### State Fields

- `idea_text`: string (initial idea).
- `obsidian_notes`: string (research content).
- `blog_url`: string (empty until blog is published).
- `phase`: string (`idea`, `teaser`, `draft`, `final`).
- `blog_content`: string (scraped from blog_url).
- `blog_summary`: string (condensed version of blog).
- `linkedin_posts`: list (generated LinkedIn posts).
- `x_posts`: list (generated X posts).
- `validation_issues`: list (problems found in draft posts).
- `peer_review_feedback`: dict (feedback from review agent).
- `improved_linkedin_posts`: list.
- `improved_x_posts`: list.
- `requires_human_review`: bool (true if automation fails after retries).

---

## 3. Workflow Structure

### Nodes

1. **capture_idea**

   - Stores hard-coded `IDEA_TEXT`.

2. **obsidian_research**

   - Processes `OBSIDIAN_NOTES`.
   - Expands ideas, adds context.

3. **planner_agent**

   - Decides next step:

     - If `blog_url` empty + phase=idea → `teaser_generator`.
     - If `blog_url` empty + phase=draft → `blog_drafter`.
     - If `blog_url` filled → `scraper`.

4. **teaser_generator**

   - Generates LinkedIn + X teaser posts.
   - Outputs to `linkedin_posts`, `x_posts`.

5. **blog_drafter**

   - Converts `obsidian_notes` into blog draft (to be published manually).

6. **scraper**

   - Scrapes content from `blog_url`.
   - Populates `blog_content`.

7. **summarizer**

   - Summarizes blog into `blog_summary`.

8. **final_post_generator**

   - Generates LinkedIn + X posts linking to the blog.

9. **validator**

   - Checks posts for style, tone, platform limits.

10. **peer_reviewer**

    - Gives structured improvement suggestions.

11. **content_improver**

    - Rewrites posts based on feedback.

12. **self_evaluator**

    - Scores posts; if score < threshold, loops back to improver.

13. **recovery_agent**

    - Handles errors, sets `requires_human_review=True` if unresolved.

---

## 4. Control Flow

1. **Entry Point** → `capture_idea`.
2. **Planner-driven routing**:

   - `teaser_generator` (for Monday teaser).
   - `blog_drafter` (for Thursday draft).
   - `scraper → summarizer → final_post_generator` (after blog is published).

3. **Validation loop**:

   - `validator` → if invalid → `peer_reviewer → content_improver → validator`.
   - If 3 retries fail → mark `requires_human_review=True` → END.

4. **Reflection loop**:

   - `self_evaluator` → if score < threshold → `content_improver`.

5. **End State**:

   - Posts ready, or flagged for human review.

---

## 5. Non-Functional Notes

- **Simplicity**: Inputs are hard-coded for now.
- **Extensibility**: Later, inputs can be read from CLI or config.
- **Parallelism**: LinkedIn + X post generation runs in parallel.
- **Error Handling**: Any exception routes to `recovery_agent`.
- **Human-in-the-Loop**: If validation fails repeatedly, automation exits gracefully.

---

✅ This keeps it **functional**, not over-engineered. You now have a blueprint that matches your _real flow_ (idea → teaser → blog → final posts) while keeping agentic flexibility (planner, loops, retries, scoring).
