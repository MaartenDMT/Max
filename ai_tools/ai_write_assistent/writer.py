import asyncio
from utils.loggers import LoggerSetup

# Import the necessary agents
from ai_tools.ai_write_assistent.agents import (
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

# Import helper functions
from ai_tools.ai_write_assistent.helpers import (
    clean_up,
    extract_and_save_json,
    get_file_contents,
    process_json_in_chunks,
    process_text_in_chunks,
)


# Set maximum chunk size (tokens)
MAX_CHUNK_SIZE = 2048  # Adjust this value as needed


class WriterAssistant:
    def __init__(self):
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("WriterAssistant", "writer_assistent.log")

    async def create_story(self):
        """Function to create and generate the story."""
        # clean_up()
        self.logger.info("Cleaning up the previous story")

        try:
            user_input_description = input("Enter a description of the book: ")

            if not user_input_description:
                description = "description.txt"
                user_input_description = get_file_contents(
                    f"ai_tools/ai_write_assistent/data/{description}"
                )

            book_description = user_input_description
            text_source = "story.txt"
            text = get_file_contents(f"ai_tools/ai_write_assistent/data/{text_source}")

            if not text:
                self.logger.error(f"Failed to read {text_source}.")
                return

            # 1. Get facts from the pre-story in chunks
            fact_response = process_json_in_chunks(get_facts, text)

            if not fact_response:
                self.logger.error("Failed to process json chunks.")
                return

            facts = extract_and_save_json(
                fact_response, "ai_tools/ai_write_assistent/json/facts.json"
            )
            if not facts:
                self.logger.error("Failed to extract facts.")
                return

            facts = str(facts)

            # Use agent_selector to decide which agents to run
            agents_to_run = str(agent_selector(facts)).lower()

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

            characters_response = character_generator(facts, book_description)
            characters = extract_and_save_json(
                characters_response,
                "ai_tools/ai_write_assistent/json/characters.json",
            )
            if not characters:
                self.logger.error("Failed to generate characters.")
                return
            characters = str(characters)

            plot_response = plot_generator(facts, characters)
            plot = extract_and_save_json(
                plot_response, "ai_tools/ai_write_assistent/json/plot.json"
            )
            if not plot:
                self.logger.error("Failed to generate plot.")
                return
            plot = str(plot)

            if "world building generator" in agents_to_run:
                world_response = world_building_generator(facts, plot)
                world = extract_and_save_json(
                    world_response, "ai_tools/ai_write_assistent/json/world.json"
                )
                if not world:
                    self.logger.error("Failed to generate world-building elements.")
                    return
                world = str(world)

            if "generate magic system" in agents_to_run:
                magic_response = generate_magic_system(facts, plot)
                magic_system = extract_and_save_json(
                    magic_response, "ai_tools/ai_write_assistent/json/magic.json"
                )
                if not magic_system:
                    self.logger.error("Failed to generate magic system.")
                    return
                magic_system = str(magic_system)

            if "generate weapons and artifacts" in agents_to_run:
                weapons_response = generate_weapons_and_artifacts(facts, plot)
                weapons_and_artifacts = extract_and_save_json(
                    weapons_response, "ai_tools/ai_write_assistent/json/weapons.json"
                )
                if not weapons_and_artifacts:
                    self.logger.error("Failed to generate weapons and artifacts.")
                    return
                weapons_and_artifacts = str(weapons_and_artifacts)

            if "generate creatures and monsters" in agents_to_run:
                creatures_response = generate_creatures_and_monsters(facts, plot)
                creatures_and_monsters = extract_and_save_json(
                    creatures_response,
                    "ai_tools/ai_write_assistent/json/creatures.json",
                )
                if not creatures_and_monsters:
                    self.logger.error("Failed to generate creatures and monsters.")
                    return
                creatures_and_monsters = str(creatures_and_monsters)

            if "generate fauna and flora" in agents_to_run:
                fauna_response = generate_fauna_and_flora(facts, plot)
                fauna_and_flora = extract_and_save_json(
                    fauna_response, "ai_tools/ai_write_assistent/json/fauna.json"
                )
                if not fauna_and_flora:
                    self.logger.error("Failed to generate fauna and flora.")
                    return
                fauna_and_flora = str(fauna_and_flora)

            if "make connections between plots and characters" in agents_to_run:
                connections_response = make_connections_between_plots_and_characters(
                    plot, characters
                )
                connections = extract_and_save_json(
                    connections_response,
                    "ai_tools/ai_write_assistent/json/connections.json",
                )
                if not connections:
                    self.logger.error("Failed to generate plot-character connections.")
                    return
                connections = str(connections)

            if "suggestions and thoughts generator" in agents_to_run:
                suggestions_response = suggestions_and_thoughts_generator(
                    facts, plot, characters
                )
                suggestions = extract_and_save_json(
                    suggestions_response,
                    "ai_tools/ai_write_assistent/json/suggestions.json",
                )
                if not suggestions:
                    self.logger.error("Failed to generate suggestions and thoughts.")
                    return
                suggestions = str(suggestions)

            self.logger.info("Story creation completed successfully.")

        except Exception as e:
            self.logger.exception(f"An error occurred during story creation: {e}")

    async def handle_user_commands(self):
        """Assistant function to handle user commands."""
        print("Welcome to the AI Book Writer!")

        while True:
            print("\nPlease choose an option:")
            print("story - to create a story")
            print("exit - to exit")

            choice = input("Enter your choice: ").strip()

            if choice.lower() == "story":
                self.logger.info("User selected to create a story.")
                await self.create_story()
            elif choice.lower() == "exit":
                print("Goodbye!")
                self.logger.info("Assistant session ended by user.")
                break
            else:
                self.logger.info("Invalid choice. Please try again.")
                print("Invalid choice. Please enter 'story' or 'exit'.")


# Run the assistant when the script is executed
if __name__ == "__main__":
    agent = WriterAssistant()
    asyncio.run(agent.handle_user_commands())
