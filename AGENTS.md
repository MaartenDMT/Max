# Max Assistant API - Agent Documentation

This document provides comprehensive information about the agent system in Max Assistant API, enabling any agent to understand and work with this codebase effectively.

## Overview

Max Assistant API is a sophisticated multi-agent AI platform built with FastAPI. It provides various AI capabilities through a modular agent system that includes:

1. **Core Agents** - Specialized agents for specific tasks
2. **Orchestrator Agent** - Central coordinator that manages workflows
3. **Enhanced Orchestrator Agent** - Advanced version with memory management
4. **AI Assistant** - Main interface for all AI functionalities
5. **Enhanced AI Assistant** - Advanced version with session management

## Architecture

```
API Layer
├── ai_router.py          # Basic AI endpoints
├── enhanced_ai_router.py  # Enhanced endpoints with memory
└── system_router.py      # System-level endpoints

Assistant Layer
├── ai_assistent.py       # Main AI assistant
└── enhanced_ai_assistant.py  # Enhanced assistant with memory

Agent Layer
├── chatbot_agent.py      # Chatbot processing
├── music_agent.py        # Music generation
├── orchestrator_agent.py # Workflow orchestration
├── enhanced_orchestrator_agent.py # Enhanced orchestration
├── research_agent.py     # Research capabilities
└── video_agent.py        # Video processing

Tool Layer
├── ai_tools/             # Specialized AI tools
├── lc_tools.py           # LangChain tools
└── crew_tools.py         # CrewAI tools
```

## Core Agents

### 1. Video Processing Agent (`agents/video_agent.py`)

Handles YouTube and Rumble video summarization:
- Transcribes video content using speech-to-text
- Generates concise summaries
- Supports both YouTube and Rumble platforms

**Key Methods:**
- `handle_user_input(video_url)` - Process video URL and return summary

### 2. Music Creation Agent (`agents/music_agent.py`)

Generates music loops based on user prompts:
- Creates audio loops with customizable BPM and duration
- Uses AI music generation models
- Outputs audio files in standard formats

**Key Methods:**
- `handle_user_request(prompt, bpm, duration)` - Generate music loop

### 3. Research Agent (`agents/research_agent.py`)

Performs comprehensive research tasks:
- Web research and information gathering
- Text analysis and summarization
- Data processing and insights extraction

**Key Methods:**
- `handle_research(query)` - Research a topic
- `handle_text_summarization(text)` - Summarize text content

### 4. Chatbot Agent (`agents/chatbot_agent.py`)

Processes chat interactions with different modes:
- Critique mode: Analyzes and critiques content
- Reflection mode: Provides reflective analysis

**Key Methods:**
- `process_with_current_mode(mode, summary, full_text)` - Process content in specific mode

### 5. Orchestrator Agent (`agents/orchestrator_agent.py`)

Coordinates workflows between different agents:
- Routes tasks to appropriate agents
- Manages task execution flow
- Combines results from multiple agents

**Key Methods:**
- `run_workflow(query)` - Execute a workflow

## Enhanced Agents

### Enhanced Orchestrator Agent (`agents/enhanced_orchestrator_agent.py`)

Advanced workflow management with memory capabilities:
- LangGraph-based state management
- Conversation memory persistence
- CrewAI collaboration patterns
- Enhanced error handling

**Key Features:**
- Session-based conversation context
- Memory checkpointing
- Multi-agent collaboration using CrewAI

### Enhanced AI Assistant (`assistents/enhanced_ai_assistant.py`)

Main interface with persistent memory:
- Database-backed session management
- Enhanced context awareness
- User preference handling

**Key Methods:**
- `process_query(query, session_id)` - Process query with context
- `start_new_session(user_id)` - Create new conversation session
- `get_session_insights(session_id)` - Retrieve session information

## API Endpoints

### Basic AI Endpoints (`/ai/*`)

All endpoints are POST requests with JSON payloads:

1. **YouTube Video Summarization** - `POST /ai/summarize_youtube`
   - Input: `{ "video_url": "https://youtube.com/watch?v=..." }`
   - Output: Summary and full transcript

2. **Chatbot Processing** - `POST /ai/chatbot`
   - Input: `{ "mode": "critique|reflecting", "summary": "...", "full_text": "..." }`
   - Output: Processed result based on mode

3. **Music Generation** - `POST /ai/music_generation`
   - Input: `{ "prompt": "description", "bpm": 120, "duration": 30 }`
   - Output: Generated music file

