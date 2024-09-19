import datetime
import os
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import pyttsx3

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel
from assistents.ai_assistent import AIAssistantAgent
from assistents.system_assistent import SystemAssistantAgent
from utils.loggers import LoggerSetup  # Assuming your logger file is named 'logger.py'


class MaxAssistant:
    def __init__(self):
        """Initialize MaxAssistant with default settings."""
        self.transcribe = TranscribeFastModel()
        self.tts_model = TTSModel()
        self.is_asleep = False
        self.mode = "fast"  # Default to slow mode
        self.slow_tts_engine = self._init_slow_tts_engine()

        # Thread management for pyttsx3
        self.slow_mode_thread = None
        self.slow_mode_event = threading.Event()

        # Initialize AI and system assistants
        self.ai_assistant = AIAssistantAgent(
            self.tts_model, self.transcribe, self._speak, self._listen
        )
        self.system_assistant = SystemAssistantAgent(
            self.tts_model, self._speak, self._listen
        )

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("MaxAssistantLogger", "max_assistant.log")

        # Thread pool for executing tasks in background
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Log initialization
        self.logger.info("MaxAssistant initialized.")

    def _init_slow_tts_engine(self):
        """Initialize pyttsx3 engine with proper settings."""
        slow_tts_engine = pyttsx3.init()
        slow_tts_engine.setProperty("rate", 150)  # Set speaking rate
        slow_tts_engine.setProperty("volume", 1.0)  # Set volume to 100%
        return slow_tts_engine

    def _wish(self):
        """Greet the user based on the current time."""
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good Morning, BOSS"
        elif hour < 17:
            greeting = "Good Afternoon, BOSS"
        elif hour < 21:
            greeting = "Good Evening, BOSS"
        else:
            greeting = "Good Night, BOSS"

        self.logger.info(f"Greeting user: {greeting}")
        self._speak(greeting)

    def set_mode(self, mode):
        """Set the assistant's mode to 'slow' (pyttsx3) or 'fast' (TTSModel)."""
        if mode in ["slow", "fast"]:
            self.mode = mode
            self.logger.info(f"Switched to {self.mode} mode.")
        else:
            self.logger.warning("Invalid mode selection.")
            print("Invalid mode. Mode remains unchanged.")

    def run(self):
        """Main loop to keep the assistant running and handle commands."""
        self._wish()
        while True:
            query = self._get_command()
            if self.is_asleep:
                if "wake up" in query:
                    self._wake_up()
                continue

            self._handle_query(query)

    def _handle_query(self, query):
        """Determine the task to handle based on the user query."""
        try:
            if "switch to slow mode" in query:
                self.set_mode("slow")
            elif "switch to fast mode" in query:
                self.set_mode("fast")
            elif self._is_system_command(query):
                if "sleep" in query:
                    self._sleep(query)
                else:
                    self.system_assistant._handle_command(query)
            elif self._is_ai_command(query):
                self.ai_assistant._determine_task(query)
            else:
                self.logger.warning(f"Unknown command: {query}")
        except Exception as e:
            self.logger.error(f"Error in _handle_query: {e}")

    def _get_command(self):
        """Retrieve command from the user via input or voice."""
        input_task = self.executor.submit(self._input_command)
        listen_task = self.executor.submit(self._listen_for_voice_command)

        # Wait for either input_task or listen_task to complete first
        done, _ = wait([input_task, listen_task], return_when=FIRST_COMPLETED)

        # Stop the transcription service if input_task completed first
        if input_task in done:
            self.transcribe.stop()

        # Return the result of the completed task
        try:
            for task in done:
                return task.result()
        except Exception as e:
            self.logger.error(f"Error in getting command: {e}")
            return ""

    def _speak(self, audio):
        """Speak using the selected mode (slow or fast)."""
        try:
            if self.mode == "fast":
                self.executor.submit(self.run_tts, audio)
            else:
                # Use pyttsx3 in a thread to avoid blocking
                self.executor.submit(self._speak_slow_mode, audio)

            self.logger.info(f"Spoken: {audio}")
        except Exception as e:
            self.logger.error(f"Error in _speak: {e}")

    def _speak_slow_mode(self, audio):
        """Run pyttsx3 in a dedicated thread to prevent blocking."""
        if self.slow_mode_thread and self.slow_mode_thread.is_alive():
            self._wait_for_slow_mode()

        self.slow_mode_event.set()  # Allow speaking to start
        self.slow_mode_thread = threading.Thread(
            target=self.run_slow_tts, args=(audio,)
        )
        self.slow_mode_thread.start()

        # Wait for pyttsx3 to finish
        self.slow_mode_thread.join()

    def run_tts(self, audio):
        """Speak using TTSModel."""
        try:
            self.tts_model.tts_speak(audio)
            self.tts_model.play_audio()
        except Exception as e:
            self.logger.error(f"Error in run_tts: {e}")
        finally:
            if os.path.exists(self.tts_model.temp_audio):
                os.remove(self.tts_model.temp_audio)

    def run_slow_tts(self, audio):
        """Speak using pyttsx3 for slow mode."""
        try:
            self.slow_tts_engine.say(audio)
            self.slow_tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Error in run_slow_tts: {e}")

    def _wait_for_slow_mode(self):
        """Wait for pyttsx3 slow mode to complete before starting a new one."""
        if self.slow_mode_thread:
            self.slow_mode_thread.join()

    def _listen(self):
        """Listen using the Fastwhisper model."""
        try:
            result = self.executor.submit(self.run_listen).result()
            self.logger.info(f"Listening result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error in _listen: {e}")
            return ""

    def run_listen(self):
        """Transcribe speech input."""
        try:
            return self.transcribe.run()
        except Exception as e:
            self.logger.error(f"Error in run_listen: {e}")
            return ""

    def _input_command(self):
        """Get input from the user."""
        try:
            result = input("Type your command: ")
            self.logger.info(f"User input: {result}")
            return result
        except EOFError:
            self.logger.error("Input stream closed.")
            return "exit"

    def _listen_for_voice_command(self):
        """Listen for a voice command."""
        return self._listen()

    def _is_system_command(self, query):
        """Check if the query is a system command."""
        return any(
            command in query for command in self.system_assistant.commands.keys()
        )

    def _is_ai_command(self, query):
        """Check if the query is an AI-related command."""
        return any(keyword in query for keyword in ["youtube", "website", "music loop"])

    def _sleep(self, query):
        """Put the assistant to sleep mode."""
        self._speak("Going to sleep.")
        self.is_asleep = True
        self.logger.info("Assistant is now asleep.")

    def _wake_up(self):
        """Wake up the assistant."""
        self._speak("Waking up.")
        self.is_asleep = False
        self.logger.info("Assistant woke up.")

    def shutdown(self):
        """Gracefully shut down the assistant."""
        self.logger.info("Shutting down assistants...")

        # Stop pyttsx3 thread
        if self.slow_mode_thread and self.slow_mode_thread.is_alive():
            self.slow_mode_event.clear()  # Signal pyttsx3 to stop
            self.slow_mode_thread.join(
                timeout=5
            )  # Join with a timeout to prevent hanging

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.logger.info("Shutdown complete")


if __name__ == "__main__":
    assistant = MaxAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("Received exit signal, shutting down...")
        assistant.shutdown()
