import asyncio
import importlib
import os
import tempfile
import time
from typing import Optional

# Heavy deps are lazy-loaded when needed:
# numpy, sounddevice, torch, whisper, faster_whisper, prompt_toolkit, pynput, scipy
from pydub import AudioSegment

from utils.loggers import LoggerSetup

TO_MINUTE = 60
MAX_SIZE_MB = 400  # Maximum size in MB


class TranscribeFastModel:
    def __init__(
        self,
        model_size: str = "base.en",
        device: Optional[str] = None,
        compute_type: str = "float16",
        sample_rate: int = 44100,
    ) -> None:
        self.model_size = model_size
        # Resolve device lazily to avoid importing torch at module import time
        if device is None:
            try:
                torch = importlib.import_module("torch")
                self.device = "cuda" if getattr(torch, "cuda").is_available() else "cpu"
            except Exception:
                self.device = "cpu"
        else:
            self.device = device
        self.compute_type = compute_type
        self.sample_rate = sample_rate
        # TODO: Investigate using smaller model_size (e.g., "tiny.en", "small.en") for faster inference
        # if acceptable accuracy trade-off.
        # TODO: Experiment with compute_type="int8" or "int8_float16" for further quantization and speed gains.
        self._fw_model = None  # faster-whisper model, created on first use
        self.ctrl_pressed = False
        self._stop_event = asyncio.Event()
        self.is_recording = False
        self.app = None  # prompt_toolkit Application (lazy)

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "TranscribeFastModel", "transcribe_fast_model.log"
        )

        self.logger.info("Transcribe Fast Model initialized with model: %s", model_size)

    def stop(self):
        """Signal to stop recording and shutdown the listener."""
        self.logger.info("Stop signal received.")
        self._stop_event.set()
        if self.app and self.app.is_running:
            self.app.exit()

    async def record_audio(self, timeout: int = 60):
        """Record audio asynchronously."""
        try:
            self.logger.info("Waiting for recording to start.")
            np = importlib.import_module("numpy")
            recording = np.array([], dtype="float64").reshape(0, 2)
            frames_per_buffer = int(self.sample_rate * 0.1)
            start_time = time.time()

            # Wait until recording starts
            while not self.is_recording and not self._stop_event.is_set():
                await asyncio.sleep(0.1)
                if (time.time() - start_time) > timeout:
                    self.logger.warning("Recording timeout waiting for start.")
                    return recording

            # Start capturing audio
            while self.is_recording and not self._stop_event.is_set():
                sd = importlib.import_module("sounddevice")
                chunk = await asyncio.to_thread(
                    sd.rec,
                    frames_per_buffer,
                    samplerate=self.sample_rate,
                    channels=2,
                    dtype="float64",
                )
                await asyncio.to_thread(sd.wait)
                recording = np.vstack([recording, chunk])

            self.logger.info("Recording completed.")
            return recording
        except Exception as e:
            self.logger.error(f"An error occurred during audio recording: {e}")
            return np.array([], dtype="float64").reshape(0, 2)

    async def save_temp_audio(self, recording):
        """Save the recorded audio to a temporary file."""
        try:
            write = importlib.import_module("scipy.io.wavfile").write
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            await asyncio.to_thread(write, temp_file.name, self.sample_rate, recording)
            self.logger.info("Audio saved to temporary file: %s", temp_file.name)
            return temp_file.name
        except Exception as e:
            self.logger.error(f"Error saving audio: {e}")

    def transcribe(self, audio_filepath):
        """Transcribe the audio file using Whisper."""
        try:
            # Check the file size in bytes
            file_size_bytes = os.path.getsize(audio_filepath)
            # Convert to MB
            file_size_mb = file_size_bytes / (1024 * 1024)

            if file_size_mb > MAX_SIZE_MB:
                self.logger.info(
                    f"File size {file_size_mb:.2f} MB exceeds {MAX_SIZE_MB} MB, splitting audio."
                )
                # Split the audio file
                audio_segments = split_audio(audio_filepath)
            else:
                self.logger.info(f"Transcribing audio file: {audio_filepath}")
                audio_segments = [audio_filepath]  # No splitting needed

            full_transcription = ""
            # Load or create faster-whisper model lazily
            if self._fw_model is None:
                WhisperModel = getattr(importlib.import_module("faster_whisper"), "WhisperModel")
                self._fw_model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

            for segment_filepath in audio_segments:
                self.logger.info(f"Transcribing segment: {segment_filepath}")
                segments, info = self._fw_model.transcribe(
                    segment_filepath, beam_size=5, language="en"
                )

                for transcribed_segment in segments:
                    self.logger.info(
                        "[%.2fm -> %.2fm] %s",
                        transcribed_segment.start / TO_MINUTE,
                        transcribed_segment.end / TO_MINUTE,
                        transcribed_segment.text,
                    )
                    full_transcription += transcribed_segment.text + " "
                os.remove(segment_filepath)  # Remove the segment after transcription

            self.logger.info(f"Transcription completed: {full_transcription}")
            return full_transcription
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")

    async def run(self):
        """Run the recording and transcription process."""
        transcription = ""
        try:
            # Lazy import prompt_toolkit
            pt = importlib.import_module("prompt_toolkit")
            Application = getattr(pt, "Application")
            KeyBindings = getattr(pt.key_binding, "KeyBindings")
            kb = KeyBindings()

            @kb.add("c-d")
            def _(event):
                """Toggle recording on Ctrl + b press."""
                self.is_recording = not self.is_recording
                if self.is_recording:
                    self.logger.info("Started recording.")
                else:
                    self.logger.info("Stopped recording.")
                    # Exit the Application when recording stops
                    event.app.exit()

            self.app = Application(key_bindings=kb, full_screen=False)

            # Run the Application and record_audio concurrently
            recording_task = asyncio.create_task(self.record_audio())
            await self.app.run_async()  # This will block until app.exit() is called

            # After the Application exits, await the recording_task
            recording = await recording_task

            if len(recording) == 0:
                self.logger.warning("No audio was captured.")
                return ""

            # Transcribe the recording
            transcription = await asyncio.to_thread(
                self.transcribe, audio_filepath=self.save_temp_audio(recording)
            )
            if transcription:
                return transcription.lower()
            else:
                return ""
        except Exception as e:
            self.logger.error(f"An error occurred in the run method: {e}")
            return ""
        finally:
            if self.app and self.app.is_running:
                self.app.exit()


