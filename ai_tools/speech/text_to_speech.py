import asyncio
import os

import pyttsx3
from pydub import AudioSegment
from pydub.playback import play
from torch import cuda
from TTS.api import TTS

from utils.loggers import LoggerSetup

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class TTSModel:
    def __init__(self, good_model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        # Good Model (TTS)
        # TODO: Investigate Coqui TTS documentation for options to quantize xtts_v2
        # or use smaller, faster models if available and suitable for desired quality.
        self.device = "cuda" if cuda.is_available() else "cpu"
        self.tts = TTS(good_model_name).to(self.device)
        self.default_speaker = "Ana Florence"
        self.default_language = "en"
        self.temp_audio = "data/audio/temp_audio.wav"

        # Bad Model (pyttsx3)
        self.bad_tts_engine = pyttsx3.init()
        self.bad_tts_engine.setProperty("rate", 150)  # Default speaking rate
        self.bad_tts_engine.setProperty("volume", 1.0)  # Max volume

        # Default to good model (TTS)
        self.use_good_model = True

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("TTSModelLogger", "tts_model_logger.log")

        # Log initialization
        self.logger.info("TTS Model initialized.")

    def set_good_model(self):
        """Switch to the good model (TTS)."""
        self.use_good_model = True
        self.logger.info("Switched to the good model (TTS).")

    def set_bad_model(self):
        """Switch to the bad model (pyttsx3)."""
        self.use_good_model = False
        self.logger.info("Switched to the bad model (pyttsx3).")

    async def tts_speak(self, text="This is a text to speech bot", path=None):
        """Generate and play speech from text based on the selected model."""
        try:
            if self.use_good_model:
                self.logger.info(f"Using good model (TTS) to speak: {text}")
                await self._speak_good_model(text, path)
            else:
                self.logger.info(f"Using bad model (pyttsx3) to speak: {text}")
                await self._speak_bad_model(text)
        except Exception as e:
            self.logger.error(f"Error in tts_speak: {e}")

    async def _speak_good_model(self, text, path=None):
        """Generate speech using the good model (TTS) and play it asynchronously."""
        if path is None:
            path = self.temp_audio
        try:
            self.logger.info(f"Generating speech using TTS model for text: {text}")
            # TODO: Explore if Coqui TTS supports streaming output to reduce latency,
            # and refactor this method to use a streaming approach if possible.
            await asyncio.to_thread(
                self.tts.tts_to_file,
                text,  # The first argument (text)
                self.default_speaker,  # The second argument (speaker)
                self.default_language,  # The third argument (language)
                None,  # speaker_wav (None by default)
                None,  # emotion (None by default)
                1,  # speed (default 1)
                None,  # pipe_out (None by default)
                path,  # file_path (output file path)
                True,  # split_sentences (default True)
            )
            await self._play_audio(path)
            self.logger.info(f"Speech generated and played for text: {text}")
        except Exception as e:
            self.logger.error(f"Error in _speak_good_model: {e}")

    async def _speak_bad_model(self, text):
        """Generate speech using the bad model (pyttsx3) asynchronously."""
        try:
            self.logger.info(f"Speaking using pyttsx3 for text: {text}")
            await asyncio.to_thread(self._run_pyttsx3, text)
            self.logger.info(f"Speech completed for text: {text}")
        except Exception as e:
            self.logger.error(f"Error in _speak_bad_model: {e}")

    def _run_pyttsx3(self, text):
        """Blocking pyttsx3 call."""
        self.bad_tts_engine.say(text)
        self.bad_tts_engine.runAndWait()

    async def _play_audio(self, path=None):
        """Play the generated audio from a file asynchronously."""
        if path is None:
            path = self.temp_audio
        try:
            self.logger.info(f"Playing audio file: {path}")
            await asyncio.to_thread(self._play_audio_file, path)
            self.logger.info(f"Audio playback finished for file: {path}")
        except Exception as e:
            self.logger.error(f"Error in play_audio: {e}")
        finally:
            if os.path.exists(path):
                os.remove(path)
                self.logger.info(f"Temporary audio file deleted: {path}")

    def _play_audio_file(self, path):
        """Blocking function to play audio file."""
        sound = AudioSegment.from_wav(path)
        play(sound)
