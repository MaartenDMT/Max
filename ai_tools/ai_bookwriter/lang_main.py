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


# Function to create and generate the story
async def create_story():

    clean_up()
    logging.info("cleaning up the previous story")

    try:
        # Read user inputs
        user_input_description = input("Enter a description of the book: ")
        user_input_how_many_chapters = input(
            "Enter how many chapters you want the book to have: "
        )

        # Validate user inputs
        if not user_input_description or not user_input_how_many_chapters.isdigit():
            logging.error(
                "Invalid input. Please provide a valid description and chapter count."
            )
            return

        book_description = user_input_description
        book_chapters = int(user_input_how_many_chapters)

        # Read pre-story text
        text_source = "story.txt"
        text = get_file_contents(f"data/{text_source}")
        if not text:
            logging.error(f"Failed to read {text_source}.")
            return

        # 1. Fact-AI getting the facts from the pre-story
        fact_response = get_facts(text)
        facts = extract_and_save_json(fact_response, "json/facts.json")
        if not facts:
            logging.error("Failed to extract facts.")
            fact_response = json_check(fact_response)
            facts = extract_and_save_json(fact_response, "json/facts.json")

        facts = str(facts)

        # 2. Character-AI getting the characters from the facts and book description
        characters_response = character_generator(facts, book_description)
        characters = extract_and_save_json(characters_response, "json/characters.json")
        if not characters:
            logging.error("Failed to generate characters.")
            characters_response = json_check(characters_response)
            characters = extract_and_save_json(
                characters_response, "json/characters.json"
            )
        characters = str(characters)

        # 3. Plot-AI getting the plot from the facts and characters
        plot_response = plot_generator(facts, characters)
        plot = extract_and_save_json(plot_response, "json/plot.json")
        if not plot:
            logging.error("Failed to generate plot.")
            plot_response = json_check(plot_response)
            plot = extract_and_save_json(plot_response, "json/plot.json")
        plot = str(plot)

        # 4. Chapter-AI getting the info from facts, characters, plot, and chapter count
        chapter_response = chapter_outline_generator(
            facts, characters, plot, book_chapters
        )
        chapters_json = extract_and_save_json(chapter_response, "json/chapters.json")
        chapters = chapters_json.get("chapterDescriptions") if chapters_json else None
        if not chapters:
            logging.error("Failed to generate chapter outlines.")
            chapter_response = json_check(chapter_response)
            chapters_json = extract_and_save_json(
                chapter_response, "json/chapters.json"
            )
            chapters = (
                chapters_json.get("chapterDescriptions") if chapters_json else None
            )
        chapters = chapters

        # Additional AI Agents
        theme_response = analyze_theme_and_tone(facts, characters, plot, chapters)
        theme = extract_and_save_json(theme_response, "json/theme.json")
        if not theme:
            logging.error("Failed to analyze theme and tone.")
            theme_response = json_check(theme_response)
            theme = extract_and_save_json(theme_response, "json/theme.json")
        theme = str(theme)

        dialogues_response = generate_dialogues(characters, plot, chapters)
        dialogues = extract_and_save_json(dialogues_response, "json/dialogue.json")
        if not dialogues:
            logging.error("Failed to generate dialogues.")
            dialogues_response = json_check(dialogues_response)
            dialogues = extract_and_save_json(dialogues_response, "json/dialogue.json")
        dialogues = str(dialogues)

        settings_response = generate_settings(facts, plot)
        settings = extract_and_save_json(settings_response, "json/settings.json")
        if not settings:
            logging.error("Failed to generate settings.")
            settings_response = json_check(settings_response)
            settings = extract_and_save_json(settings_response, "json/settings.json")
        settings = str(settings)

        conflict_response = generate_conflicts_and_resolutions(plot, chapters)
        conflict = extract_and_save_json(conflict_response, "json/conflict.json")
        if not conflict:
            logging.error("Failed to generate conflicts and resolutions.")
            conflict_response = json_check(conflict_response)
            conflict = extract_and_save_json(conflict_response, "json/conflict.json")
        conflict = str(conflict)

        developer_response = develop_characters(characters, plot)
        developer = extract_and_save_json(developer_response, "json/developer.json")
        if not developer:
            logging.error("Failed to develop characters.")
            developer_response = json_check(developer_response)
            developer = extract_and_save_json(developer_response, "json/developer.json")
        developer = str(developer)

        genre_response = analyze_genre_and_market(facts, characters, plot)
        genre = extract_and_save_json(genre_response, "json/genre.json")
        if not genre:
            logging.error("Failed to analyze genre and market.")
            genre_response = json_check(genre_response)
            genre = extract_and_save_json(genre_response, "json/genre.json")
        genre = str(genre)

        # 5. Generate and save chapters
        await generate_and_save_chapters(
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


# Function to generate and save all chapters
async def generate_and_save_chapters(
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
    all_chapters = {}
    tasks = []

    for chapter in chapters:
        chapter_number = int(chapter["chapterNumber"])
        current_chapter = chapter["description"]
        task = asyncio.create_task(
            generate_and_save_chapter(
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

    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)

    # Save all chapters to a single JSON file
    os.makedirs("chapters", exist_ok=True)
    filename = "chapters/all_chapters.json"
    try:
        with open(filename, "w") as f:
            json.dump(all_chapters, f, indent=2)
        logging.info(f"All chapters saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save chapters to {filename}: {e}")


# Function to generate and save a single chapter
async def generate_and_save_chapter(
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
    try:
        # Generate chapter content asynchronously
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

        # Extract chapter content from the response
        try:
            # Assuming <chapter> tags are correctly placed
            chapter_text = chapter_content.split("<chapter>")[1].split("</chapter>")[0]
        except IndexError:
            logging.error(f"Invalid chapter format for chapter {chapter_number}.")
            return

        # Parse the chapter text to extract chapter number, title, and content
        lines = chapter_text.strip().split("\n")
        if len(lines) < 3:
            logging.error(f"Insufficient data in chapter {chapter_number}.")
            return

        try:
            chapter_number = lines[0].split(":")[1].strip().strip('"').strip(",")
            chapter_title = lines[1].strip().strip('"').strip(",")
            chapter_content_text = "\n".join(lines[2:]).strip().strip('"')
        except (IndexError, ValueError) as e:
            logging.error(f"Error parsing chapter {chapter_number}: {e}")
            return

        # Create chapter dictionary
        chapter_dict = {
            "chapter_number": chapter_number,
            "title": chapter_title,
            "content": chapter_content_text,
        }

        # Add chapter to all_chapters dictionary in correct order
        all_chapters[f"chapter {chapter_number}"] = chapter_dict
        logging.info(f"Chapter {chapter_number} generated and saved.")

    except asyncio.CancelledError:
        logging.warning(f"Chapter generation for {chapter_number} was cancelled.")
        # Handle task cancellation if needed (e.g., cleanup or retry logic)
    except Exception as e:
        logging.error(f"Failed to generate chapter {chapter_number}: {e}")


# retrieve_info function to use the agent_chain
async def retrieve_info(agent_chain, chat_history, question):
    try:
        query = question
        if not query:
            logging.error("No query provided.")
            return

        # Use the agent_chain directly to handle the query
        result = await agent_chain.ainvoke(input=query)

        response = result.get("output", "No answer found")
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=response))

        if response:
            print("\nRetrieved Information:")
            print(response)
        else:
            logging.error("No information retrieved.")

    except Exception as e:
        logging.exception(f"An error occurred during information retrieval: {e}")


# Assistant function to handle user commands
async def book_assistant():
    print("Welcome to the AI Book Writer!")

    with open("json/urls.json", "r") as file:
        urls = json.load(file)

    documents = get_documents(urls)
    vector_store = create_db(documents)

    # Create initial agent chain
    agent_chain = create_agentchain(vector_store, include_web_search=False)

    chat_history = []

    while True:
        print("\nPlease choose an option:")
        print("story")
        print("Just start chatting")
        print("exit - to exit")

        choice = input("Enter your choice: ").strip()

        if choice == "story":
            logging.info("User selected to create a story.")
            await create_story()
        elif choice == "exit":
            print("Goodbye!")
            logging.info("Assistant session ended by user.")
            break
        else:
            logging.info("User selected to ask questions.")
            await retrieve_info(
                agent_chain, chat_history, choice
            )  # Pass include_web_search flag


# Run the assistant when the script is executed
if __name__ == "__main__":
    asyncio.run(book_assistant())
