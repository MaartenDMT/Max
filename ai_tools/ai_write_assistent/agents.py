import json
import re

try:
    import ollama  # optional
except Exception:  # pragma: no cover - optional dep
    ollama = None
from dotenv import load_dotenv

try:
    from langchain_ollama import ChatOllama  # optional
except Exception:  # pragma: no cover - optional dep
    ChatOllama = None
try:
    from termcolor import colored  # optional
except Exception:  # pragma: no cover - optional dep
    def colored(text, *_, **__):
        return text

# Load environment variables from .env file
load_dotenv(".env")

model_ = (
    ChatOllama(
        model="llama3.1",
        temperature=0.5,
        num_predict=-1,
    )
    if ChatOllama is not None
    else None
)

model = ollama.Client() if (ollama is not None and hasattr(ollama, "Client")) else None


def get_facts(text):
    # Replace placeholders like {{LONG_TEXT}} with real values
    if model_ is None:
        return "<json>{}\n</json>"
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You will be given a large text from which you need to extract all factual information and present it in a structured JSON format. Here is the text:

<text>{text}</text>

Your task is to carefully read through this text and identify all factual information contained within it. Factual information includes:

1. Dates and times
2. Names of people, places, or organizations
3. Numerical data (statistics, measurements, quantities, etc.)
4. Historical events
5. Scientific facts
6. Definitions of terms
7. Descriptions of processes or procedures
8. Verifiable claims or statements

Structure your JSON output as follows:

1. Use key-value pairs to represent each piece of factual information.
2. Group related facts under common categories.
3. Use arrays when multiple related facts are present.
4. Nest objects as needed to represent hierarchical relationships.

Guidelines for handling information:

1. If a fact is uncertain or ambiguous, include it but add a "certainty" field with a value of "low", "medium", or "high".
2. If dates are approximate, indicate this in the value (e.g., "circa 1900").
3. If numerical ranges are given, represent them as such.
4. Omit opinions, subjective statements, or unverifiable claims.

Before providing your final answer, use <scratchpad> tags to think through the process:

<scratchpad>
1. Identify the main topics or themes in the text.
2. List the key categories of factual information present.
3. Consider how to best structure this information in JSON format.
4. Note any challenges or ambiguities you encounter.
</scratchpad>


Now, provide your final JSON output containing all the factual information from the text. Do not use // to write comments.
Enclose your JSON within <json> tags. Ensure your JSON is properly formatted and valid, be sure to double check it. Do not include the <scratchpad> in your final answer.

<json>
[your JSON output here]
</json>""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "green"), end="", flush=True)
            assistant_response += content
    return assistant_response


def character_generator(facts, book_description):
    if model_ is None:
        return "<json>[]</json>"
    # Replace placeholders like {{TEXT}} with real values

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with generating detailed character descriptions based on a large text and a book description. Your goal is to create at least 5 unique and well-developed characters that fit both the provided text and the book's overall theme and setting.

First, carefully read and analyze the following text and use it creatively to create characters:

<text>Stay true to and use the facts provided; the characters should be anchored around three facts.
{facts}
</text>

Now, consider the description of the book:

<book_description>
{book_description}
</book_description>

Using the information from both the text and the book description, create at least 5 varied and diverse detailed fictional character descriptions. Stay away from clichés and repetitive descriptions; make characters exciting and memorable. Do not use any actual names from the facts. Each character should:

1. Have a unique name that fits the setting and tone of the book.
2. Include physical characteristics (age, appearance, etc.).
3. Describe personality traits and quirks.
4. Provide a brief background or backstory.
5. Explain their potential role or significance in the story.
6. Incorporate elements from both the provided text and book description.

Now, provide your detailed character descriptions in JSON format. Enclose your JSON within <json> tags. The JSON structure should be an array of character objects, each containing 'name' and 'description' fields. Be sure to enclose it with <json> tags.

<json>
[
    {{
        "name": "[Character Name]",
        "description": "[Detailed character description including physical characteristics, personality traits, background, and potential role in the story]"
    }}
]
</json>

Ensure that you create at least 5 unique characters, but feel free to generate more if inspired by the text and book description.
Make each character distinct and memorable, with clear connections to the provided materials.
Ensure your JSON is properly formatted and valid, be sure to double check it. After the </json> tag, do not write anything else.
""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "yellow"), end="", flush=True)
            assistant_response += content
    return assistant_response


def plot_generator(facts, character_descriptions):
    # Replace placeholders like {{FACTS}} with real values
    if model_ is None:
        return "<json>{}</json>"

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating a detailed plot for a book based on provided facts and character descriptions. Your goal is to weave these elements into a compelling narrative structure.

First, carefully read and analyze the following facts and use them creatively to create a plot:

