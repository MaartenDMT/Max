import asyncio
import sys
import os

# Add the parent directory of ai_tools to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_experiments.latent_space_activation import ReasoningAgent

async def run_stt_to_llm_integration():
    """
    Integrates Speech-to-Text with the ReasoningAgent's expert bot.
    Records audio, transcribes it, and feeds the text to the LLM.
    """
    print("Starting STT to LLM Integration. Press Ctrl+D to start/stop recording.")
    
    stt_model = TranscribeFastModel()
    reasoning_agent = ReasoningAgent()

    try:
        transcribed_text = await stt_model.run()
        if transcribed_text:
            print(f"\nTranscribed Text: {transcribed_text}")
            print("Feeding transcribed text to the Expert Bot...")
            llm_response = reasoning_agent.expert_bot(transcribed_text)
            print(f"\nLLM Expert Bot Response: {llm_response.content}")
        else:
            print("No speech detected or transcribed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the STT model is stopped if it's still running
        stt_model.stop()

if __name__ == "__main__":
    asyncio.run(run_stt_to_llm_integration())
