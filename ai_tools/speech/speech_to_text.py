import os
import tempfile
import threading
import time

import numpy as np
import sounddevice as sd
import whisper
from faster_whisper import WhisperModel
from pynput import keyboard
from scipy.io.wavfile import write
from torch import cuda
from queue import Queue

from utils.loggers import LoggerSetup


class TranscribeFastModel:
    def __init__(
        self,
        model_size="base.en",
        device="cuda" if cuda.is_available() else "cpu",
        compute_type="float16",
        sample_rate=44100,
    ):
        self.model_size = model_size
        self.sample_rate = sample_rate
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.is_recording = False
        self.ctrl_pressed = False
        self._stop_event = threading.Event()

        # Queue to handle start/stop recording signals
        self.record_queue = Queue()

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "TranscribeFastModel", "transcribe_fast_model.log"
        )

        self.logger.info("Transcribe Fast Model initialized with model: %s", model_size)

        # Start the keyboard listener in a non-blocking manner
        self.listener_thread = threading.Thread(target=self.start_keyboard_listener)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def stop(self):
        """Signal to stop recording and shutdown the listener."""
        self.logger.info("Stop signal received.")
        self._stop_event.set()

    def on_press(self, key):
        """Handle key press event."""
        try:
            if key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            if (
                key == keyboard.Key.space
                and self.ctrl_pressed
                and not self.is_recording
            ):
                self.is_recording = True
                self.logger.info("Started recording.")
                self.record_queue.put(True)  # Signal to start recording
        except Exception as e:
            self.logger.error(f"Error in on_press: {e}")

    def on_release(self, key):
        """Handle key release event."""
        try:
            if key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False

            if key == keyboard.Key.space and self.is_recording:
                self.is_recording = False
                self.logger.info("Stopped recording.")
                self.record_queue.put(False)  # Signal to stop recording
                return False  # Stop listener when recording is finished
        except Exception as e:
            self.logger.error(f"Error in on_release: {e}")

    def start_keyboard_listener(self):
        """Start the keyboard listener in a non-blocking manner."""
        self.logger.info("Keyboard listener started.")
        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()

    def record_audio(self, timeout=60):
        """Record audio while the hotkey (CTRL + SPACE) is pressed, with a timeout."""
        try:
            self.logger.info("Waiting for recording to start.")
            recording = np.array([], dtype="float64").reshape(0, 2)
            frames_per_buffer = int(self.sample_rate * 0.1)
            start_time = time.time()

            while (
                not self._stop_event.is_set() and (time.time() - start_time) < timeout
            ):
                if not self.record_queue.empty():
                    should_record = self.record_queue.get()

                    if should_record:
                        # Start capturing audio
                        while self.is_recording and not self._stop_event.is_set():
                            chunk = sd.rec(
                                frames_per_buffer,
                                samplerate=self.sample_rate,
                                channels=2,
                                dtype="float64",
                            )
                            sd.wait()
                            recording = np.vstack([recording, chunk])
                        break

            if len(recording) > 0:
                self.logger.info("Recording captured with %d samples.", len(recording))
                return recording
            else:
                self.logger.warning("No audio was captured.")
                return np.array([], dtype="float64").reshape(0, 2)
        except Exception as e:
            self.logger.error(f"An error occurred during audio recording: {e}")

    def save_temp_audio(self, recording):
        """Save the recorded audio to a temporary file."""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            write(temp_file.name, self.sample_rate, recording)
            self.logger.info(f"Audio saved to temporary file: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            self.logger.error(f"Error saving audio: {e}")

    def transcribe(self, audio_filepath):
        """Transcribe the audio file using Whisper."""
        try:
            self.logger.info(f"Transcribing audio file: {audio_filepath}")
            segments, info = self.model.transcribe(
                audio_filepath, beam_size=5, language="en"
            )
            full_transcription = ""
            for segment in segments:
                self.logger.info(
                    "[%.2fs -> %.2fs] %s", segment.start, segment.end, segment.text
                )
                full_transcription += segment.text + " "
            os.remove(audio_filepath)
            self.logger.info(f"Transcription completed: {full_transcription}")
            return full_transcription
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")

    def run(self):
        """Run the recording and transcription process."""
        try:
            self.logger.info("Starting recording and transcription process.")
            self._stop_event.clear()
            recording = self.record_audio()

            if len(recording) == 0:
                self.logger.warning("No audio was captured.")
                return ""

            transcription = self.transcribe(
                audio_filepath=self.save_temp_audio(recording)
            )
            return transcription.lower()
        except Exception as e:
            self.logger.error(f"An error occurred in the run method: {e}")
            return ""


class TranscribeSlowModel:
    def __init__(
        self,
        model_size="base.en",
        sample_rate=44100,
        device="cuda" if cuda.is_available() else "cpu",
    ):
        self.model_size = model_size
        self.sample_rate = sample_rate
        self.device = device
        self.model = whisper.load_model(model_size).to(device)
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
        if key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = True
        if key == keyboard.Key.space and self.ctrl_pressed:
            if not self.is_recording:
                self.is_recording = True
                self.logger.info("Started recording.")

    def on_release(self, key):
        """Handle key release event."""
        if key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key == keyboard.Key.space and self.is_recording:
            self.is_recording = False
            self.logger.info("Stopped recording.")
            return False

    def record_audio(self):
        """Record audio while the hotkey is pressed."""
        self.logger.info("Waiting for hotkey press to start recording.")
        try:
            recording = np.array([], dtype="float64").reshape(0, 2)
            frames_per_buffer = int(self.sample_rate * 0.1)

            with keyboard.Listener(
                on_press=self.on_press, on_release=self.on_release
            ) as listener:
                while True:
                    if self.is_recording:
                        chunk = sd.rec(
                            frames_per_buffer,
                            samplerate=self.sample_rate,
                            channels=2,
                            dtype="float64",
                        )
                        sd.wait()
                        recording = np.vstack([recording, chunk])
                    if not self.is_recording and len(recording) > 0:
                        break
                listener.join()
            self.logger.info("Recording captured with %d samples.", len(recording))
        except Exception as e:
            self.logger.error("Error in recording audio: %s", e)
        return recording

    def save_temp_audio(self, recording):
        """Save the recorded audio to a temporary file."""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            write(temp_file.name, self.sample_rate, recording)
            self.logger.info("Audio saved to temporary file: %s", temp_file.name)
            return temp_file.name
        except Exception as e:
            self.logger.error("Error saving audio: %s", e)

    def transcribe(self, audio_filepath):
        """Transcribe the given audio file using Whisper."""
        try:
            self.logger.info("Transcribing audio file: %s", audio_filepath)
            result = self.model.transcribe(audio_filepath)
            query = result["text"].lower()
            self.logger.info("Transcription completed: %s", query)
            return query
        except Exception as e:
            self.logger.error("Error during transcription: %s", e)

    def run(self):
        """Main loop to handle recording and transcribing."""
        while True:
            recording = self.record_audio()
            transcription = self.transcribe(
                audio_filepath=self.save_temp_audio(recording)
            )
            self.logger.info("Transcription: %s", transcription)
            print(
                "\nPress Ctrl_R + Space to start the recording again, or press Ctrl+C to stop it.\n"
            )
