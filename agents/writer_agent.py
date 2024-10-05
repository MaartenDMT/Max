import asyncio
import logging

from helpers import extract_and_save_json, get_file_contents

from agents import (
    agent_selector,
    character_generator,
    generate_creatures_and_monsters,
    generate_fauna_and_flora,
    generate_magic_system,
    generate_weapons_and_artifacts,
    get_facts,
    make_connections_between_plots_and_characters,
    plot_generator,
    suggestions_and_thoughts_generator,
    world_building_generator,
)
from ai_tools.ai_bookwriter.bookwriter import (
    BookWriter,
)  # Assuming you've structured your code in separate files
from ai_tools.ai_write_assistent.writer import WriterAssistant


class AIWriterAgent:
    def __init__(self, transcribe=None):
        """
        Initialize the AI Writer Assistant class, which includes both a `WriterAssistant` and a `BookWriter`.
        """
        self.transcribe = transcribe
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

            mode = (
                await asyncio.to_thread(input, "Mode (writer/book/exit): ")
                .strip()
                .lower()
            )

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
            task = await asyncio.to_thread(input, "Task (story/exit): ").strip().lower()

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
            task = (
                await asyncio.to_thread(input, "Task (create/exit): ").strip().lower()
            )

            if task == "create":
                await self.book_writer.create_story()
                await self._speak("Book creation complete.")
            elif task == "exit":
                return
            else:
                await self._speak("Invalid task. Please enter 'create' or 'exit'.")
        except Exception as e:
            await self._speak(f"Error in book mode: {str(e)}")

    async def _speak(self, message):
        """
        Placeholder method for text-to-speech (or printing in this case).
        """
        print(message)

    async def _determine_task(self, query):
        """
        Determine the task the user wants to execute based on their query.
        """
        try:
            if "write" in query or "story" in query:
                await self._handle_writer_mode()
            elif "book" in query:
                await self._handle_book_mode()
            else:
                await self._speak("Sorry, I didn't understand the request.")
        except Exception as e:
            self.logger.error(f"Error determining task: {str(e)}")
            await self._speak(f"Error: {str(e)}")


# Example usage
if __name__ == "__main__":
    assistant = AIWriterAgent()

    # Running a loop that allows mode selection and task execution
    loop_running = True
    while loop_running:
        loop_running = asyncio.run(assistant.handle_mode_selection())
