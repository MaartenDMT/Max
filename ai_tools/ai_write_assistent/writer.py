import asyncio

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
    extract_and_save_json,
    process_json_in_chunks,
)
from utils.loggers import LoggerSetup

# Set maximum chunk size (tokens)
MAX_CHUNK_SIZE = 2048  # Adjust this value as needed


class WriterAssistant:
    def __init__(self):
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("WriterAssistant", "writer_assistent.log")

    async def create_story(self, book_description: str, text_content: str) -> str:
        """
        Function to create and generate the story based on provided description and text content.
        """
        # clean_up() # Keep this if you want to clean up previous runs
        self.logger.info("Starting story creation.")

        try:
            if not book_description or not text_content:
                self.logger.error("Book description or text content is missing.")
                return "Error: Book description or text content is missing."

            facts_response = await process_json_in_chunks(get_facts, text_content)
            facts = await extract_and_save_json(
                facts_response, "ai_tools/ai_write_assistent/json/facts.json"
            )
            if not facts:
                self.logger.error("Failed to extract facts.")
                return "Error: Failed to extract facts."
            facts = str(facts)

            agents_to_run = str(await agent_selector(facts)).lower()

            characters_response = await character_generator(facts, book_description)
            characters = await extract_and_save_json(
                characters_response,
                "ai_tools/ai_write_assistent/json/characters.json",
            )
            if not characters:
                self.logger.error("Failed to generate characters.")
                return "Error: Failed to generate characters."
            characters = str(characters)

            plot_response = await plot_generator(facts, characters)
            plot = await extract_and_save_json(
                plot_response, "ai_tools/ai_write_assistent/json/plot.json"
            )
            if not plot:
                self.logger.error("Failed to generate plot.")
                return "Error: Failed to generate plot."
            plot = str(plot)

            # Initialize variables to store outputs
            world, magic_system, weapons_and_artifacts = None, None, None
            creatures_and_monsters, fauna_and_flora, connections, suggestions = (
                None,
                None,
                None,
                None,
            )

            if "world building generator" in agents_to_run:
                world_response = await world_building_generator(facts, plot)
                world = await extract_and_save_json(
                    world_response, "ai_tools/ai_write_assistent/json/world.json"
                )
                if not world:
                    self.logger.error("Failed to generate world-building elements.")
                    return "Error: Failed to generate world-building elements."
                world = str(world)

            if "generate magic system" in agents_to_run:
                magic_response = await generate_magic_system(facts, plot)
                magic_system = await extract_and_save_json(
                    magic_response, "ai_tools/ai_write_assistent/json/magic.json"
                )
                if not magic_system:
                    self.logger.error("Failed to generate magic system.")
                    return "Error: Failed to generate magic system."
                magic_system = str(magic_system)

            if "generate weapons and artifacts" in agents_to_run:
                weapons_response = await generate_weapons_and_artifacts(facts, plot)
                weapons_and_artifacts = await extract_and_save_json(
                    weapons_response, "ai_tools/ai_write_assistent/json/weapons.json"
                )
                if not weapons_and_artifacts:
                    self.logger.error("Failed to generate weapons and artifacts.")
                    return "Error: Failed to generate weapons and artifacts."
                weapons_and_artifacts = str(weapons_and_artifacts)

            if "generate creatures and monsters" in agents_to_run:
                creatures_response = await generate_creatures_and_monsters(facts, plot)
                creatures_and_monsters = await extract_and_save_json(
                    creatures_response,
                    "ai_tools/ai_write_assistent/json/creatures.json",
                )
                if not creatures_and_monsters:
                    self.logger.error("Failed to generate creatures and monsters.")
                    return "Error: Failed to generate creatures and monsters."
                creatures_and_monsters = str(creatures_and_monsters)

            if "generate fauna and flora" in agents_to_run:
                fauna_response = await generate_fauna_and_flora(facts, plot)
                fauna_and_flora = await extract_and_save_json(
                    fauna_response, "ai_tools/ai_write_assistent/json/fauna.json"
                )
                if not fauna_and_flora:
                    self.logger.error("Failed to generate fauna and flora.")
                    return "Error: Failed to generate fauna and flora."
                fauna_and_flora = str(fauna_and_flora)

            if "make connections between plots and characters" in agents_to_run:
                connections_response = await make_connections_between_plots_and_characters(
                    plot, characters
                )
                connections = await extract_and_save_json(
                    connections_response,
                    "ai_tools/ai_write_assistent/json/connections.json",
                )
                if not connections:
                    self.logger.error("Failed to generate plot-character connections.")
                    return "Error: Failed to generate plot-character connections."
                connections = str(connections)

            if "suggestions and thoughts generator" in agents_to_run:
                suggestions_response = await suggestions_and_thoughts_generator(
                    facts, plot, characters
                )
                suggestions = await extract_and_save_json(
                    suggestions_response,
                    "ai_tools/ai_write_assistent/json/suggestions.json",
                )
                if not suggestions:
                    self.logger.error("Failed to generate suggestions and thoughts.")
                    return "Error: Failed to generate suggestions and thoughts."
                suggestions = str(suggestions)

            self.logger.info("Story creation completed successfully.")
            return "Story creation completed successfully. Generated JSON files in ai_tools/ai_write_assistent/json/."

        except Exception as e:
            self.logger.exception(f"An error occurred during story creation: {e}")
            return f"Error during story creation: {str(e)}"


# Example usage (for testing purposes, non-interactive)
if __name__ == "__main__":

    async def test_writer_assistant():
        writer_assistant = WriterAssistant()
        description = "A thrilling detective story set in a futuristic city."
        text = "The neon lights flickered, casting long shadows over the rain-slicked streets. Detective Kaito adjusted his trench coat, the collar pulled high against the biting wind. Another case, another mystery in Neo-Kyoto."
        result = await writer_assistant.create_story(description, text)
        print(f"Story creation result: {result}")

    asyncio.run(test_writer_assistant())