def split_audio(audio_filepath):
    """Splits the audio file into smaller segments using pydub (synchronous)."""
    audio = AudioSegment.from_file(audio_filepath)
    segment_length = 60 * 60 * 1000  # 60 minutes in milliseconds
    segments = []

    # Use a temporary sibling folder near input file to avoid repo paths in tests
    base_dir = os.path.join(os.path.dirname(audio_filepath), "segments")
    os.makedirs(base_dir, exist_ok=True)

    for start in range(0, len(audio), segment_length):
        end = min(start + segment_length, len(audio))
        segment = audio[start:end]
        time_min = (start // 1000) // 60
        segment_filename = os.path.join(base_dir, f"segment_{time_min}.wav")
        segment.export(segment_filename, format="wav")
        segments.append(segment_filename)

    return segments


class TranscribeSlowModel:
    def __init__(
        self,
        model_size: str = "base.en",
        sample_rate: int = 44100,
        device: Optional[str] = None,
    ) -> None:
        self.model_size = model_size
        self.sample_rate = sample_rate
        if device is None:
            try:
                torch = importlib.import_module("torch")
                self.device = "cuda" if getattr(torch, "cuda").is_available() else "cpu"
            except Exception:
                self.device = "cpu"
        else:
            self.device = device
        self._slow_model = None  # lazy-loaded openai-whisper model
        self.is_recording = False
        self.ctrl_pressed = False  # Track if Ctrl is pressed

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "TranscribeSlowModel", "transcribe_slow_model.log"
        )

        self.logger.info("Transcribe Slow Model initialized with model: %s", model_size)

    def on_press(self, key):
        """Handle key press event."""
        keyboard = importlib.import_module("pynput.keyboard")
        if key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key == keyboard.Key.space and self.ctrl_pressed:
            if not self.is_recording:
                self.is_recording = True
                self.logger.info("Started recording.")

    def on_release(self, key):
        """Handle key release event."""
        keyboard = importlib.import_module("pynput.keyboard")
        if key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key == keyboard.Key.space and self.is_recording:
            self.is_recording = False
            self.logger.info("Stopped recording.")
            return None

    async def record_audio(self):
        """Record audio while the hotkey is pressed."""
        self.logger.info("Waiting for hotkey press to start recording.")
        recording = None
        try:
            np = importlib.import_module("numpy")
            recording = np.array([], dtype="float64").reshape(0, 2)
            frames_per_buffer = int(self.sample_rate * 0.1)

            keyboard = importlib.import_module("pynput.keyboard")
            # Run the listener in a separate thread to avoid blocking the event loop
            listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            listener.start()

            while True:
                if self.is_recording:
                    sd = importlib.import_module("sounddevice")
                    chunk = await asyncio.to_thread(
                        sd.rec,
                        frames_per_buffer,
                        samplerate=self.sample_rate,
                        channels=2,
                        dtype="float64",
                    )
                    await asyncio.to_thread(sd.wait)
                    recording = np.vstack([recording, chunk])
                if not self.is_recording and len(recording) > 0:
                    break
                await asyncio.sleep(0.01) # Small sleep to yield control
            listener.stop()
            listener.join()
            self.logger.info("Recording captured with %d samples.", len(recording))
        except Exception as e:
            self.logger.error("Error in recording audio: %s", e)
        return recording

    def save_temp_audio(self, recording):
        """Save the recorded audio to a temporary file."""
        try:
            write = importlib.import_module("scipy.io.wavfile").write
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            write(temp_file.name, self.sample_rate, recording)
            self.logger.info("Audio saved to temporary file: %s", temp_file.name)
            return temp_file.name
        except Exception as e:
            self.logger.error("Error saving audio: %s", e)

    async def transcribe(self, audio_filepath):
        """Transcribe the given audio file using Whisper."""
        try:
            self.logger.info("Transcribing audio file: %s", audio_filepath)
            if self._slow_model is None:
                whisper = importlib.import_module("whisper")
                self._slow_model = await asyncio.to_thread(whisper.load_model, self.model_size).to(self.device)
            result = await asyncio.to_thread(self._slow_model.transcribe, audio_filepath)
            if (
                isinstance(result, dict)
                and "text" in result
                and isinstance(result["text"], str)
            ):
                query = result["text"].lower()
                self.logger.info("Transcription completed: %s", query)
                return query
            else:
                self.logger.warning(
                    "Transcription result does not contain 'text' or is not a string."
                )
                return ""
        except Exception as e:
            self.logger.error("Error during transcription: %s", e)

    async def run(self):
        """Main loop to handle recording and transcribing."""
        while True:
            recording = await self.record_audio()
            if recording is not None and len(recording) > 0:
                transcription = await self.transcribe(
                    audio_filepath=await self.save_temp_audio(recording)
                )
                if transcription:
                    self.logger.info("Transcription: %s", transcription)
                else:
                    self.logger.warning("Transcription failed.")
            else:
                self.logger.warning("No audio recorded, skipping transcription.")
            print(
                "\nPress Ctrl_R + Space to start the recording again, or press Ctrl+C to stop it.\n"
            )
