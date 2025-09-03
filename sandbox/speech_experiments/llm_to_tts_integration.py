import asyncio
import sys
import os

# Add the parent directory of ai_tools to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ai_tools.speech.text_to_speech import TTSModel
from ai_experiments.latent_space_activation import ReasoningAgent

async def run_llm_to_tts_integration(query: str):
    """
    Integrates the ReasoningAgent's expert bot with Text-to-Speech.
    Gets a response from the LLM and then speaks it aloud.
    """
    print(f"Querying LLM: {query}")
    
    reasoning_agent = ReasoningAgent()
    tts_model = TTSModel()

    try:
        llm_response = reasoning_agent.expert_bot(query)
        response_text = llm_response.content
        print(f"\nLLM Expert Bot Response: {response_text}")
        print("Speaking LLM response...")
        await tts_model.tts_speak(response_text)
        print("Speech complete.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example usage:
    query = "Tell me a short story about a brave knight and a wise dragon."
    asyncio.run(run_llm_to_tts_integration(query))
