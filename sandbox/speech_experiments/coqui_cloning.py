import torch
from TTS.api import TTS

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
print(TTS().list_models())

# Init TTS
tts = TTS("tts_models/eng/fairseq/vits").to(device)
text = """
Once upon a time, there was a young girl named Lily who lived in a small village. 
She loved to play with her friends and explore the woods around them. 
One day, she stumbled upon a hidden cave that had never been seen before. 
As she explored deeper into the cave, she found a strange creature inside. It was a giant octopus, and it was afraid of her. 
Lily tried to scare it away but it wouldn't budge. 
She decided to take matters into her own hands and used her magic wand to create a powerful barrier around the creature. 
The octopus finally gave up its power and allowed Lily to explore the cave with her friends. 
From that day on, Lily became known as the brave girl who could scare any monster in the woods.
"""
# Run TTS
# ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
# Text to speech list of amplitude values as output
# wav = tts.tts(text="Hello world!", speaker_wav="data/speaker/kanye.wav", language="en")
# Text to speech to a file
tts.tts_to_file(
    text=text,
    # speaker_wav="data/speaker/kanye.wav",
    language="en",
    file_path="data/audio/coqui.wav",
    speed=1.3,
)
