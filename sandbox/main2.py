import asyncio
import datetime
import os
import threading
import warnings

import pyautogui
import pyjokes
import pywhatkit
import wikipedia
from dotenv import load_dotenv

from ai_tools.ai_bookwriter.bookwriter import book_assistant
from ai_tools.ai_doc_webpage_summarizer import WebPageSummarizer
from ai_tools.ai_music_generation import MusicLoopGenerator
from ai_tools.ai_youtube_summary import YouTubeSummarizer
from ai_tools.speech.app_speech import SpeechApp
from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel

warnings.simplefilter(action="ignore", category=FutureWarning)

load_dotenv(os.environ.get("USER_AGENT"))

ASSISTANT_NAME = "MAX"


class Assistant:
    def __init__(self, tts_model, transcribe):
        self.transcribe = transcribe
        self.tts_model = tts_model
        self.speech_app = SpeechApp(self.tts_model)
        self.summarizer = YouTubeSummarizer()
        self.web_summarizer = WebPageSummarizer(max_retries=3, retry_delay=2)
        self.music_loop_generator = MusicLoopGenerator

        self.is_asleep = False
        self.running = True
        self.voice_command = None
        self.commands = {
            "exit max": self._exit,
            "time": self._tell_time,
            "open edge": self._open_edge,
            "what is your name": self._tell_name,
            "who are you": self._tell_name,
            "play": self._play_song,
            "type": self._type_text,
            "joke": self._tell_joke,
            "minimize": self._minimize,
            "minimise": self._minimize,
            "maximize": self._maximize,
            "close": self._close_window,
            "volume up": lambda: self._adjust_volume("up"),
            "volume down": lambda: self._adjust_volume("down"),
            "mute": lambda: self._adjust_volume("mute"),
            "sleep": self._sleep,
        }

    def _speak(self, audio):
        """Call run_tts as a thread."""
        tts_thread = threading.Thread(target=self.run_tts, args=(audio,))
        tts_thread.start()
        tts_thread.join()

    def run_tts(self, audio):
        """Convert text to speech using TTSModel and play it."""
        print(f"Speaking: {audio}")
        try:
            self.tts_model.tts_speak(audio)  # Generate speech
            self.tts_model.play_audio()  # Play the audio
        except Exception as e:
            print(f"Error occurred during TTS: {e}")
        finally:
            os.remove(self.tts_model.temp_audio)
            print("Finished speaking.")

    async def _get_command(self):
        """Get the command dynamically based on whether the user is speaking or typing."""
        print("Listening for a command (speak or type)...")
        print("Press Enter to type, or start speaking.")
        try:
            listen_task = asyncio.create_task(self._listen_for_voice_command())
            input_task = asyncio.create_task(self._input_command())

            # Wait for whichever input comes first
            done, pending = await asyncio.wait(
                [listen_task, input_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel the pending task (the other input method)
            for task in pending:
                task.cancel()

            # Get the result of the completed task
            for task in done:
                return task.result()
        except Exception as e:
            print(f"Error occurred during voice command listening: {e}")
        finally:
            self.transcribe.stop()

    async def _input_command(self):
        """Get input from the user asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, "Type your command: ")

    async def _listen_for_voice_command(self):
        """Listen for a voice command."""
        try:
            self.voice_command = await asyncio.get_event_loop().run_in_executor(
                None, self._listen
            )
            return self.voice_command
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def _handle_command(self, query):
        """Handle the recognized command."""
        for command, action in self.commands.items():
            if command in query:
                action(query)
                break
        else:
            self._speak("Sorry, I didn't understand that command.")

    def _listen(self):
        try:
            record = self.transcribe.record_audio()
            result = self.transcribe.transcribe(
                audio_filepath=self.transcribe.save_temp_audio(record)
            )
            query = result.lower()
            if self.is_asleep:
                if "wake up" in query:
                    self.is_asleep = False
                    self._speak("Waking up.")
                    return "wake up"
                else:
                    return ""
            else:
                return query
        except Exception as e:
            print(f"Error: {e}")
            return ""

    async def run(self):
        """Main loop to keep the assistant running."""
        try:
            while self.running:
                query = await self._get_command()  # Get the command
                if query:  # Proceed only if there's valid input
                    self._handle_command(query)
        except KeyboardInterrupt:
            print("Shutting down gracefully...")
            self._shutdown()
        except Exception as e:
            print(f"An error occurred while running the assistant: {e}")

    def _shutdown(self):
        """Clean up resources and shut down the assistant."""
        self.running = False
        print("Assistant has been shut down.")

    def _exit(self, query):
        self._speak("Shutting down.")
        self.running = False

    def _summarize_youtube(self, query):
        self._speak("Please provide the YouTube video URL.")
        video_url = input("YouTube video URL: ")
        if video_url:
            self._speak("Downloading and summarizing the video...")
            summary = self.summarizer.summarize_youtube_video(video_url)
            self._speak("Here is the summary:")
            print(summary)

    def _learn_site(self, query):
        self._speak("Please provide the website URL.")
        website_url = input("Listening for website URL: ").lstrip()

        while True:
            self._speak(
                "Please provide the question you want answered from the website."
            )
            print("What do you want to know about this site?")
            question = (
                input("Please provide the question: ")
                if "input" in query
                else self._listen()
            )

            if website_url and question:
                try:
                    result = self.web_summarizer.summarize_website(
                        website_url, question, summary_length="brief"
                    )
                    print("Summary:", result["summary"])
                    print("Keywords:", result["keywords"])
                    print("Sentiment:", result["sentiment"])
                except ValueError as e:
                    print(f"Input error: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

            self._speak(
                "Do you want to ask another question about this website? Say 'yes' to continue or 'no' to stop."
            )
            continue_query = (
                input("Do you want to ask another question? (yes/no): ").strip().lower()
            )

            if continue_query not in ["yes", "y"]:
                self._speak("Thank you! Ending the session.")
                break

    def _tell_time(self, query):
        str_time = datetime.datetime.now().strftime("%H:%M")
        self._speak(f"Sir, the current time is {str_time}")

    def _open_edge(self, query):
        self._speak("Opening Edge Browser...")
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(edge_path):
            os.startfile(edge_path)
        else:
            self._speak("Edge browser not found on your system.")

    def _tell_name(self, query):
        self._speak(f"My name is {ASSISTANT_NAME}, your personal assistant!")

    def _search_wikipedia(self, query):
        self._speak("Searching Wikipedia...")
        query = query.replace("wikipedia", "").strip()
        if query:
            try:
                results = wikipedia.summary(query, sentences=2)
                self._speak(f"According to Wikipedia, {results}")
            except wikipedia.exceptions.DisambiguationError as e:
                self._speak(
                    "There are multiple entries for this topic. Please be more specific."
                )
            except wikipedia.exceptions.PageError:
                self._speak("Sorry, I could not find any information on that topic.")
            except Exception as e:
                self._speak(f"An error occurred while searching Wikipedia: {e}")
        else:
            self._speak("Please specify a topic to search on Wikipedia.")

    def _play_song(self, query):
        song = query.replace("play", "").strip()
        if song:
            self._speak(f"Playing {song} on YouTube...")
            pywhatkit.playonyt(song)
        else:
            self._speak("Please specify a song to play.")

    def _type_text(self, query):
        self._speak("Please, tell me the text you want to type...")
        while True:
            text = self._listen()
            if "exit typing" in text:
                self._speak("Exiting typing mode...")
                break
            else:
                pyautogui.write(text)

    def _tell_joke(self, query):
        joke = pyjokes.get_joke()
        self._speak(joke)

    def _open_speech_app(self, query):
        self._speak("Opening speech app...")
        self.speech_app.gradio()

    def _minimize(self, query):
        pyautogui.hotkey("win", "down")

    def _maximize(self, query):
        pyautogui.hotkey("win", "up")

    def _close_window(self, query):
        pyautogui.hotkey("alt", "f4")

    def _adjust_volume(self, direction):
        # Implement the volume control logic here
        pass

    def _sleep(self, query):
        self._speak("Going to sleep mode.")
        self.is_asleep = True

    def _make_book(self, query):
        self._run_book()

    def _listen2(self):
        # Implement speech-to-text logic here
        return input("Listening for your command: ")

    def _run_book(self):
        # Implement the logic for "make a book" command
        """make a small book"""
        thread = threading.Thread(target=asyncio(book_assistant.run()), daemon=True)
        thread.start()

    def _make_loop(self):
        """make a music loop"""
        self._speak("Making a music loop...")
        prompt = input("what kind of music loop do you want: ").lstrip()
        bpm = input("what BPM do you want: ")
        output = self.music_loop_generator.generate_loop(prompt, bpm)
        print("output: " + output)


class MaxAssistant:
    def __init__(self):
        self.transcribe = TranscribeFastModel()
        self.tts_model = TTSModel()

        # Integrate Assistant class
        self.assistant = Assistant(self.tts_model, self.transcribe, self.speech_app)

        self._wish()

    def _wish(self):
        """Wish the user based on the current time."""
        hour = int(datetime.datetime.now().hour)
        if hour >= 0 and hour < 12:
            greeting = "Good Morning, BOSS"
        elif hour >= 12 and hour < 17:
            greeting = "Good Afternoon, BOSS"
        elif hour >= 17 and hour < 21:
            greeting = "Good Evening, BOSS"
        else:
            greeting = "Good Night, BOSS"
        print(greeting)
        self.assistant._speak(greeting)

    def run(self):
        """Main loop to keep the assistant running."""
        asyncio.run(self.assistant.run())


if __name__ == "__main__":
    max_assistant = MaxAssistant()
    if max_assistant.running:
        max_assistant.run()