<facts>Stay true to and use the facts provided; the plot should be anchored around the facts.
{facts}
</facts>

Now, review the character descriptions:

<character_descriptions>
{character_descriptions}
</character_descriptions>

To create a detailed plot:

1. Analyze the facts and character descriptions, looking for potential connections, conflicts, and themes.
2. Determine a central conflict or goal that will drive the plot, based on the provided information.
3. Identify a protagonist and, if applicable, an antagonist from the character descriptions.
4. Outline the basic structure of the plot, including:
    a. Exposition (introduction of characters and setting)
    b. Rising action (development of conflicts and relationships)
    c. Climax (the peak of tension or action)
    d. Falling action (events following the climax)
    e. Resolution (how the story concludes)

5. Incorporate the provided facts throughout the plot, ensuring they play significant roles in the story's development.
6. Develop character arcs for the main characters, showing how they change or grow throughout the story.
7. Create subplots that intertwine with the main plot, adding depth and complexity to the narrative.
8. Consider the pacing of the story, balancing action, dialogue, and description.
9. Think about potential plot twists or surprises that could enhance the story while remaining consistent with the provided facts and character descriptions.
10. Ensure that all the major elements introduced in the plot are resolved or addressed by the end of the story.
11. Stay away from clichés and repetitive descriptions; make the plot engaging, memorable, and unique.

Present your detailed plot outline as a JSON object with the following structure. Ensure it is enclosed within the <json> tags:

<json>
{{
    "title": "[Provide a working title for the book]",
    "genre": "[Specify the genre based on the plot you've developed]",
    "setting": "[Describe the primary setting(s) of the story]",
    "mainCharacters": [
        {{
            "name": "[Character name]",
            "role": "[Character's role in the story]"
        }}
    ],
    "plotSummary": "[Write a brief overview of the entire plot]",
    "plotStructure": {{
        "exposition": "[Describe the exposition]",
        "risingAction": "[Describe the rising action]",
        "climax": "[Describe the climax]",
        "fallingAction": "[Describe the falling action]",
        "resolution": "[Describe the resolution]"
    }},
    "subplots": [
        {{
            "title": "[Subplot title]",
            "description": "[Brief description of the subplot]"
        }}
    ],
    "characterArcs": [
        {{
            "character": "[Character Name]",
            "arc": "[Description of the character's development]"
        }}
    ],
    "themes": [
        "[Theme 1]",
        "[Theme 2]",
        "[Theme 3]"
    ],
    "keyPlotPoints": [
        "[Key plot point 1]",
        "[Key plot point 2]",
        "[Key plot point 3]",
        "[Key plot point 4]",
        "[Key plot point 5]"
    ]
}}
</json>

Ensure that your plot outline is coherent, engaging, and makes full use of the provided facts and character descriptions.
The plot should be detailed enough to serve as a comprehensive guide for writing a full-length novel.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "blue"), end="", flush=True)
            assistant_response += content
    return assistant_response


def world_building_generator(facts, plot):
    # Generate detailed world-building elements such as geography, history, cultures, and societies
    if model_ is None:
        return "<json>{}</json>"

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating an immersive world for the story, including geography, history, cultures, and societies. Your goal is to enrich the narrative by providing detailed world-building elements that integrate seamlessly with the plot.

First, carefully read and analyze the following facts and plot:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

To generate the world-building elements:

1. Develop the geography of the world, including continents, countries, cities, and natural landmarks.
2. Outline the history of the world, highlighting significant events that shape the current setting.
3. Describe the various cultures and societies, including customs, traditions, and social structures.
4. Explain how the geography and history influence the plot and characters.
5. Ensure that all elements are cohesive and enhance the overall narrative.

Present your world-building elements as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "geography": {{
        "continents": [
            {{
                "name": "[Continent Name]",
                "description": "[Description of the continent]"
            }}
        ],
        "countries": [
            {{
                "name": "[Country Name]",
                "description": "[Description of the country]",
                "continent": "[Continent Name]"
            }}
        ],
        "cities": [
            {{
                "name": "[City Name]",
                "description": "[Description of the city]",
                "country": "[Country Name]"
            }}
        ],
        "landmarks": [
            {{
                "name": "[Landmark Name]",
                "description": "[Description of the landmark]",
                "location": "[Geographical location]"
            }}
        ]
    }},
    "history": [
        {{
            "era": "[Historical Era]",
            "events": [
                {{
                    "name": "[Event Name]",
                    "description": "[Description of the event]",
                    "impact": "[Impact on the world and plot]"
                }}
            ]
        }}
    ],
    "cultures": [
        {{
            "name": "[Culture Name]",
            "description": "[Description of the culture]",
            "societyStructure": "[Details about social hierarchy, governance, etc.]",
            "traditions": "[Cultural traditions and customs]"
        }}
    ]
}}
</json>
Ensure that your world-building elements are detailed and contribute to the depth and richness of the story.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "cyan"), end="", flush=True)
            assistant_response += content
    return assistant_response