4. **Research** - `POST /ai/research`
   - Input: `{ "query": "research topic" }`
   - Output: Research results

5. **Website Summarization** - `POST /ai/summarize_website`
   - Input: `{ "url": "https://example.com", "question": "what is this site about?" }`
   - Output: Website summary and keywords

6. **Website Research** - `POST /ai/website_research`
   - Input: `{ "category": "research_category", "question": "specific question" }`
   - Output: Research results

7. **Writing Tasks** - `POST /ai/writer_task`
   - Input: `{ "task_type": "story|book", "book_description": "...", "num_chapters": 5, "text_content": "..." }`
   - Output: Generated content

### Enhanced AI Endpoints (`/enhanced-ai/*`)

Advanced endpoints with memory and session support:

1. **Session Management** - `POST /enhanced-ai/session/create`
   - Create persistent conversation sessions

2. **Context-Aware Queries** - `POST /enhanced-ai/query`
   - Queries with conversation history and preferences

3. **Session Insights** - `POST /enhanced-ai/session/insights`
   - Retrieve session context and memory

## Integration Guide

### 1. Using the API

To interact with the Max Assistant API:

1. Start the server: `python max.py`
2. Send HTTP POST requests to endpoints with appropriate JSON payloads
3. Handle responses according to the schema in `api/schemas.py`

Example using curl:
```bash
curl -X POST "http://localhost:8000/ai/summarize_youtube" \
     -H "Content-Type: application/json" \
     -d '{"video_url": "https://youtube.com/watch?v=example"}'
```

### 2. Working with Agents Directly

To use agents programmatically:

```python
from assistents.ai_assistent import AIAssistant
from ai_tools.speech.speech_to_text import TranscribeFastModel

# Initialize assistant
assistant = AIAssistant(
    tts_model=None,
    transcribe=TranscribeFastModel(),
    speak=None,
    listen=None
)

# Process a YouTube video
result = await assistant._summarize_youtube_api("https://youtube.com/watch?v=example")
```

### 3. Extending Functionality

To add new capabilities:

1. Create a new agent in `agents/` directory
2. Implement required methods
3. Add corresponding API endpoints in `api/routers/`
4. Update the orchestrator to route to your new agent
5. Add appropriate tools in `ai_tools/`

## Memory Management

The enhanced system provides persistent memory through:

1. **Session-based Context** - Each conversation has a unique session ID
2. **Database Storage** - SQLite database stores conversation history
3. **User Preferences** - Customizable settings per session
4. **Agent Memory** - Persistent storage for agent-specific data

## Configuration

Key configuration options in `.env`:

- `MAX_LLM_PROVIDER` - AI model provider (ollama, openai, anthropic)
- `MAX_OLLAMA_BASE_URL` - Ollama server URL
- `MAX_OLLAMA_MODEL` - Ollama model name
- `MAX_RATE_LIMIT_ENABLED` - Enable API rate limiting
- `MAX_DEBUG` - Enable debug logging

## Development Guidelines

1. **Agent Design**:
   - Follow single responsibility principle
   - Implement async methods for I/O operations
   - Handle errors gracefully with meaningful messages
   - Use lazy loading for heavy dependencies

2. **API Development**:
   - Define schemas in `api/schemas.py`
   - Add endpoints to appropriate router files
   - Follow REST conventions
   - Implement proper error handling

3. **Memory Management**:
   - Use session IDs for context persistence
   - Clean up old sessions periodically
   - Store only necessary information
   - Implement proper data serialization

4. **Testing**:
   - Write unit tests for each agent
   - Test API endpoints with various inputs
   - Verify error handling scenarios
   - Check memory persistence functionality

## Tools and Technologies

- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **CrewAI** - Multi-agent collaboration
- **LangGraph** - State management
- **SQLite** - Database storage
- **Pydantic** - Data validation
- **Ollama** - Local LLM inference

## Troubleshooting

Common issues and solutions:

1. **Model Loading Errors**:
   - Ensure LLM provider is properly configured
   - Check model availability on the provider
   - Verify network connectivity

2. **Memory Issues**:
   - Check database file permissions
   - Monitor session count and clean up old sessions
   - Adjust memory limits in configuration

3. **API Errors**:
   - Validate request payloads against schemas
   - Check server logs for detailed error information
   - Ensure dependencies are properly installed

This documentation should provide any agent with the necessary information to understand, interact with, and extend the Max Assistant API system.