import asyncio
import datetime
import warnings

from dotenv import find_dotenv, load_dotenv

from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel
from assistents.ai_assistent import AIAssistant
from assistents.system_assistent import SystemAssistant
from utils.loggers import LoggerSetup

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=UserWarning)
load_dotenv(find_dotenv(".env"))


class MaxAssistant:
    def __init__(self):
        """Initialize MaxAssistant with default settings."""
        self.transcribe = TranscribeFastModel()
        self.tts_model = TTSModel()
        self.is_asleep = False
        self.model_type = "good"  # Default to good model

        # Initialize AI and system assistants
        self.ai_assistant = AIAssistant(
            self.tts_model, self.transcribe, self._speak, self._listen
        )
        self.system_assistant = SystemAssistant(
            self.tts_model, self._speak, self._listen
        )

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("MaxAssistantLogger", "max_assistant.log")

        # Log initialization
        self.logger.info("MaxAssistant initialized.")

    async def _wish(self):
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
        await self._speak(greeting)

    def set_good_model(self):
        """Set the assistant to use the good model (TTS)."""
        self.tts_model.set_good_model()
        self.logger.info("Switched to good model.")

    def set_bad_model(self):
        """Set the assistant to use the bad model (pyttsx3)."""
        self.tts_model.set_bad_model()
        self.logger.info("Switched to bad model.")

    async def run(self):
        """Main loop to keep the assistant running and handle commands."""
        await self._wish()

        try:
            while True:
                query = await self._get_command()

                if "rust" in query:
                    await self._sleep(query)

                if self.is_asleep:
                    if "wake up" in query:
                        await self._wake_up()
                    continue

                if "exit" in query or "shut down" in query:
                    await self._speak("Shutting down.")
                    self.logger.info("Shutdown command received.")
                    break  # Exit the loop and trigger shutdown

                await self._handle_query(query)
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")

        # Call the shutdown method once the loop exits
        await self.shutdown()

    async def _handle_query(self, query):
        """Determine the task to handle based on the user query."""
        try:
            if "critique mode" in query:
                await self._speak("Switching to critique mode.")
                self.ai_assistant.set_llm_mode("critique")  # Switch to critique mode
            elif "reflecting mode" in query:
                await self._speak("Switching to reflecting mode.")
                self.ai_assistant.set_llm_mode(
                    "reflecting"
                )  # Switch to reflecting mode
            elif "switch to good model" in query:
                await self._speak("Switching to good model")
                self.set_good_model()
            elif "switch to bad model" in query:
                await self._speak("Switching to bad model")
                self.set_bad_model()
            elif self._is_system_command(query):
                await self.system_assistant.handle_command(query)
            elif self._is_ai_command(query):
                await self.ai_assistant.handle_command(query)
            else:
                self.logger.warning(f"Unknown command: {query}")
        except Exception as e:
            self.logger.error(f"Error in _handle_query: {e}")

    async def _get_command(self):
        """Retrieve command from the user via input or voice asynchronously."""
        try:
            input_task = asyncio.create_task(self._input_command(), name="Input task")
            listen_task = asyncio.create_task(
                self._listen_for_voice_command(), name="Voice in task"
            )

            done, pending = await asyncio.wait(
                [listen_task, input_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel the pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.info(f"{task.get_name()} was cancelled.")

            # Retrieve the result of the completed task
            completed_task = next(iter(done))
            return completed_task.result()

        except Exception as e:
            self.logger.error(f"Error in _get_command: {e}")
            return ""

    async def _speak(self, audio):
        """Speak asynchronously using the selected model."""
        try:
            await self.tts_model.tts_speak(audio)
            self.logger.info(f"Spoken: {audio}")
        except Exception as e:
            self.logger.error(f"Error in _speak: {e}")

    async def _listen(self):
        """Listen asynchronously using the Fastwhisper model."""
        try:
            result = await self.transcribe.run()
            self.logger.info(f"Listening result: {result}")
            return result
        except asyncio.CancelledError:
            self.logger.info("Listening task was cancelled.")
            return ""
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

    async def _input_command(self):
        """Get input from the user asynchronously."""
        try:
            result = await asyncio.to_thread(input, "Type your command: ")
            self.logger.info(f"User input: {result}")
            return result
        except asyncio.CancelledError:
            self.logger.info("Input task was cancelled.")
            return ""
        except EOFError:
            self.logger.error("Input stream closed.")
            return "exit"
        except Exception as e:
            self.logger.error(f"Error in _input_command: {e}")
            return "exit"

    async def _listen_for_voice_command(self):
        """Listen for a voice command."""
        return await self._listen()

    def _is_system_command(self, query):
        """Check if the query is a system command."""
        return any(
            command in query for command in self.system_assistant.commands.keys()
        )

    def _is_ai_command(self, query):
        """Check if the query is an AI-related command."""
        return any(command in query for command in self.ai_assistant.commands.keys())

    async def _sleep(self, query):
        """Put the assistant to sleep mode."""
        await self._speak("Going to sleep.")
        self.is_asleep = True
        self.logger.info("Assistant is now asleep.")

    async def _wake_up(self, query):
        """Wake up the assistant."""
        await self._speak("Waking up.")
        self.is_asleep = False
        self.logger.info("Assistant woke up.")

    async def shutdown(self):
        """Gracefully shut down the assistant."""
        self.logger.info("Shutting down assistants...")

        # Stop any ongoing recording
        self.transcribe.stop()  # Close the prompt_toolkit application if it's running
        if self.transcribe.app and self.transcribe.app.is_running:
            self.transcribe.app.exit()

        # Ensure we are working with the running event loop
        try:
            # Gather all running tasks excluding the current shutdown task
            tasks = [
                task
                for task in asyncio.all_tasks()
                if task is not asyncio.current_task()
            ]

            # Cancel all tasks
            for task in tasks:
                task.cancel()

            # Wait for all tasks to finish properly
            await asyncio.gather(*tasks, return_exceptions=True)

            # Shut down the event loop properly
            await asyncio.get_event_loop().shutdown_asyncgens()
        except RuntimeError as e:
            self.logger.warning(f"Event loop already closed: {e}")
        except Exception as e:
            self.logger.error(f"A error occured at shutdown: {e}")

        self.logger.info("Shutdown complete")


async def main():
    """Main entry point for the assistant."""
    assistant = MaxAssistant()
    try:
        await assistant.run()
    except KeyboardInterrupt:
        print("Received exit signal, shutting down...")
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exited gracefully.")
    except Exception as e:
        print(f"Unexpected error: {e}")
