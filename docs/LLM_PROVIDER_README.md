# Enhanced LLM Provider Management System

This enhanced version of the Max AI Assistant now supports multiple LLM providers with dynamic switching capabilities. You can seamlessly switch between OpenAI, Anthropic, Google Gemini, OpenRouter, and local Ollama models.

## 🚀 Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, OpenRouter, Ollama
- **Dynamic Provider Switching**: Change providers and models at runtime
- **API Key Management**: Centralized environment variable configuration
- **Session Memory**: Maintains conversation context across provider switches
- **RESTful API**: Full API endpoints for provider management
- **Validation System**: Automatic API key and provider validation
- **Fallback Handling**: Graceful degradation when providers are unavailable

## 📋 Supported Providers and Models

### OpenAI
- gpt-4o
- gpt-4o-mini
- gpt-3.5-turbo

### Anthropic
- claude-3-5-sonnet-20241022
- claude-3-opus-20240229
- claude-3-haiku-20240307

### Google Gemini
- gemini-1.5-pro
- gemini-1.5-flash

### OpenRouter
- Multiple models through OpenRouter gateway

### Ollama (Local)
- Any locally installed Ollama models

## 🔧 Setup

### 1. Environment Variables

Create a `.env` file in your project root with your API keys:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# OpenRouter (optional)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Other services
SERPAPI_KEY=your_serpapi_key_here
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv add langchain langchain-openai langchain-anthropic langchain-google-genai langchain-ollama

# Using pip
pip install langchain langchain-openai langchain-anthropic langchain-google-genai langchain-ollama
```

### 3. Ollama Setup (Optional)

For local models, install Ollama:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2
```

## 🛠️ Usage

### Direct Python Usage

```python
from assistents.enhanced_ai_assistant import EnhancedAIAssistant

# Initialize assistant
assistant = EnhancedAIAssistant()

# Get current provider info
info = assistant.get_llm_info()
print(f"Current: {info['current_provider']}/{info['current_model']}")

# Switch provider
result = assistant.change_llm_provider("anthropic", "claude-3-5-sonnet-20241022")
if result['status'] == 'success':
    print("Successfully switched to Anthropic!")

# Query with new provider
response = await assistant.query("Hello! Which model are you?")
print(response['response'])
```

### API Usage

Start the API server:

```bash
uvicorn api.main_api:app --reload
```

#### Get LLM Information

```bash
curl http://localhost:8000/enhanced-ai/llm/info
```

#### Change Provider

```bash
curl -X POST http://localhost:8000/enhanced-ai/llm/change \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7
  }'
```

#### Get Available Providers

```bash
curl http://localhost:8000/enhanced-ai/llm/providers
```

#### Validate Setup

```bash
curl http://localhost:8000/enhanced-ai/llm/validate
```

## 📚 API Endpoints

### LLM Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/enhanced-ai/llm/info` | GET | Get current LLM provider information |
| `/enhanced-ai/llm/change` | POST | Change LLM provider and model |
| `/enhanced-ai/llm/providers` | GET | Get all available providers |
| `/enhanced-ai/llm/providers/{provider}/models` | GET | Get models for specific provider |
| `/enhanced-ai/llm/validate` | GET | Validate LLM setup and API keys |
| `/enhanced-ai/llm/test` | GET | Test current LLM provider |

### Enhanced Query Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/enhanced-ai/query` | POST | Send query with session memory |
| `/enhanced-ai/query/stream` | POST | Stream query response |

## 🔄 Provider Switching Examples

### Switching for Different Tasks

```python
# Use GPT-4 for complex reasoning
assistant.change_llm_provider("openai", "gpt-4o")
analysis = await assistant.query("Analyze this complex dataset...")

# Switch to Claude for creative writing
assistant.change_llm_provider("anthropic", "claude-3-5-sonnet-20241022")
story = await assistant.query("Write a creative story about...")

# Use Gemini for factual information
assistant.change_llm_provider("gemini", "gemini-1.5-flash")
facts = await assistant.query("What are the latest facts about...")
```

### Cost Optimization

```python
# Use cheaper models for simple tasks
assistant.change_llm_provider("openai", "gpt-3.5-turbo")
simple_response = await assistant.query("What is 2+2?")

# Use premium models for complex tasks
assistant.change_llm_provider("openai", "gpt-4o")
complex_response = await assistant.query("Explain quantum computing...")
```

## 🔍 Validation and Error Handling

The system includes comprehensive validation:

```python
# Validate all providers
validation = assistant.validate_llm_setup()
for provider, status in validation.items():
    if status['valid']:
        print(f"✅ {provider}: Ready")
    else:
        print(f"❌ {provider}: {status['message']}")

# Check available models
models = assistant.get_available_models("openai")
print(f"OpenAI models: {models}")

# Safe provider switching with error handling
result = assistant.change_llm_provider("invalid_provider", "invalid_model")
if result['status'] == 'error':
    print(f"Switch failed: {result['message']}")
```

## 🧠 Memory and Session Management

The enhanced system maintains conversation context across provider switches:

```python
# Start conversation with OpenAI
assistant.change_llm_provider("openai", "gpt-4o-mini")
response1 = await assistant.query("My name is Alice.")

# Switch to Claude - memory is preserved
assistant.change_llm_provider("anthropic", "claude-3-5-sonnet-20241022")
response2 = await assistant.query("What's my name?")
# Claude will remember: "Your name is Alice."
```

## 📊 Monitoring and Logging

All provider activities are logged:

```python
# Check logs for provider activities
import logging
logger = logging.getLogger("enhanced_ai_assistant")
logger.info("Provider switched to OpenAI/GPT-4")
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `.env` file is in project root
   - Check environment variable names match exactly
   - Restart application after adding new keys

2. **Provider Not Available**
   - Verify API key is valid
   - Check internet connection
   - Ensure service is not experiencing outages

3. **Model Not Found**
   - Check model name spelling
   - Verify model is available for your API tier
   - Use `get_available_models()` to see supported models

4. **Ollama Connection Issues**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are installed: `ollama list`
   - Verify Ollama is accessible on localhost:11434

### Debug Commands

```python
# Check provider status
info = assistant.get_llm_info()
print(f"Current provider: {info}")

# Validate setup
validation = assistant.validate_llm_setup()
print(f"Validation results: {validation}")

# Test connection
test_result = await assistant.test_current_provider()
print(f"Test result: {test_result}")
```

## 🧪 Running Examples

We've included demonstration scripts:

### Direct Python Demo
```bash
python examples/llm_provider_demo.py
```

### API Demo
```bash
# Start API server first
uvicorn api.main_api:app --reload

# In another terminal
python examples/api_demo.py
```

## 🔮 Advanced Usage

### Custom Provider Configuration

```python
from utils.llm_manager import LLMProviderManager

# Create custom manager with specific settings
manager = LLMProviderManager(
    default_provider="anthropic",
    default_model="claude-3-5-sonnet-20241022",
    default_temperature=0.5
)

# Use with assistant
assistant = EnhancedAIAssistant(llm_manager=manager)
```

### Provider-Specific Settings

```python
# Configure different temperatures per provider
openai_config = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.3  # Conservative for analysis
}

anthropic_config = {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.8  # Creative for writing
}
```

## 📝 Contributing

To add new providers:

1. Add provider configuration to `utils/llm_manager.py`
2. Add environment variable for API key
3. Implement provider-specific LangChain integration
4. Add provider to validation system
5. Update documentation

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**Happy AI Chatting with Multiple Providers! 🤖✨**
