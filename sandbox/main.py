# import time
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
from ai_tools.ai_youtube_summary import YouTubeSummarizer
from ai_tools.speech.app_speech import SpeechApp
from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.speech.text_to_speech import TTSModel

warnings.simplefilter(action="ignore", category=FutureWarning)

load_dotenv(os.environ.get("USER_AGENT"))

ASSISTANT_NAME = "MAX"


class MaxAssistant:
    def __init__(self):
        self.transcribe = TranscribeFastModel()
        self.tts_model = TTSModel()

        self.speech_app = SpeechApp(self.tts_model)
        self.is_asleep = False
        self.running = True

        self._wish()
        self.summarizer = YouTubeSummarizer()
        self.web_summarizer = WebPageSummarizer(max_retries=3, retry_delay=2)

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

    def _speak(self, audio):
        """Call run_tts as a thread."""
        tts_thread = threading.Thread(target=self.run_tts, args=(audio,))
        tts_thread.start()
        tts_thread.join()

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
        self._speak(greeting)

    def _handle_command(self, query):
        """Handle the recognized command."""
        if "exit max" in query:
            self._speak("Shutting down ")
            self.running = False

        elif "summarize youtube" in query:
            self._speak("Please provide the YouTube video URL.")
            video_url = input("YouTube video URL: ")
            if video_url:
                self._speak("Downloading and summarizing the video...")
                summary = self.summarizer.summarize_youtube_video(video_url)
                self._speak("Here is the summary:")
                print(summary)

        elif "learn site" in query or "learn page" in query:
            self._speak("Please provide the website URL.")
            website_url = input("Listening for website URL: ").lstrip()

            while True:
                self._speak(
                    "Please provide the question you want answered from the website."
                )

                print("what do you wanna know about this side?")
                if "input" in query:
                    question = (
                        input(
                            "Please provide the question you want answered from the website: "
                        )
                        .lstrip()
                        .lower()
                    )
                else:
                    question = self._listen()

                    if website_url and question:
                        try:
                            result = self.web_summarizer.summarize_website(
                                website_url,
                                question,
                                summary_length="brief",
                            )

                            print("Summary:", result["summary"])
                            print("Keywords:", result["keywords"])
                            print("Sentiment:", result["sentiment"])
                        except ValueError as e:
                            print(f"Input error: {e}")
                        except Exception as e:
                            print(f"An unexpected error occurred: {e}")
                        # Ask the user if they want to ask another question
                self._speak(
                    "Do you want to ask another question about this website? Say 'yes' to continue or 'no' to stop."
                )
                continue_query = (
                    input("Do you want to ask another question? (yes/no): ")
                    .strip()
                    .lower()
                )

                if continue_query not in ["yes", "y"]:
                    self._speak("Thank you! Ending the session.")
                    break

        elif "time" in query:
            str_time = datetime.datetime.now().strftime("%H:%M")
            self._speak(f"Sir, the current time is {str_time}")

        elif "open edge" in query:
            self._speak("Opening Edge Browser...")
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if os.path.exists(edge_path):
                os.startfile(edge_path)
            else:
                self._speak("Edge browser not found on your system.")

        elif "what is your name" in query:
            self._speak(f"My name is {ASSISTANT_NAME}, your personal assistant!")

        elif "who are you" in query:
            self._speak(f"I am {ASSISTANT_NAME}, your personal assistant!")

        elif "wikipedia" in query:
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
                    self._speak(
                        "Sorry, I could not find any information on that topic."
                    )
                except Exception as e:
                    self._speak(f"An error occurred while searching Wikipedia: {e}")
            else:
                self._speak("Please specify a topic to search on Wikipedia.")

        elif "play" in query:
            song = query.replace("play", "").strip()
            if song:
                self._speak(f"Playing {song} on YouTube...")
                pywhatkit.playonyt(song)
            else:
                self._speak("Please specify a song to play.")

        elif "type" in query:
            self._speak("Please, tell me the text you want to type...")
            while True:
                text = self._listen()
                if "exit typing" in text:
                    self._speak("Exiting typing mode...")
                    break
                else:
                    pyautogui.write(text)

        elif "joke" in query:
            joke = pyjokes.get_joke()
            self._speak(joke)

        elif "speech app" in query:
            self._speak(f"Opening speech app...")
            self.speech_app.gradio()

        elif "minimize" in query or "minimise" in query:
            pyautogui.hotkey("win", "down")

        elif "maximize" in query:
            pyautogui.hotkey("win", "up")

        elif "close" in query:
            pyautogui.hotkey("alt", "f4")

        elif "volume up" in query:
            self._adjust_volume("up")

        elif "volume down" in query:
            self._adjust_volume("down")

        elif "mute" in query:
            self._adjust_volume("mute")

        elif "sleep" in query:
            self._speak("Going to sleep mode.")
            self.is_asleep = True
        elif "make a book" in query:
            self._run_book()

    def _adjust_volume(self, action):
        """Adjust the system volume."""
        if action == "up":
            pyautogui.press("volumeup")
        elif action == "down":
            pyautogui.press("volumedown")
        elif action == "mute":
            pyautogui.press("volumemute")
        elif action == "unmute":
            pyautogui.press("unmute")
        self._speak(f"Volume {action}")

    def _run_book():
        """make a small book"""
        thread = threading.Thread(target=asyncio(book_assistant.run()), daemon=True)
        thread.start()

    def _listen(self):
        try:
            # Start recording and transcription
            record = self.transcribe.record_audio()
            result = self.transcribe.transcribe(
                audio_filepath=self.transcribe.save_temp_audio(record)
            )
            query = result.lower()
            print(query)
            if self.is_asleep:
                if "wake up, max" in query:
                    self.is_asleep = False
                    self._speak("Waking up.")
                    return "wake up max"
                else:
                    return ""
            else:
                return query
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def run(self):
        """Main loop to keep the assistant running."""
        try:
            while self.running:
                print("Waiting for command...")
                query = self._listen()
                if query:  # Proceed only if there's valid input
                    self._speak(query)  # Speak the user input
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


if __name__ == "__main__":
    assistant = MaxAssistant()
    if assistant.running:
        assistant.run()