def generate_magic_system(facts, plot):
    # Create a magic system that fits within the world and plot
    if model_ is None:
        return "<json>{}</json>"

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating a detailed magic system for the story, based on the provided facts and plot. Your goal is to design a unique and coherent magic system that enhances the world-building and contributes to the narrative.

First, carefully read and analyze the following facts and plot:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

To generate the magic system:

1. Define the fundamental principles and rules that govern magic in this world.
2. Describe how magic is learned, accessed, and used by characters.
3. Explain any limitations, costs, or consequences associated with using magic.
4. Explore how magic influences society, culture, and the environment in the story.
5. Ensure that the magic system is integrated with the plot and character development.

Present your magic system as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "magicSystem": {{
        "principles": "[Description of the fundamental principles of magic]",
        "access": "[Explanation of how magic is accessed and learned]",
        "limitations": "[Details of limitations and consequences of using magic]",
        "influence": "[Description of how magic influences society and the environment]",
        "integration": "[Explanation of how the magic system integrates with the plot and characters]"
    }}
}}
</json>

Ensure that your magic system is unique, coherent, and contributes to the depth and richness of the story.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "magenta"), end="", flush=True)
            assistant_response += content
    return assistant_response


def generate_weapons_and_artifacts(facts, plot):
    # Create unique weapons and artifacts that fit within the world and plot

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with designing unique weapons and artifacts for the story, based on the provided facts and plot. Your goal is to create items that are significant to the characters and the narrative.

First, carefully read and analyze the following facts and plot:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

To generate weapons and artifacts:

1. Create detailed descriptions of unique weapons and artifacts, including their appearance, abilities, and history.
2. Explain the significance of each item to the characters and the plot.
3. Ensure that the items fit logically within the world's technology level and magic system (if applicable).
4. Incorporate any cultural or historical relevance to enhance their importance in the story.

Present your weapons and artifacts as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "weaponsAndArtifacts": [
        {{
            "name": "[Item Name]",
            "type": "[Weapon or Artifact]",
            "description": "[Detailed description of the item]",
            "abilities": "[Special abilities or properties]",
            "history": "[Background and significance in the story]",
            "owner": "[Character associated with the item]"
        }},
    ]
}}
</json>

Ensure that your weapons and artifacts are unique and contribute meaningfully to the plot and character development.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "yellow"), end="", flush=True)
            assistant_response += content
    return assistant_response


def generate_creatures_and_monsters(facts, plot):
    # Create unique creatures and monsters for the story

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with designing unique creatures and monsters for the story, based on the provided facts and plot. Your goal is to enrich the world with interesting fauna that can influence events in the narrative.

First, carefully read and analyze the following facts and plot:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

To generate creatures and monsters:

1. Create detailed descriptions of unique creatures and monsters, including their appearance, behaviors, habitats, and abilities.
2. Explain how each creature interacts with the environment and characters.
3. Ensure that the creatures fit within the world's ecology and contribute to the atmosphere and challenges within the story.

Present your creatures and monsters as a JSON object with the following structure, enclosed with the <json> tags:

<json>
[
    {{
        "name": "[Creature Name]",
        "description": "[Detailed description of the creature]",
        "habitat": "[Natural habitat]",
        "abilities": "[Special abilities or traits]",
        "roleInStory": "[How the creature influences the plot or characters]"
    }}
]
</json>

Ensure that you create at least 5 unique creatures, but feel free to generate more if inspired by the facts and plot. Make sure each creature is distinct and well-connected to the provided materials.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "green"), end="", flush=True)
            assistant_response += content
    return assistant_response


def generate_fauna_and_flora(facts, plot):
    # Create unique fauna and flora for the story's world

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating unique fauna and flora for the story's world, based on the provided facts and plot. Your goal is to develop plants and animals that add depth to the world-building.

First, carefully read and analyze the following facts and plot:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

To generate fauna and flora:

1. Create detailed descriptions of unique plants and animals, including their appearance, habitats, and uses.
2. Explain how these species interact with the environment and the characters.
3. Consider any ecological relationships and how they affect the world's balance.

Present your fauna and flora as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "faunaAndFlora": [
        {{
            "name": "[Species Name]",
            "type": "[Fauna or Flora]",
            "description": "[Detailed description of the species]",
            "habitat": "[Natural habitat]",
            "uses": "[Practical uses or significance]",
            "roleInStory": "[How the species influences the plot or characters]"
        }},
    ]
}}
</json>

