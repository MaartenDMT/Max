import os

import nltk
import numpy as np
import scipy.io.wavfile
from bark import SAMPLE_RATE, generate_audio
from bark.generation import preload_models
from IPython.display import Audio
from transformers import AutoProcessor, BarkModel

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["SUNO_OFFLOAD_CPU"] = "True"
os.environ["SUNO_USE_SMALL_MODELS"] = "True"

# Preload models for Bark
preload_models()
# processor = AutoProcessor.from_pretrained("suno/bark") #suno/bark-small
# model = BarkModel.from_pretrained("suno/bark") #suno/bark-small


# Script to be converted to audio
script = """
Hey, have you heard about this new text-to-audio model called "Bark"? 
Apparently, it's the most realistic and natural-sounding text-to-audio model 
out there right now. People are saying it sounds just like a real person speaking. 
I think it uses advanced machine learning algorithms to analyze and understand the 
nuances of human speech, and then replicates those nuances in its own speech output. 
It's pretty impressive, and I bet it could be used for things like audiobooks or podcasts. 
In fact, I heard that some publishers are already starting to use Bark to create audiobooks. 
It would be like having your own personal voiceover artist. I really think Bark is going to 
be a game-changer in the world of text-to-audio technology.
""".replace(
    "\n", " "
).strip()

# Split the script into sentences
sentences = nltk.sent_tokenize(script)

# Speaker identifier for Bark
SPEAKER = "v2/en_speaker_6"

# Define silence between sentences (quarter second)
silence = np.zeros(int(0.25 * SAMPLE_RATE))

# Generate audio pieces
pieces = []
for sentence in sentences:
    audio_array = generate_audio(sentence, history_prompt=SPEAKER)
    pieces.append(audio_array)
    pieces.append(silence.copy())

# Concatenate all audio pieces
final_audio = np.concatenate(pieces)

# Ensure audio is in int16 format (common for WAV)
final_audio = (final_audio * np.iinfo(np.int16).max).astype(np.int16)

# Play the generated audio
Audio(final_audio, rate=SAMPLE_RATE)

# Save the audio to a WAV file
scipy.io.wavfile.write("bark_out.wav", rate=SAMPLE_RATE, data=final_audio)
