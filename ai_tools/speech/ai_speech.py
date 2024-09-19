import os
import warnings

import nltk  # we'll use this to split into sentences
import numpy as np
import scipy
from bark import SAMPLE_RATE, generate_audio
from bark.generation import preload_models
from dotenv import find_dotenv, load_dotenv
from IPython.display import Audio

warnings.simplefilter(action="ignore", category=FutureWarning)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

load_dotenv(find_dotenv(".env"))

preload_models()

# Read the text file properly using the 'open' function
with open(
    r"data/text/Sauron vs Morgoth  Who Was More Evil Differences and Similarities Explained_full.txt",
    "r",
    encoding="utf-8",
) as file:
    script = file.read()

# script = """
# Hey, have you heard about this new text-to-audio model called "Bark"?
# Apparently, it's the most realistic and natural-sounding text-to-audio model
# out there right now. People are saying it sounds just like a real person speaking.
# I think it uses advanced machine learning algorithms to analyze and understand the
# nuances of human speech, and then replicates those nuances in its own speech output.
# It's pretty impressive, and I bet it could be used for things like audiobooks or podcasts.
# In fact, I heard that some publishers are already starting to use Bark to create audiobooks.
# It would be like having your own personal voiceover artist. I really think Bark is going to
# be a game-changer in the world of text-to-audio technology.
# """.replace(
#     "\n", " "
# ).strip()


sentences = nltk.sent_tokenize(script)

SPEAKER = "v2/en_speaker_6"
silence = np.zeros(int(0.25 * SAMPLE_RATE))  # quarter second of silence

pieces = []
for sentence in sentences:
    audio_array = generate_audio(sentence, history_prompt=SPEAKER)
    pieces += [audio_array, silence.copy()]
Audio(np.concatenate(pieces), rate=SAMPLE_RATE)
scipy.io.wavfile.write(
    "data/audio/bark_out.wav", rate=SAMPLE_RATE, data=np.concatenate(pieces)
)
