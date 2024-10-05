import asyncio
import logging
from re import T

from ai_tools.ai_bookwriter.bookwriter import (
    BookWriter,
)  # Assuming you've structured your code in separate files
from ai_tools.ai_write_assistent.writer import WriterAssistant


class AIWriterAgent:
    def __init__(self, speak=None):
        """
        Initialize the AI Writer Assistant class, which includes both a `WriterAssistant` and a `BookWriter`.
        """
        self._speak = speak
        self.writer_assistant = WriterAssistant()
        self.book_writer = BookWriter()
        self.logger = logging.getLogger("AIWriterAssistant")

        # Store session context
        self.session_context = {
            "current_story": None,
            "last_task": None,
        }

    async def handle_mode_selection(self):
        """
        Allow the user to select between different modes (Writer Assistant, Book Writer).
        """
        try:
            modes = ["writer", "book", "exit"]
            await self._speak("Please select the mode: writer, book, or exit.")

            mode = await asyncio.to_thread(input, "Mode (writer/book/exit): ")
            mode.strip().lower()
            if mode == "writer":
                await self._handle_writer_mode()
            elif mode == "book":
                await self._handle_book_mode()
            elif mode == "exit":
                await self._speak("Goodbye!")
                return False
            else:
                await self._speak(f"Invalid mode. Please select between {modes}.")
            return True
        except Exception as e:
            await self._speak(f"Error selecting mode: {str(e)}")
            return True

    async def _handle_writer_mode(self):
        """
        Handle story writing tasks using WriterAssistant.
        """
        try:
            await self._speak("You are in Writer mode. What would you like to do?")
            task = await asyncio.to_thread(input, "Task (story/exit): ")

            task.strip().lower()

            if task == "story":
                await self.writer_assistant.create_story()
                await self._speak("Story creation complete.")
            elif task == "exit":
                return
            else:
                await self._speak("Invalid task. Please enter 'story' or 'exit'.")
        except Exception as e:
            await self._speak(f"Error in writer mode: {str(e)}")

    async def _handle_book_mode(self):
        """
        Handle book writing tasks using BookWriter.
        """
        try:
            await self._speak("You are in Book mode. What would you like to do?")
            task = await asyncio.to_thread(input, "Task (create/exit): ")

            task.strip().lower()

            if task == "create":
                await self.book_writer.create_story()
                await self._speak("Book creation complete.")
            elif task == "exit":
                return
            else:
                await self._speak("Invalid task. Please enter 'create' or 'exit'.")
        except Exception as e:
            await self._speak(f"Error in book mode: {str(e)}")


# Example usage
if __name__ == "__main__":
    assistant = AIWriterAgent()

    # Running a loop that allows mode selection and task execution
    loop_running = True
    while loop_running:
        loop_running = asyncio.run(assistant.handle_mode_selection())
