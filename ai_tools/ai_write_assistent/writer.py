import asyncio
import json
import logging
import re

# Import helper functions
from helpers import clean_up, extract_and_save_json, get_file_contents

# Import the necessary agents
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

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set maximum chunk size (tokens)
MAX_CHUNK_SIZE = 2048  # Adjust this value as needed


class WriterAssistant:
    def __init__(self):
        pass

    def split_text(self, text, max_chunk_size=MAX_CHUNK_SIZE):
        """Split text into chunks suitable for LLM processing."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            estimated_tokens = (len(current_chunk) + len(sentence)) // 4
            if estimated_tokens <= max_chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

                if len(current_chunk) // 4 > max_chunk_size:
                    words = current_chunk.split()
                    sub_chunk = ""
                    for word in words:
                        if (len(sub_chunk) + len(word)) // 4 <= max_chunk_size:
                            sub_chunk += " " + word
                        else:
                            chunks.append(sub_chunk.strip())
                            sub_chunk = word
                    if sub_chunk:
                        chunks.append(sub_chunk.strip())
                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def process_text_in_chunks(self, agent_function, text, *args, **kwargs):
        """Process the text in chunks using the specified agent function."""
        chunks = self.split_text(text)
        results = []

        for idx, chunk in enumerate(chunks):
            logging.info(f"Processing chunk {idx + 1}/{len(chunks)}")
            result = agent_function(chunk, *args, **kwargs)
            if result:
                results.append(result)
            else:
                logging.error(f"Failed to process chunk {idx + 1}")

        combined_result = "\n".join(results)
        return combined_result

    async def create_story(self):
        """Function to create and generate the story."""
        clean_up()
        logging.info("Cleaning up the previous story")

        try:
            user_input_description = input("Enter a description of the book: ")

            if not user_input_description:
                logging.error("Invalid input. Please provide a valid description.")
                return

            book_description = user_input_description
            text_source = "story.txt"
            text = get_file_contents(f"data/{text_source}")

            if not text:
                logging.error(f"Failed to read {text_source}.")
                return

            # 1. Get facts from the pre-story in chunks
            fact_response = self.process_text_in_chunks(get_facts, text)
            facts = extract_and_save_json(fact_response, "json/facts.json")
            if not facts:
                logging.error("Failed to extract facts.")
                return

            facts = str(facts)

            # Use agent_selector to decide which agents to run
            agents_to_run = agent_selector(facts)

            # Initialize variables to store outputs
            characters, plot, world, magic_system, weapons_and_artifacts = (
                None,
                None,
                None,
                None,
                None,
            )
            creatures_and_monsters, fauna_and_flora, connections, suggestions = (
                None,
                None,
                None,
                None,
            )

            # Run the selected agents
            if "character_generator" in agents_to_run:
                characters_response = character_generator(facts, book_description)
                characters = extract_and_save_json(
                    characters_response, "json/characters.json"
                )
                if not characters:
                    logging.error("Failed to generate characters.")
                    return
                characters = str(characters)

            if "plot_generator" in agents_to_run:
                plot_response = plot_generator(facts, characters)
                plot = extract_and_save_json(plot_response, "json/plot.json")
                if not plot:
                    logging.error("Failed to generate plot.")
                    return
                plot = str(plot)

            if "world_building_generator" in agents_to_run:
                world_response = world_building_generator(facts, plot)
                world = extract_and_save_json(world_response, "json/world.json")
                if not world:
                    logging.error("Failed to generate world-building elements.")
                    return
                world = str(world)

            if "generate_magic_system" in agents_to_run:
                magic_response = generate_magic_system(facts, plot)
                magic_system = extract_and_save_json(magic_response, "json/magic.json")
                if not magic_system:
                    logging.error("Failed to generate magic system.")
                    return
                magic_system = str(magic_system)

            if "generate_weapons_and_artifacts" in agents_to_run:
                weapons_response = generate_weapons_and_artifacts(facts, plot)
                weapons_and_artifacts = extract_and_save_json(
                    weapons_response, "json/weapons.json"
                )
                if not weapons_and_artifacts:
                    logging.error("Failed to generate weapons and artifacts.")
                    return
                weapons_and_artifacts = str(weapons_and_artifacts)

            if "generate_creatures_and_monsters" in agents_to_run:
                creatures_response = generate_creatures_and_monsters(facts, plot)
                creatures_and_monsters = extract_and_save_json(
                    creatures_response, "json/creatures.json"
                )
                if not creatures_and_monsters:
                    logging.error("Failed to generate creatures and monsters.")
                    return
                creatures_and_monsters = str(creatures_and_monsters)

            if "generate_fauna_and_flora" in agents_to_run:
                fauna_response = generate_fauna_and_flora(facts, plot)
                fauna_and_flora = extract_and_save_json(
                    fauna_response, "json/fauna.json"
                )
                if not fauna_and_flora:
                    logging.error("Failed to generate fauna and flora.")
                    return
                fauna_and_flora = str(fauna_and_flora)

            if "make_connections_between_plots_and_characters" in agents_to_run:
                connections_response = make_connections_between_plots_and_characters(
                    plot, characters
                )
                connections = extract_and_save_json(
                    connections_response, "json/connections.json"
                )
                if not connections:
                    logging.error("Failed to generate plot-character connections.")
                    return
                connections = str(connections)

            if "suggestions_and_thoughts_generator" in agents_to_run:
                suggestions_response = suggestions_and_thoughts_generator(
                    facts, plot, characters
                )
                suggestions = extract_and_save_json(
                    suggestions_response, "json/suggestions.json"
                )
                if not suggestions:
                    logging.error("Failed to generate suggestions and thoughts.")
                    return
                suggestions = str(suggestions)

            logging.info("Story creation completed successfully.")

        except Exception as e:
            logging.exception(f"An error occurred during story creation: {e}")

    async def handle_user_commands(self):
        """Assistant function to handle user commands."""
        print("Welcome to the AI Book Writer!")

        while True:
            print("\nPlease choose an option:")
            print("story - to create a story")
            print("exit - to exit")

            choice = input("Enter your choice: ").strip()

            if choice.lower() == "story":
                logging.info("User selected to create a story.")
                await self.create_story()
            elif choice.lower() == "exit":
                print("Goodbye!")
                logging.info("Assistant session ended by user.")
                break
            else:
                logging.info("Invalid choice. Please try again.")
                print("Invalid choice. Please enter 'story' or 'exit'.")


# Run the assistant when the script is executed
if __name__ == "__main__":
    agent = WriterAssistant()
    asyncio.run(agent.handle_user_commands())
