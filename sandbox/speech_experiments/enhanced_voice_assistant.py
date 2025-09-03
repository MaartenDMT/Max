import asyncio
import sys
import os

# Add the parent directory of ai_tools to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel
from ai_experiments.latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

async def run_enhanced_voice_assistant():
    """
    Runs an enhanced voice-controlled AI assistant for multi-turn conversations.
    Listens for voice input, processes with LLM, and speaks the response.
    """
    print("\nStarting Enhanced Voice Assistant. Say 'goodbye' or 'stop assistant' to end the conversation.")
    print("Press Ctrl+D to start/stop recording for each turn.")
    
    stt_model = TranscribeFastModel()
    tts_model = TTSModel()
    reasoning_agent = ReasoningAgent()

    conversation_history = [] # To maintain context for future enhancements

    try:
        while True:
            print("\nListening for your query...")
            transcribed_text = await stt_model.run()
            
            if not transcribed_text:
                print("No speech detected. Please try again.")
                continue

            print(f"You said: {transcribed_text}")

            if transcribed_text.lower() in ["goodbye", "stop assistant", "exit"]: # Added exit for robustness
                print("Ending conversation. Goodbye!")
                await tts_model.tts_speak("Goodbye!")
                break

            # For now, each turn is a fresh query to the expert_bot.
            # For true multi-turn context, conversation_history would be passed to ReasoningAgent.
            llm_response = reasoning_agent.expert_bot(transcribed_text)
            response_text = llm_response.content
            print(f"Assistant: {response_text}")

            await tts_model.tts_speak(response_text)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stt_model.stop()

if __name__ == "__main__":
    asyncio.run(run_enhanced_voice_assistant())
