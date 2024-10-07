import datetime
import os
import shutil  # To get disk space info
import webbrowser

import psutil  # To get system information
import pyautogui
import pyjokes
import pywhatkit
import requests

from utils.loggers import LoggerSetup
from utils.call_commands import get_system_commands


class SystemAssistant:
    def __init__(self, tts_model, speak, listen):
        """Initialize the system assistant agent with commands."""
        self.tts_model = tts_model
        self._speak = speak
        self._listen = listen

        self.commands = get_system_commands(self)

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("SystemAssistant", "system_assistant.log")

        # Log initialization
        self.logger.info("System Assistant initialized.")

    async def handle_command(self, query):
        """Handle system commands based on user query."""
        command_key = query.strip().lower()
        if command_key in self.commands:
            command_func = self.commands[command_key]
            self.logger.info(f"Executing system command: {command_key}")
            await command_func(query)
        else:
            self.logger.warning(f"Unknown system command: {command_key}")
            await self._speak(f"Sorry, I don't know how to handle '{query}'.")

    # System Control Functions
    async def _shutdown(self, query):
        """Shut down the system."""
        await self._speak("Shutting down the system.")
        self.logger.info("Shutdown initiated.")
        os.system("shutdown /s /t 1")

    async def _restart(self, query):
        """Restart the system."""
        await self._speak("Restarting the system.")
        self.logger.info("Restart initiated.")
        os.system("shutdown /r /t 1")

    async def _lock_screen(self, query):
        """Lock the screen."""
        await self._speak("Locking the screen.")
        self.logger.info("Lock screen command executed.")
        pyautogui.hotkey("win", "l")

    async def _sleep(self, query):
        """Put the system to sleep."""
        await self._speak("Putting the system to sleep.")
        self.logger.info("Sleep command executed.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    async def _open_app(self, query):
        """Open a specific application."""
        app_name = query.replace("open app", "").strip()
        await self._speak(f"Opening {app_name}.")
        self.logger.info(f"Opening application: {app_name}")
        os.system(f"start {app_name}")

    # File Operations
    async def _open_file(self, query):
        """Open a file."""
        file_name = query.replace("open file", "").strip()
        await self._speak(f"Opening {file_name}.")
        self.logger.info(f"Opening file: {file_name}")
        os.startfile(file_name)

    async def _delete_file(self, query):
        """Delete a file."""
        file_name = query.replace("delete file", "").strip()
        await self._speak(f"Deleting {file_name}.")
        self.logger.info(f"Deleting file: {file_name}")
        os.remove(file_name)

    async def _create_folder(self, query):
        """Create a folder."""
        folder_name = query.replace("create folder", "").strip()
        await self._speak(f"Creating folder {folder_name}.")
        self.logger.info(f"Creating folder: {folder_name}")
        os.makedirs(folder_name)

    async def _move_file(self, query):
        """Move a file to a folder."""
        parts = query.replace("move file", "").strip().split(" to ")
        file_name = parts[0].strip()
        folder_name = parts[1].strip()
        await self._speak(f"Moving {file_name} to {folder_name}.")
        self.logger.info(f"Moving file {file_name} to {folder_name}")
        shutil.move(file_name, folder_name)

    # System Information
    async def _battery_status(self, query):
        """Get battery status."""
        battery = psutil.sensors_battery()
        percent = battery.percent
        self.logger.info(f"Battery status: {percent}%")
        await self._speak(f"Battery is at {percent}%.")

    async def _cpu_usage(self, query):
        """Get CPU usage."""
        usage = psutil.cpu_percent(interval=1)
        self.logger.info(f"CPU usage: {usage}%")
        await self._speak(f"CPU usage is at {usage}%.")

    async def _memory_usage(self, query):
        """Get memory usage."""
        memory = psutil.virtual_memory()
        self.logger.info(f"Memory usage: {memory.percent}%")
        await self._speak(f"Memory usage is at {memory.percent}%.")

    async def _disk_space(self, query):
        """Get disk space information."""
        total, used, free = shutil.disk_usage("/")
        total_gb = total // (2**30)
        used_gb = used // (2**30)
        free_gb = free // (2**30)
        self.logger.info(
            f"Disk space: Total={total_gb}GB, Used={used_gb}GB, Free={free_gb}GB"
        )
        await self._speak(
            f"Total disk space: {total_gb}GB, Used: {used_gb}GB, Free: {free_gb}GB."
        )

    # Weather
    async def _get_weather(self, query):
        """Get weather information."""
        location = query.replace("weather", "").strip()
        await self._speak(f"Checking weather for {location}.")
        self.logger.info(f"Fetching weather for location: {location}")
        # Use a weather API to fetch the information, e.g., OpenWeatherMap
        api_key = "your_openweathermap_api_key"
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        )
        if response.status_code == 200:
            weather_data = response.json()
            description = weather_data["weather"][0]["description"]
            temp = (
                weather_data["main"]["temp"] - 273.15
            )  # Convert from Kelvin to Celsius
            await self._speak(
                f"The weather in {location} is {description} with a temperature of {temp:.1f} degrees Celsius."
            )
            self.logger.info(f"Weather in {location}: {description}, {temp:.1f}°C")
        else:
            self.logger.error(f"Failed to retrieve weather for {location}")
            await self._speak(f"Could not retrieve weather information for {location}.")

    # Alarms and Timers
    async def _set_alarm(self, query):
        """Set an alarm."""
        time = query.replace("set alarm for", "").strip()
        self.logger.info(f"Setting alarm for {time}")
        await self._speak(f"Setting an alarm for {time}.")

    # Screenshots
    async def _take_screenshot(self, query):
        """Take a screenshot."""
        screenshot = pyautogui.screenshot()
        screenshot.save("data/pics/screenshot.png")
        self.logger.info("Screenshot taken and saved to data/pics/screenshot.png")
        await self._speak("Screenshot taken and saved.")

    # Math/Calculation
    async def _calculate(self, query):
        """Perform a calculation."""
        expression = query.replace("calculate", "").strip()
        try:
            result = eval(expression)
            self.logger.info(f"Calculation performed: {expression} = {result}")
            await self._speak(f"The result is {result}.")
        except Exception as e:
            self.logger.error(f"Error calculating: {e}")
            await self._speak(f"Error calculating: {e}")

    # Existing Functions for Edge, Name, Volume, etc.

    async def _tell_time(self, query):
        """Tell the current time."""
        try:
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.logger.info(f"Told time: {current_time}")
            await self._speak(f"The time is {current_time}")
        except Exception as e:
            self.logger.error(f"Error telling time: {e}")

    async def _open_edge(self, query):
        """Open Microsoft Edge."""
        try:
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if os.path.exists(edge_path):
                self.logger.info("Opening Microsoft Edge.")
                os.startfile(edge_path)
            else:
                self.logger.warning("Microsoft Edge is not installed.")
                await self._speak("Microsoft Edge is not installed on this system.")
        except Exception as e:
            self.logger.error(f"Error opening Microsoft Edge: {e}")

    async def _tell_name(self, query):
        """Tell the assistant's name."""
        try:
            await self._speak("My name is System Assistant, your personal helper!")
            self.logger.info("Told assistant's name.")
        except Exception as e:
            self.logger.error(f"Error telling name: {e}")

    async def _play_song(self, query):
        """Play a song on YouTube."""
        try:
            song = query.replace("play", "").strip()
            if song:
                await self._speak(f"Playing {song} on YouTube.")
                self.logger.info(f"Playing song: {song}")
                pywhatkit.playonyt(song)
            else:
                await self._speak("Please specify a song to play.")
                self.logger.warning("No song specified to play.")
        except Exception as e:
            self.logger.error(f"Error playing song: {e}")

    async def _type_text(self, query):
        """Type text based on user voice input."""
        try:
            await self._speak(
                "You can start dictating the text. Say 'exit type' to stop."
            )
            while True:
                text = await self._listen()
                if "exit type" in text.lower():
                    await self._speak("Exiting typing mode.")
                    self.logger.info("Exiting typing mode.")
                    break
                pyautogui.write(text)
                self.logger.info(f"Typed text: {text}")
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")

    async def _tell_joke(self, query):
        """Tell a random joke."""
        try:
            joke = pyjokes.get_joke()
            await self._speak(joke)
            self.logger.info(f"Told joke: {joke}")
        except Exception as e:
            self.logger.error(f"Error telling joke: {e}")

    async def _minimize(self, query):
        """Minimize the active window."""
        try:
            await self._speak("Minimizing window.")
            self.logger.info("Minimizing window.")
            pyautogui.hotkey("win", "down")
        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")

    async def _maximize(self, query):
        """Maximize the active window."""
        try:
            await self._speak("Maximizing window.")
            self.logger.info("Maximizing window.")
            pyautogui.hotkey("win", "up")
        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")

    async def _close_window(self, query):
        """Close the active window."""
        try:
            await self._speak("Closing the active window.")
            self.logger.info("Closing window.")
            pyautogui.hotkey("alt", "f4")
        except Exception as e:
            self.logger.error(f"Error closing window: {e}")

    async def _adjust_volume(self, direction):
        """Adjust the system volume."""
        try:
            if direction == "up":
                await self._speak("Turning volume up.")
                pyautogui.press("volumeup")
                self.logger.info("Volume increased.")
            elif direction == "down":
                await self._speak("Turning volume down.")
                pyautogui.press("volumedown")
                self.logger.info("Volume decreased.")
            elif direction == "mute":
                await self._speak("Muting volume.")
                pyautogui.press("volumemute")
                self.logger.info("Volume muted.")
        except Exception as e:
            self.logger.error(f"Error adjusting volume: {e}")
