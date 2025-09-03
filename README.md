# Max Assistant API

A powerful FastAPI-based multi-agent AI assistant platform with tools for research, video summarization, website summarization, writing, music generation, and more.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-orange)

## Features

- **Video Summarization**: Summarize YouTube videos with AI analysis
- **Website Research**: Extract key information from websites
- **AI Writing**: Generate content with different writing styles
- **Music Generation**: Create music loops with customizable parameters
- **Chatbot**: Process content with different LLM modes (critique, reflection)
- **Research**: Perform AI-powered research on topics
- **Optimized Performance**: Asynchronous processing with lazy-loading of models

## System Requirements

- **Python**: 3.11 (required)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 2GB minimum for application and dependencies
- **CUDA**: Optional but recommended for GPU acceleration
  - CUDA 12.x compatible with PyTorch 2.6
  - 8GB+ VRAM for optimal performance

## Quick Start Guide

### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager and installer.

```powershell
# Install uv (Windows)
Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression

# Create and activate virtual environment
uv venv
.\.venv\Scripts\Activate.ps1

# Install dependencies from pyproject.toml
uv sync

# Run the application
python max.py
```

Base URL: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Option 2: Using Conda

```bash
# Create environment from yml file
conda env create -f conda-env.yml

# Activate the environment
conda activate max

# Run the application
python max.py
```

### Option 3: Using venv + pip

```powershell
# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.\.venv\Scripts\Activate.ps1
# Activate environment (Linux/Mac)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python max.py
```

## Configuration

Max Assistant API uses environment variables for configuration. Copy `.env.example` to `.env` and customize settings:

```bash
cp .env.example .env
```

Key configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| UVICORN_HOST | Host to bind the server | 0.0.0.0 |
| UVICORN_PORT | Port to run the server | 8000 |
| LLM_PROVIDER | AI provider (ollama, openai, anthropic) | ollama |
| OLLAMA_BASE_URL | URL for local Ollama instance | http://localhost:11434 |
| OLLAMA_MODEL | Ollama model to use | llama3.1 |
| RATE_LIMIT_ENABLED | Enable rate limiting | false |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /ai/summarize_youtube | POST | Summarize a YouTube video |
| /ai/chatbot | POST | Process content with LLM modes |
| /ai/music_generation | POST | Generate music loops |
| /ai/research | POST | Perform AI research |
| /ai/summarize_website | POST | Summarize website content |
| /ai/website_research | POST | Research across websites |
| /ai/writer_task | POST | Generate written content |

Full API documentation is available at `/docs` when the server is running.

## Troubleshooting

- **Logs**: Check `data/logs/` for detailed logs with automatic rotation
- **Health Check**: Visit `/health` endpoint to verify API status
- **Memory Issues**: Adjust `AI_MEMORY_LIMIT` in `.env` file
- **Performance**: The application uses async operations and lazy loading to optimize performance

## Database migrations (Alembic + SQLite)

This project uses Alembic for schema migrations. On SQLite, ALTER TABLE operations are limited; we enable batch mode to make changes safely and apply consistent naming conventions for constraints and indexes.

- Naming conventions are configured on SQLAlchemy `Base.metadata` and in `alembic/env.py` so constraint names are deterministic across DBs.
- For SQLite, Alembic is configured to use `render_as_batch=True` automatically.

Typical workflow:

```powershell
# Create a new revision with autogenerate
alembic revision -m "your message" --autogenerate

# Apply migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1
```

If you add or modify models under `api/models.py` or `utils/database.py`, run a new autogenerate and review the script to ensure it matches the intended changes.

## Architecture

- **FastAPI**: Modern, high-performance web framework
- **Pydantic**: Data validation and settings management
- **Langchain/Ollama**: AI model orchestration
- **Asynchronous Processing**: Async-safe tools with thread offloading for heavy operations

## LangChain 0.3+ import conventions

This repo uses the split-package layout introduced in LangChain 0.3+. Common imports you will see:

- Core prompts, messages, runnables: `from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder`
- Text splitters: `from langchain_text_splitters import RecursiveCharacterTextSplitter`
- Providers (examples):
  - OpenAI: `from langchain_openai import ChatOpenAI`
  - Ollama: `from langchain_ollama import ChatOllama, OllamaEmbeddings`
  - Anthropic: `from langchain_anthropic import ChatAnthropic`
  - Google: `from langchain_google_genai import ChatGoogleGenerativeAI`
- Community loaders/vectorstores/tools: `from langchain_community.document_loaders import ...`, `from langchain_community.vectorstores import ...`

Legacy imports like `from langchain.text_splitter` or `from langchain.llms` should be avoided. Prefer the split packages above.

### LCEL Patterns Used

This codebase adopts LangChain Expression Language (LCEL) for composing chains, which provides better type safety, streaming, and debugging compared to legacy chain classes.

**Summarization Pattern**:

```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

chain = PromptTemplate.from_template("Summarize: {context}") | llm | StrOutputParser()
result = chain.invoke({"context": "some text"})
```

**RAG (Retrieval-Augmented Generation) Pattern**:

```python
from operator import itemgetter
from langchain_core.runnables import RunnableLambda

# Compose retriever and answer chains
rewrite_chain = {"input": itemgetter("input"), "chat_history": itemgetter("chat_history")} | retriever_prompt | llm | StrOutputParser()
docs_chain = rewrite_chain | retriever
format_docs = RunnableLambda(lambda docs: "\n\n".join(doc.page_content for doc in docs))
final_chain = {"context": docs_chain | format_docs, "input": itemgetter("input"), "chat_history": itemgetter("chat_history")} | answer_prompt | llm | StrOutputParser()

result = final_chain.invoke({"input": "query", "chat_history": []})
```

These patterns ensure chains are composable, async-friendly, and compatible with modern LangChain features.

## Contributing

Contributions welcome! Please see our [contribution guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