Ensure that your fauna and flora are unique and contribute to the richness of the world-building.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "cyan"), end="", flush=True)
            assistant_response += content
    return assistant_response


def make_connections_between_plots_and_characters(plot, characters):
    # Analyze and enhance connections between plots and characters

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with analyzing and enhancing the connections between the plot and characters. Your goal is to ensure that each character is meaningfully integrated into the narrative and that their actions influence the plot's progression.

First, carefully read and analyze the following plot and character descriptions:

<plot>
{plot}
</plot>

<characters>
{characters}
</characters>

To make connections:

1. Identify how each character contributes to the central plot and subplots.
2. Strengthen relationships and interactions between characters to enhance the narrative.
3. Ensure that character motivations align with their actions within the plot.
4. Introduce any additional connections or conflicts that add depth to the story.

Present your analysis and enhancements as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "plotCharacterConnections": [
        {{
            "character": "[Character Name]",
            "contributions": "[How the character contributes to the plot]",
            "relationships": "[Key relationships with other characters]",
            "conflicts": "[Conflicts the character faces]",
            "development": "[How the character evolves throughout the plot]"
        }},
    ]
}}
</json>

Ensure that your connections enhance the cohesiveness of the story and deepen the reader's engagement with the characters.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "magenta"), end="", flush=True)
            assistant_response += content
    return assistant_response


def suggestions_and_thoughts_generator(facts, plot, characters):
    # Provide suggestions and thoughts to improve the story

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with providing suggestions and thoughts to improve the story, based on the provided facts, plot, and characters. Your goal is to offer constructive feedback and creative ideas that enhance the narrative.

First, carefully read and analyze the following:

<facts>
{facts}
</facts>

<plot>
{plot}
</plot>

<characters>
{characters}
</characters>

To generate suggestions and thoughts:

1. Identify areas where the story could be strengthened, such as plot holes, pacing issues, or character inconsistencies.
2. Offer creative ideas for plot twists, character development, or thematic depth.
3. Provide general feedback on how to enhance the story's engagement and originality.

Present your suggestions and thoughts as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "suggestionsAndThoughts": [
        {{
            "area": "[Plot/Character/Theme]",
            "suggestion": "[Detailed suggestion or thought]"
        }},
    ]
}}
</json>

Ensure that your feedback is constructive and aimed at improving the overall quality of the story.""",
                    }
                ],
            }
        ]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "blue"), end="", flush=True)
            assistant_response += content
    return assistant_response


def agent_selector(facts):
    """
    Analyzes the provided facts and decides which agents to run based on the content.

    Returns a list of agent names to run.
    """
    # Prepare the prompt for the model to decide which agents to run
    prompt = f"""
    You are an assistant that decides which agents to run based on the provided facts.

    The available agents are:

    - world building generator
    - generate magic system
    - generate weapons and artifacts
    - generate creatures and monsters
    - generate fauna and flora
    - make connections between plots and characters
    - suggestions and thoughts generator

    You must choose only from the above agents.

    Based on the following facts, decide which agents should be run to generate appropriate content.
    Only return the exact agent names that are listed above. Do not include any names that are not on this list.

    <facts>
    {facts}
    </facts>

    Provide your answer as a JSON array of agent names (only from the list above) do not use names coming from the facts, enclosed with the <json> tags:

    <json>
    [agents]
    </json>
    """

    # Invoke the model with the prompt
    message = model_.invoke(
        input=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    )

    assistant_response = ""
    for chunk in message:
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            assistant_response += content

    # Extract the JSON array of agent names
    try:
        json_match = re.search(r"<json>(.*?)</json>", assistant_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            agent_list = json.loads(json_str)
            print(colored(agent_list, "blue"), end="", flush=True)
            return agent_list
        else:
            print("Error: No valid JSON found in the assistant's response.")
            return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from response: {e}")
        return []
    except Exception as e:
        print(f"Error parsing JSON from response: {e}")
        return []


# Existing functions (e.g., chapter_outline_generator, analyze_theme_and_tone, etc.) remain unchanged or can be modified similarly to integrate with the new content.

# Don't forget to import any required modules at the beginning of your script.

# Example usage:
# facts = get_facts(your_text)
# characters = character_generator(facts, book_description)
# plot = plot_generator(facts, characters)
# world = world_building_generator(facts, plot)
# magic_system = generate_magic_system(facts, plot)
# weapons_and_artifacts = generate_weapons_and_artifacts(facts, plot)
# creatures_and_monsters = generate_creatures_and_monsters(facts, plot)
# fauna_and_flora = generate_fauna_and_flora(facts, plot)
# connections = make_connections_between_plots_and_characters(plot, characters)
# suggestions = suggestions_and_thoughts_generator(facts, plot, characters)
