# Social Media Content Automation

An intelligent automation system that transforms blog content and Obsidian notes into optimized social media posts for LinkedIn and X (Twitter). Built with LangGraph workflow orchestration and powered by Google's Gemini AI.

## 🚀 Features

### Content Sources

- **Blog Scraping**: Automatically extract and process content from any blog URL
- **Obsidian Integration**: Upload, paste, or link Obsidian markdown notes
- **Combined Processing**: Merge blog content with personal notes for richer context

### AI-Powered Generation

- **LinkedIn Posts**:
  - Monday Teaser (150-200 chars, no links)
  - Thursday Blog Reference (200-300 chars, includes blog URL)
- **X Threads**: Complete 3-part thread structure with hook, starter, and numbered content
- **Custom Prompts**: Inject personalized instructions for tone, style, and focus

### Quality Assurance

- **Content Validation**: Automatic length checks and format validation
- **Peer Review System**: AI-powered quality scoring (1-10 scale) with detailed feedback
- **Content Improvement**: Automated enhancement based on peer review insights
- **Fact Checking**: Flags potentially unsupported claims for manual review

### User Experience

- **Streamlit Web Interface**: Beautiful, intuitive web application
- **Real-time Progress**: Live updates during content generation
- **Interactive Results**: Copy buttons, expandable sections, quality metrics
- **Version Comparison**: Toggle between original and improved content versions

## 🏗️ Architecture

### Workflow Pipeline (LangGraph)

The application uses a sophisticated workflow orchestration system:

```
Blog URL/Obsidian → Scraper → Obsidian Processor → Summarizer → LinkedIn Generator → X Generator → Validator → Peer Reviewer → Content Improver → Results
```

#### Workflow Steps:

1. **Content Scraping**: Extract blog content using intelligent selectors
2. **Obsidian Processing**: Clean and integrate markdown notes
3. **Summarization**: Generate key insights and takeaways
4. **Social Media Generation**: Create platform-specific content
5. **Validation**: Check length, format, and content requirements
6. **Peer Review**: AI analysis with scoring and improvement suggestions
7. **Content Enhancement**: Generate improved versions based on feedback

### Key Components

#### Core Modules

- `main.py`: Streamlit web interface and user interaction
- `workflow.py`: LangGraph workflow orchestration
- `utils.py`: Content scraping, summarization, and data models
- `social_media.py`: Platform-specific content generation and quality assurance
- `obsidian.py`: Markdown processing and note integration

#### Data Models

- `AutomationState`: Complete workflow state management
- `SocialMediaPost`: Rich post objects with metadata, validation, and quality scores

## 🛠️ Technical Stack

- **AI/ML**: Google Gemini 2.5 Flash via LangChain
- **Workflow**: LangGraph for state management and orchestration
- **Web Framework**: Streamlit for interactive UI
- **Content Processing**: BeautifulSoup, requests for web scraping
- **Data Handling**: Python dataclasses, TypedDict for type safety

## 📋 Requirements

### Environment Variables

Create a `.env` file with:

```
GEMINI_API_KEY=your_google_gemini_api_key
```

### Dependencies

- streamlit
- langgraph
- langchain-google-genai
- beautifulsoup4
- requests
- python-dotenv

## 🚀 Getting Started

1. **Setup Environment**:

   ```bash
   pip install -r requirements.txt
   cp .env.example .env  # Add your API keys
   ```

2. **Run Application**:

   ```bash
   streamlit run main.py
   ```

3. **Use the Interface**:
   - **Tab 1**: Enter blog URL for content extraction
   - **Tab 2**: Upload/paste Obsidian notes (optional)
   - **Tab 3**: Add custom AI instructions (optional)
   - Click "Generate Social Media Content"

## 📊 Output Format

### LinkedIn Posts

- **Monday Teaser**: Curiosity-driven post without links (150-200 chars)
- **Thursday Reference**: Value-rich post with blog link (200-300 chars)

### X Threads

- **Hook Tweet**: Attention-grabbing opener (<280 chars)
- **Thread Starter**: Introduction with thread indicator (<280 chars)
- **Numbered Thread**: 6-8 connected tweets with blog URL in final tweet

### Quality Metrics

- Character counts and length validation
- AI peer review scores (1-10)
- Improvement suggestions and enhanced versions
- Validation flags for fact-checking

## 🎯 Content Strategy

### LinkedIn Approach

- Professional tone with engaging hooks
- Monday teasers build anticipation
- Thursday posts drive traffic with clear value propositions
- Industry-relevant hashtags and calls-to-action

### X Thread Strategy

- Conversational, accessible tone
- Strong hooks to maximize engagement
- Numbered format for easy consumption
- Strategic link placement in final tweet

## 🔄 Advanced Features

### Peer Review System

- Automated quality analysis across 6 criteria:
  - Engagement potential
  - Platform-specific best practices
  - Message clarity and flow
  - Educational/entertainment value
  - Call-to-action effectiveness
  - Brand voice consistency

### Content Improvement

- AI-powered enhancement based on peer feedback
- Maintains core message while addressing identified issues
- Preserves strengths while fixing weaknesses
- Version tracking with improvement notes

### Validation & Safety

- Length and format compliance checking
- Unsupported claim detection
- Manual review flagging for quality concerns
- Comprehensive error handling and user feedback

## 🎨 Customization

### Custom Prompts

Tailor content generation with specific instructions:

- **Tone & Style**: "Write in a conversational, friendly tone"
- **Content Focus**: "Focus on practical applications and real-world examples"
- **Format**: "Use bullet points for key takeaways"
- **Audience**: "Target startup founders and entrepreneurs"

### Platform Optimization

- LinkedIn: Professional networking focus with industry insights
- X: Conversational threads with viral potential
- Automatic hashtag generation and engagement optimization
