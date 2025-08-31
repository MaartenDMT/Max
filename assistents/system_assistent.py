import datetime
import os
import shutil  # To get disk space info

import psutil  # To get system information
import pyautogui
import pyjokes
import pywhatkit  # Keep only this import for pywhatkit

from utils.loggers import LoggerSetup

# requests removed; httpx used for async HTTP calls



class SystemAssistant:
    def __init__(self, tts_model, speak, listen):
        """Initialize the system assistant agent with commands."""
        self.tts_model = tts_model
        # These will be placeholders for API context
        self._speak = speak
        self._listen = listen

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("SystemAssistant", "system_assistant.log")

        # Log initialization
        self.logger.info("System Assistant initialized.")

    # Placeholder for speak in API context
    async def _speak_api(self, message: str):
        self.logger.info(f"API Speak: {message}")
        return {"message": message}

    # Placeholder for listen in API context
    async def _listen_api(self):
        self.logger.info("API Listen: No direct listening in API context.")
        return ""

    async def _handle_command_api(self, command: str) -> dict:
        """Handle system commands based on user query for API."""
        command_lower = command.strip().lower()
        try:
            if "shutdown" in command_lower:
                return await self._shutdown_api()
            elif "restart" in command_lower:
                return await self._restart_api()
            elif "lock screen" in command_lower:
                return await self._lock_screen_api()
            elif "sleep" in command_lower:
                return await self._sleep_api()
            elif command_lower.startswith("open app"):
                app_name = command_lower.replace("open app", "").strip()
                return await self._open_app_api(app_name)
            elif command_lower.startswith("open file"):
                file_name = command_lower.replace("open file", "").strip()
                return await self._open_file_api(file_name)
            elif command_lower.startswith("delete file"):
                file_name = command_lower.replace("delete file", "").strip()
                return await self._delete_file_api(file_name)
            elif command_lower.startswith("create folder"):
                folder_name = command_lower.replace("create folder", "").strip()
                return await self._create_folder_api(folder_name)
            elif "move file" in command_lower and " to " in command_lower:
                parts = command_lower.replace("move file", "").strip().split(" to ")
                file_name = parts[0].strip()
                folder_name = parts[1].strip()
                return await self._move_file_api(file_name, folder_name)
            elif "battery status" in command_lower:
                return await self._battery_status_api()
            elif "cpu usage" in command_lower:
                return await self._cpu_usage_api()
            elif "memory usage" in command_lower:
                return await self._memory_usage_api()
            elif "disk space" in command_lower:
                return await self._disk_space_api()
            elif command_lower.startswith("weather"):
                location = command_lower.replace("weather", "").strip()
                return await self._get_weather_api(location)
            elif command_lower.startswith("set alarm for"):
                alarm_time = command_lower.replace("set alarm for", "").strip()
                return await self._set_alarm_api(alarm_time)
            elif "take screenshot" in command_lower:
                return await self._take_screenshot_api()
            elif command_lower.startswith("calculate"):
                expression = command_lower.replace("calculate", "").strip()
                return await self._calculate_api(expression)
            elif "tell time" in command_lower:
                return await self._tell_time_api()
            elif "open edge" in command_lower:
                return await self._open_edge_api()
            elif "tell name" in command_lower:
                return await self._tell_name_api()
            elif command_lower.startswith("play"):
                song = command_lower.replace("play", "").strip()
                return await self._play_song_api(song)
            elif "type text" in command_lower:
                return {
                    "status": "error",
                    "message": "Typing text is not supported via API directly.",
                }
            elif "tell joke" in command_lower:
                return await self._tell_joke_api()
            elif "minimize" in command_lower:
                return await self._minimize_api()
            elif "maximize" in command_lower:
                return await self._maximize_api()
            elif "close window" in command_lower:
                return await self._close_window_api()
            elif "volume up" in command_lower:
                return await self._adjust_volume_api("up")
            elif "volume down" in command_lower:
                return await self._adjust_volume_api("down")
            elif "mute volume" in command_lower:
                return await self._adjust_volume_api("mute")
            else:
                self.logger.warning(f"Unknown system command: {command}")
                return {
                    "status": "error",
                    "message": f"Sorry, I don't know how to handle '{command}'.",
                }
        except Exception as e:
            self.logger.error(f"Error handling system command '{command}': {str(e)}")
            return {"status": "error", "message": f"Error processing command: {str(e)}"}

    async def _shutdown_api(self) -> dict:
        """Shut down the system."""
        self.logger.info("Shutdown initiated.")
        # os.system("shutdown /s /t 1") # This will shut down the host machine, use with caution
        return {
            "status": "success",
            "message": "System shutdown command received (not executed in API mode).",
        }

    async def _restart_api(self) -> dict:
        """Restart the system."""
        self.logger.info("Restart initiated.")
        # os.system("shutdown /r /t 1") # This will restart the host machine, use with caution
        return {
            "status": "success",
            "message": "System restart command received (not executed in API mode).",
        }

    async def _lock_screen_api(self) -> dict:
        """Lock the screen."""
        self.logger.info("Lock screen command executed.")
        pyautogui.hotkey("win", "l")
        return {"status": "success", "message": "Screen locked."}

    async def _sleep_api(self) -> dict:
        """Put the system to sleep."""
        self.logger.info("Sleep command executed.")
        # os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0") # This will sleep the host machine, use with caution
        return {
            "status": "success",
            "message": "System sleep command received (not executed in API mode).",
        }

    async def _open_app_api(self, app_name: str) -> dict:
        """Open a specific application."""
        try:
            self.logger.info(f"Opening application: {app_name}")
            os.system(f"start {app_name}")
            return {"status": "success", "message": f"Opening {app_name}."}
        except Exception as e:
            self.logger.error(f"Error opening app {app_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to open {app_name}: {str(e)}",
            }

    async def _open_file_api(self, file_name: str) -> dict:
        """Open a file."""
        try:
            self.logger.info(f"Opening file: {file_name}")
            os.startfile(file_name)
            return {"status": "success", "message": f"Opening {file_name}."}
        except Exception as e:
            self.logger.error(f"Error opening file {file_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to open {file_name}: {str(e)}",
            }

    async def _delete_file_api(self, file_name: str) -> dict:
        """Delete a file."""
        try:
            self.logger.info(f"Deleting file: {file_name}")
            os.remove(file_name)
            return {"status": "success", "message": f"Deleted {file_name}."}
        except Exception as e:
            self.logger.error(f"Error deleting file {file_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to delete {file_name}: {str(e)}",
            }

    async def _create_folder_api(self, folder_name: str) -> dict:
        """Create a folder."""
        try:
            self.logger.info(f"Creating folder: {folder_name}")
            os.makedirs(folder_name)
            return {"status": "success", "message": f"Created folder {folder_name}."}
        except Exception as e:
            self.logger.error(f"Error creating folder {folder_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to create folder {folder_name}: {str(e)}",
            }

    async def _move_file_api(self, file_name: str, folder_name: str) -> dict:
        """Move a file to a folder."""
        try:
            self.logger.info(f"Moving file {file_name} to {folder_name}")
            shutil.move(file_name, folder_name)
            return {
                "status": "success",
                "message": f"Moved {file_name} to {folder_name}.",
            }
        except Exception as e:
            self.logger.error(
                f"Error moving file {file_name} to {folder_name}: {str(e)}"
            )
            return {
                "status": "error",
                "message": f"Failed to move {file_name} to {folder_name}: {str(e)}",
            }

    async def _battery_status_api(self) -> dict:
        """Get battery status."""
        try:
            battery = psutil.sensors_battery()
            percent = battery.percent
            self.logger.info(f"Battery status: {percent}%")
            return {
                "status": "success",
                "message": f"Battery is at {percent}%.",
                "data": {"percent": percent},
            }
        except Exception as e:
            self.logger.error(f"Error getting battery status: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get battery status: {str(e)}",
            }

    async def _cpu_usage_api(self) -> dict:
        """Get CPU usage."""
        try:
            usage = psutil.cpu_percent(interval=1)
            self.logger.info(f"CPU usage: {usage}%")
            return {
                "status": "success",
                "message": f"CPU usage is at {usage}%.",
                "data": {"usage": usage},
            }
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {str(e)}")
            return {"status": "error", "message": f"Failed to get CPU usage: {str(e)}"}

    async def _memory_usage_api(self) -> dict:
        """Get memory usage."""
        try:
            memory = psutil.virtual_memory()
            self.logger.info(f"Memory usage: {memory.percent}%")
            return {
                "status": "success",
                "message": f"Memory usage is at {memory.percent}%.",
                "data": {"percent": memory.percent},
            }
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get memory usage: {str(e)}",
            }

    async def _disk_space_api(self) -> dict:
        """Get disk space information."""
        try:
            total, used, free = shutil.disk_usage("/")
            total_gb = total // (2**30)
            used_gb = used // (2**30)
            free_gb = free // (2**30)
            self.logger.info(
                f"Disk space: Total={total_gb}GB, Used={used_gb}GB, Free={free_gb}GB"
            )
            return {
                "status": "success",
                "message": f"Total disk space: {total_gb}GB, Used: {used_gb}GB, Free: {free_gb}GB.",
                "data": {"total_gb": total_gb, "used_gb": used_gb, "free_gb": free_gb},
            }
        except Exception as e:
            self.logger.error(f"Error getting disk space: {str(e)}")
            return {"status": "error", "message": f"Failed to get disk space: {str(e)}"}

    async def _get_weather_api(self, location: str) -> dict:
        """Get weather information."""
        try:
            if not location:
                return {
                    "status": "error",
                    "message": "Location not provided for weather.",
                }
            self.logger.info(f"Fetching weather for location: {location}")
            import httpx
            api_key = "your_openweathermap_api_key"  # Replace with actual API key
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "http://api.openweathermap.org/data/2.5/weather",
                    params={"q": location, "appid": api_key},
                )
            if response.status_code == 200:
                weather_data = response.json()
                description = weather_data["weather"][0]["description"]
                temp = (
                    weather_data["main"]["temp"] - 273.15
                )  # Convert from Kelvin to Celsius
                message = f"The weather in {location} is {description} with a temperature of {temp:.1f} degrees Celsius."
                self.logger.info(f"Weather in {location}: {description}, {temp:.1f}°C")
                return {
                    "status": "success",
                    "message": message,
                    "data": {
                        "location": location,
                        "description": description,
                        "temperature_celsius": temp,
                    },
                }
            else:
                self.logger.error(f"Failed to retrieve weather for {location}")
                return {
                    "status": "error",
                    "message": f"Could not retrieve weather information for {location}.",
                }
        except Exception as e:
            self.logger.error(f"Error getting weather: {str(e)}")
            return {"status": "error", "message": f"Failed to get weather: {str(e)}"}

    async def _set_alarm_api(self, alarm_time: str) -> dict:
        """Set an alarm."""
        try:
            if not alarm_time:
                return {"status": "error", "message": "Alarm time not provided."}
            self.logger.info(f"Setting alarm for {alarm_time}")
            # Implement actual alarm setting logic here (e.g., using a scheduler)
            return {
                "status": "success",
                "message": f"Setting an alarm for {alarm_time} (functionality not fully implemented).",
            }
        except Exception as e:
            self.logger.error(f"Error setting alarm: {str(e)}")
            return {"status": "error", "message": f"Failed to set alarm: {str(e)}"}

    async def _take_screenshot_api(self) -> dict:
        """Take a screenshot."""
        try:
            screenshot_path = "data/pics/screenshot.png"
            pyautogui.screenshot().save(screenshot_path)
            self.logger.info(f"Screenshot taken and saved to {screenshot_path}")
            return {
                "status": "success",
                "message": "Screenshot taken and saved.",
                "data": {"path": screenshot_path},
            }
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to take screenshot: {str(e)}",
            }

    async def _calculate_api(self, expression: str) -> dict:
        """Perform a calculation."""
        try:
            if not expression:
                return {
                    "status": "error",
                    "message": "No expression provided for calculation.",
                }
            result = eval(expression)  # Be cautious with eval in production
            self.logger.info(f"Calculation performed: {expression} = {result}")
            return {
                "status": "success",
                "message": f"The result is {result}.",
                "data": {"expression": expression, "result": result},
            }
        except Exception as e:
            self.logger.error(f"Error calculating: {str(e)}")
            return {"status": "error", "message": f"Error calculating: {str(e)}"}

    async def _tell_time_api(self) -> dict:
        """Tell the current time."""
        try:
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.logger.info(f"Told time: {current_time}")
            return {
                "status": "success",
                "message": f"The time is {current_time}",
                "data": {"time": current_time},
            }
        except Exception as e:
            self.logger.error(f"Error telling time: {str(e)}")
            return {"status": "error", "message": f"Failed to get time: {str(e)}"}

    async def _open_edge_api(self) -> dict:
        """Open Microsoft Edge."""
        try:
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if os.path.exists(edge_path):
                self.logger.info("Opening Microsoft Edge.")
                os.startfile(edge_path)
                return {"status": "success", "message": "Opening Microsoft Edge."}
            else:
                self.logger.warning("Microsoft Edge is not installed.")
                return {
                    "status": "error",
                    "message": "Microsoft Edge is not installed on this system.",
                }
        except Exception as e:
            self.logger.error(f"Error opening Microsoft Edge: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to open Microsoft Edge: {str(e)}",
            }

    async def _tell_name_api(self) -> dict:
        """Tell the assistant's name."""
        try:
            self.logger.info("Told assistant's name.")
            return {
                "status": "success",
                "message": "My name is System Assistant, your personal helper!",
            }
        except Exception as e:
            self.logger.error(f"Error telling name: {str(e)}")
            return {"status": "error", "message": f"Failed to tell name: {str(e)}"}

    async def _play_song_api(self, song: str) -> dict:
        """Play a song on YouTube."""
        try:
            if not song:
                return {"status": "error", "message": "Please specify a song to play."}
            self.logger.info(f"Playing song: {song}")
            pywhatkit.playonyt(song)  # Corrected call
            return {"status": "success", "message": f"Playing {song} on YouTube."}
        except Exception as e:
            self.logger.error(f"Error playing song: {str(e)}")
            return {"status": "error", "message": f"Failed to play song: {str(e)}"}

    async def _tell_joke_api(self) -> dict:
        """Tell a random joke."""
        try:
            joke = pyjokes.get_joke()
            self.logger.info(f"Told joke: {joke}")
            return {"status": "success", "message": joke}
        except Exception as e:
            self.logger.error(f"Error telling joke: {str(e)}")
            return {"status": "error", "message": f"Failed to tell joke: {str(e)}"}

    async def _minimize_api(self) -> dict:
        """Minimize the active window."""
        try:
            self.logger.info("Minimizing window.")
            pyautogui.hotkey("win", "down")
            return {"status": "success", "message": "Window minimized."}
        except Exception as e:
            self.logger.error(f"Error minimizing window: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to minimize window: {str(e)}",
            }

    async def _maximize_api(self) -> dict:
        """Maximize the active window."""
        try:
            self.logger.info("Maximizing window.")
            pyautogui.hotkey("win", "up")
            return {"status": "success", "message": "Window maximized."}
        except Exception as e:
            self.logger.error(f"Error maximizing window: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to maximize window: {str(e)}",
            }

    async def _close_window_api(self) -> dict:
        """Close the active window."""
        try:
            self.logger.info("Closing window.")
            pyautogui.hotkey("alt", "f4")
            return {"status": "success", "message": "Active window closed."}
        except Exception as e:
            self.logger.error(f"Error closing window: {str(e)}")
            return {"status": "error", "message": f"Failed to close window: {str(e)}"}

    async def _adjust_volume_api(self, direction: str) -> dict:
        """Adjust the system volume."""
        try:
            if direction == "up":
                pyautogui.press("volumeup")
                self.logger.info("Volume increased.")
                return {"status": "success", "message": "Volume increased."}
            elif direction == "down":
                pyautogui.press("volumedown")
                self.logger.info("Volume decreased.")
                return {"status": "success", "message": "Volume decreased."}
            elif direction == "mute":
                pyautogui.press("volumemute")
                self.logger.info("Volume muted.")
                return {"status": "success", "message": "Volume muted."}
            else:
                return {
                    "status": "error",
                    "message": "Invalid volume direction. Use 'up', 'down', or 'mute'.",
                }
        except Exception as e:
            self.logger.error(f"Error adjusting volume: {str(e)}")
            return {"status": "error", "message": f"Failed to adjust volume: {str(e)}"}
