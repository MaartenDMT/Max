import asyncio
import importlib
import os

import pyttsx3
from pydub import AudioSegment
from pydub.playback import play

from utils.loggers import LoggerSetup

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class TTSModel:
    def __init__(self, good_model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        # Good Model (TTS)
        # TODO: Investigate Coqui TTS documentation for options to quantize xtts_v2
        # or use smaller, faster models if available and suitable for desired quality.
        # Resolve device lazily to avoid hard torch import at module import time
        try:
            torch = importlib.import_module("torch")
            self.device = (
                "cuda"
                if getattr(torch, "cuda", None) is not None and torch.cuda.is_available()
                else "cpu"
            )
        except Exception:
            self.device = "cpu"
        self.tts = None  # Coqui TTS model instance (lazy)
        self._good_model_name = good_model_name
        self.default_speaker = "Ana Florence"
        self.default_language = "en"
        self.temp_audio = "data/audio/temp_audio.wav"

        # Bad Model (pyttsx3)
        self.bad_tts_engine = pyttsx3.init()
        self.bad_tts_engine.setProperty("rate", 150)  # Default speaking rate
        self.bad_tts_engine.setProperty("volume", 1.0)  # Max volume

        # Default preference to good model; we'll try to init it on first use
        self.use_good_model = True

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("TTSModelLogger", "tts_model_logger.log")

        # Log initialization
        self.logger.info("TTS Model initialized.")

    def _try_allowlist_qualified(self, qualified: str) -> bool:
        """Allowlist a fully qualified class/function name for torch safe deserialization.
        Example: 'TTS.config.shared_configs.BaseDatasetConfig'
        """
        try:
            torch = importlib.import_module("torch")
            serialization = getattr(torch, "serialization", None)
            if not (serialization and hasattr(serialization, "add_safe_globals")):
                return False
            mod_name, cls_name = qualified.rsplit(".", 1)
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            serialization.add_safe_globals([cls])
            self.logger.debug("Allowlisted safe global: %s", qualified)
            return True
        except Exception as e:
            self.logger.debug("Failed to allowlist %s: %s", qualified, e)
            return False

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
            if not self.tts:
                # Try to lazy-load Coqui TTS only now
                try:  # pragma: no cover - optional dependency
                    tts_api = importlib.import_module("TTS.api")
                    TTSClass = getattr(tts_api, "TTS")
                    # PyTorch 2.6+ defaults to weights_only=True which breaks legacy checkpoints
                    # Allowlist Coqui's XTTS configs for safe deserialization when trusted.
                    try:
                        torch = importlib.import_module("torch")
                        serialization = getattr(torch, "serialization", None)
                        if serialization and hasattr(serialization, "add_safe_globals"):
                            xtts_cfg_mod = importlib.import_module(
                                "TTS.tts.configs.xtts_config"
                            )
                            XttsConfig = getattr(xtts_cfg_mod, "XttsConfig")
                            xtts_model_mod = importlib.import_module(
                                "TTS.tts.models.xtts"
                            )
                            XttsAudioConfig = getattr(xtts_model_mod, "XttsAudioConfig")
                            # Also frequently required shared config types
                            try:
                                shared_cfg_mod = importlib.import_module(
                                    "TTS.config.shared_configs"
                                )
                                BaseDatasetConfig = getattr(shared_cfg_mod, "BaseDatasetConfig")
                                serialization.add_safe_globals([
                                    XttsConfig,
                                    XttsAudioConfig,
                                    BaseDatasetConfig,
                                ])
                            except Exception:
                                serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
                    except Exception as e:
                        # Best-effort; will fallback to pyttsx3 on failure
                        self.logger.debug("Safe globals setup failed: %s", e)
                    # Attempt model init with up to 3 dynamic allowlisting retries
                    last_err = None
                    for _ in range(3):
                        try:
                            self.tts = TTSClass(self._good_model_name).to(self.device)
                            break
                        except Exception as ie:
                            last_err = ie
                            msg = str(ie)
                            # Parse "Unsupported global: GLOBAL package.path.ClassName"
                            marker = "Unsupported global: GLOBAL "
                            if marker in msg:
                                start = msg.find(marker) + len(marker)
                                end = msg.find(" ", start)
                                if end == -1:
                                    end = len(msg)
                                qualified = msg[start:end].strip()
                                if not self._try_allowlist_qualified(qualified):
                                    break
                                else:
                                    continue
                            else:
                                break
                    else:
                        # Exhausted retries
                        raise last_err
                except Exception as e:
                    # Fallback if unavailable
                    self.logger.warning(f"Coqui TTS unavailable, falling back: {e}")
                    await self._speak_bad_model(text)
                    return
            self.logger.info(f"Generating speech using TTS model for text: {text}")
            # TODO: Explore if Coqui TTS supports streaming output to reduce latency,
            # and refactor this method to use a streaming approach if possible.
            await asyncio.to_thread(
                self.tts.tts_to_file,
                text=text,
                speaker=self.default_speaker,
                language=self.default_language,
                file_path=path,
                split_sentences=True,
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
