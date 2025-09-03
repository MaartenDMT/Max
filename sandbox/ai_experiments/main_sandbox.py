import datetime
import os

import pyautogui
import pyjokes
import pyttsx3
import pywhatkit
import soundfile as sf
import speech_recognition as sr
import wikipedia
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play

from ai_tools.ai_doc_webpage_summarizer import WebPageSummarizer
from ai_tools.ai_youtube_summary import YouTubeSummarizer

load_dotenv(os.environ.get("USER_AGENT"))


class MaxAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_asleep = False
        self.running = True

        # Initialize pyttsx3 TTS
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)  # Speed of speech
            self.engine.setProperty("volume", 1)  # Volume (0.0 to 1.0)
        except Exception as e:
            print(f"Failed to initialize TTS: {e}")
            self.running = (
                False  # Prevent the assistant from running if TTS initialization fails
            )

        self._wish()
        self.summarizer = YouTubeSummarizer()
        self.web_summarizer = WebPageSummarizer()

    def _speak(self, audio):
        """Convert text to speech using pyttsx3."""
        try:
            print(f"Speaking: {audio}")
            self.engine.say(audio)
            self.engine.runAndWait()
            print("Finished speaking.")
        except Exception as e:
            print(f"Error in speaking: {e}")

    def _listen(self, prompt="Listening..."):
        """Listen to a voice command and return the recognized text. If asleep, only respond to 'wake up max'."""
        with sr.Microphone() as source:
            print(prompt)
            try:
                self.recognizer.pause_threshold = 1
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source)
            except Exception as e:
                print(f"Error in listening {e}")
        try:
            print("Processing...")
            # Recognize speech using Sphinx (offline) or Google (online)
            query = self.recognizer.recognize_google(audio, language="en-US")
            print(f"You said: {query}\n")
            query = query.lower()

            if self.is_asleep:
                if "wake up max" in query:
                    self.is_asleep = False
                    self._speak("Waking up.")
                    return "wake up max"
                else:
                    return ""  # Ignore other commands when asleep
            else:
                return query  # Normal listening when awake

        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""

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
            self._speak("I'm leaving, bye!")
            self.running = False

        elif "summarize youtube" in query:
            self._speak("Please provide the YouTube video URL.")
            video_url = input("YouTube video URL:")
            if video_url:
                self._speak("Downloading and summarizing the video...")
                summary = self.summarizer.summarize_youtube_video(video_url)
                self._speak("Here is the summary:")
                print(summary)

        elif "summarize a site" in query or "summarize a webpage" in query:
            self._speak("Please provide the website URL.")
            website_url = self._listen(prompt="Listening for website URL...")
            self._speak(
                "Please provide the question you want answered from the website."
            )
            question = self._listen(prompt="Listening for your question...")
            if website_url and question:
                self._speak("Summarizing the website content...")
                summary = self.web_summarizer.summarize_website(website_url, question)
                self._speak("Here is the summary:")
                print(summary)

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
            self._speak("My name is Jarvis, your personal assistant!")

        elif "who are you" in query:
            self._speak("I am Jarvis, your personal assistant!")

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
                text = self._listen(prompt="Listening for text...")
                if "exit typing" in text:
                    self._speak("Exiting typing mode...")
                    break
                else:
                    pyautogui.write(text)

        elif "joke" in query:
            joke = pyjokes.get_joke()
            self._speak(joke)

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
        else:
            return ""

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

    def run(self):
        """Main loop to keep the assistant running."""
        try:
            while self.running:
                print("Waiting for command...")
                query = self._listen(
                    prompt="Listening for command..."
                )  # Listen for voice command
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
    if assistant.running:  # Only start if initialization succeeded
        assistant.run()
