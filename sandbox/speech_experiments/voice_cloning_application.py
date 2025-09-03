import asyncio
import sys
import os
import torch
from TTS.api import TTS

# Add the parent directory of ai_tools to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ai_experiments.latent_space_activation import ReasoningAgent

async def run_voice_cloning_application(query: str, speaker_wav_path: str):
    """
    Demonstrates voice cloning by generating LLM response in a cloned voice.
    Requires a speaker_wav_path to an audio file of the voice to be cloned.
    """
    if not os.path.exists(speaker_wav_path):
        print(f"Error: Speaker WAV file not found at {speaker_wav_path}")
        print("Please provide a valid path to an audio file for voice cloning.")
        return

    print(f"Querying LLM: {query}")
    
    reasoning_agent = ReasoningAgent()
    
    # Get device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Init TTS with a multi-lingual voice cloning model
    # Using the same model as in coqui_cloning.py for consistency
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    try:
        llm_response = reasoning_agent.expert_bot(query)
        response_text = llm_response.content
        print(f"\nLLM Expert Bot Response: {response_text}")
        print(f"Generating speech in cloned voice from {speaker_wav_path}...")
        
        output_audio_path = "data/audio/cloned_llm_response.wav"
        
        # Generate speech with voice cloning
        tts.tts_to_file(
            text=response_text,
            speaker_wav=speaker_wav_path,
            language="en", # Assuming English, can be made dynamic if needed
            file_path=output_audio_path,
            speed=1.0,
        )
        print(f"Cloned speech saved to {output_audio_path}")
        print("Voice cloning application complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example usage:
    # IMPORTANT: Replace 'path/to/your/speaker.wav' with an actual path to an audio file
    # of the voice you want to clone.
    example_speaker_wav = "data/speaker/kanye.wav" # Placeholder, replace with a real file
    query = "Can you explain the concept of artificial neural networks?"
    asyncio.run(run_voice_cloning_application(query, example_speaker_wav))