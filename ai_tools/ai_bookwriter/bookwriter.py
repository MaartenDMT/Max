import asyncio
import json
import logging
import os

from langchain_core.messages import AIMessage, HumanMessage

from ai_tools.ai_bookwriter.agents import *
from ai_tools.ai_bookwriter.agents import character_generator, json_check
from ai_tools.ai_bookwriter.ai_tools import get_documents  # Add this to load documents
from ai_tools.ai_bookwriter.ai_tools import (  # Add this if you need to use the agent chain; Add this to create the vector store
    create_agentchain,
    create_db,
    retrieve_from_internet,
    retrieve_from_vectorstore,
)
from ai_tools.ai_bookwriter.helpers import (  # add_chapter_to_dict,; parse_chapter,
    clean_up,
    extract_and_save_json,
    get_file_contents,
)

# Set up logging
logging.basicConfig(level=logging.INFO)


class BookWriter:
    def __init__(self):
        self.agent_chain = None
        self.chat_history = []
        self.vector_store = None

    async def create_story(self):
        """
        Function to create and generate the story.
        """
        clean_up()
        logging.info("Cleaning up the previous story")

        try:
            # Read user inputs
            book_description = input("Enter a description of the book: ")
            user_input_how_many_chapters = input(
                "Enter how many chapters you want the book to have: "
            )

            if not book_description or not user_input_how_many_chapters.isdigit():
                logging.error(
                    "Invalid input. Please provide a valid description and chapter count."
                )
                return

            book_chapters = int(user_input_how_many_chapters)
            text_source = "story.txt"
            text = get_file_contents(f"data/{text_source}")

            if not text:
                logging.error(f"Failed to read {text_source}.")
                return

            # Extract facts from the pre-story
            fact_response = get_facts(text)
            facts = extract_and_save_json(fact_response, "json/facts.json")
            if not facts:
                logging.error("Failed to extract facts.")
                fact_response = json_check(fact_response)
                facts = extract_and_save_json(fact_response, "json/facts.json")
            facts = str(facts)

            # Generate characters
            characters_response = character_generator(facts, book_description)
            characters = extract_and_save_json(
                characters_response, "json/characters.json"
            )
            if not characters:
                logging.error("Failed to generate characters.")
                characters_response = json_check(characters_response)
                characters = extract_and_save_json(
                    characters_response, "json/characters.json"
                )
            characters = str(characters)

            # Generate plot
            plot_response = plot_generator(facts, characters)
            plot = extract_and_save_json(plot_response, "json/plot.json")
            if not plot:
                logging.error("Failed to generate plot.")
                plot_response = json_check(plot_response)
                plot = extract_and_save_json(plot_response, "json/plot.json")
            plot = str(plot)

            # Generate chapter outlines
            chapter_response = chapter_outline_generator(
                facts, characters, plot, book_chapters
            )
            chapters_json = extract_and_save_json(
                chapter_response, "json/chapters.json"
            )
            chapters = (
                chapters_json.get("chapterDescriptions") if chapters_json else None
            )
            if not chapters:
                logging.error("Failed to generate chapter outlines.")
                chapter_response = json_check(chapter_response)
                chapters_json = extract_and_save_json(
                    chapter_response, "json/chapters.json"
                )
                chapters = (
                    chapters_json.get("chapterDescriptions") if chapters_json else None
                )

            # Additional AI Agents (theme, dialogues, etc.)
            theme_response = analyze_theme_and_tone(facts, characters, plot, chapters)
            theme = extract_and_save_json(theme_response, "json/theme.json")
            dialogues_response = generate_dialogues(characters, plot, chapters)
            dialogues = extract_and_save_json(dialogues_response, "json/dialogue.json")
            settings_response = generate_settings(facts, plot)
            settings = extract_and_save_json(settings_response, "json/settings.json")
            conflict_response = generate_conflicts_and_resolutions(plot, chapters)
            conflict = extract_and_save_json(conflict_response, "json/conflict.json")
            developer_response = develop_characters(characters, plot)
            developer = extract_and_save_json(developer_response, "json/developer.json")
            genre_response = analyze_genre_and_market(facts, characters, plot)
            genre = extract_and_save_json(genre_response, "json/genre.json")

            # Generate and save chapters
            await self.generate_and_save_chapters(
                facts,
                characters,
                plot,
                chapters,
                theme,
                dialogues,
                settings,
                conflict,
                developer,
                genre,
            )

            logging.info("Story creation completed successfully.")

        except Exception as e:
            logging.exception(f"An error occurred during story creation: {e}")

    async def generate_and_save_chapters(
        self,
        facts,
        characters,
        plot,
        chapters,
        theme,
        dialogues,
        settings,
        conflict,
        developer,
        genre,
    ):
        """
        Function to generate and save all chapters.
        """
        all_chapters = {}
        tasks = []

        for chapter in chapters:
            chapter_number = int(chapter["chapterNumber"])
            current_chapter = chapter["description"]
            task = asyncio.create_task(
                self.generate_and_save_chapter(
                    facts,
                    characters,
                    plot,
                    chapters,
                    theme,
                    dialogues,
                    settings,
                    conflict,
                    developer,
                    genre,
                    current_chapter,
                    chapter_number,
                    all_chapters,
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        os.makedirs("chapters", exist_ok=True)
        filename = "chapters/all_chapters.json"
        try:
            with open(filename, "w") as f:
                json.dump(all_chapters, f, indent=2)
            logging.info(f"All chapters saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save chapters to {filename}: {e}")

    async def generate_and_save_chapter(
        self,
        facts,
        characters,
        plot,
        chapters,
        theme,
        dialogues,
        settings,
        conflict,
        developer,
        genre,
        current_chapter,
        chapter_number,
        all_chapters,
    ):
        """
        Function to generate and save a single chapter.
        """
        try:
            chapter_content = await chapter_generator_async(
                facts,
                characters,
                plot,
                chapters,
                theme,
                dialogues,
                settings,
                conflict,
                developer,
                genre,
                current_chapter,
                chapter_number,
            )

            try:
                chapter_text = chapter_content.split("<chapter>")[1].split(
                    "</chapter>"
                )[0]
            except IndexError:
                logging.error(f"Invalid chapter format for chapter {chapter_number}.")
                return

            lines = chapter_text.strip().split("\n")
            if len(lines) < 3:
                logging.error(f"Insufficient data in chapter {chapter_number}.")
                return

            chapter_number = lines[0].split(":")[1].strip().strip('"').strip(",")
            chapter_title = lines[1].strip().strip('"').strip(",")
            chapter_content_text = "\n".join(lines[2:]).strip().strip('"')

            chapter_dict = {
                "chapter_number": chapter_number,
                "title": chapter_title,
                "content": chapter_content_text,
            }

            all_chapters[f"chapter {chapter_number}"] = chapter_dict
            logging.info(f"Chapter {chapter_number} generated and saved.")

        except asyncio.CancelledError:
            logging.warning(f"Chapter generation for {chapter_number} was cancelled.")
        except Exception as e:
            logging.error(f"Failed to generate chapter {chapter_number}: {e}")

    async def retrieve_info(self, question):
        """
        Function to retrieve information using the agent_chain.
        """
        try:
            if not question:
                logging.error("No query provided.")
                return

            result = await self.agent_chain.ainvoke(input=question)

            response = result.get("output", "No answer found")
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=response))

            if response:
                print("\nRetrieved Information:")
                print(response)
            else:
                logging.error("No information retrieved.")

        except Exception as e:
            logging.exception(f"An error occurred during information retrieval: {e}")

    async def handle_user_commands(self):
        """
        Function to handle user input commands.
        """
        print("Welcome to the AI Book Writer!")

        documents = get_documents("json/urls.json")
        self.vector_store = create_db(documents)
        self.agent_chain = create_agentchain(
            self.vector_store, include_web_search=False
        )

        while True:
            print("\nPlease choose an option:")
            print("story")
            print("Just start chatting")
            print("exit - to exit")

            choice = input("Enter your choice: ").strip()

            if choice == "story":
                logging.info("User selected to create a story.")
                await self.create_story()
            elif choice == "exit":
                print("Goodbye!")
                logging.info("Assistant session ended by user.")
                break
            else:
                logging.info("User selected to ask questions.")
                await self.retrieve_info(choice)


if __name__ == "__main__":
    agent = BookWriter()
    asyncio.run(agent.handle_user_commands())
