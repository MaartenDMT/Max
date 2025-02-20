import ollama
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from termcolor import colored

# Load environment variables from .env file
load_dotenv(".env")

model_ = ChatOllama(
    # sam4096/qwen2tools:0.5b
    model="deepseek-r1",
    temperature=0.7,
    num_predict=-1,
)

model = ollama.Client()


def get_facts(text):
    # replace placeholders like {{LONG_TEXT}} with real values
    # because SDK does not su^pport variables

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You will be given a large text from which you need to extract all factual information  and present it in a structured JSON format. Here is the text:
                     
<text>{text}</text>

Your task is to carefully read through this text and identify all factual information contained within it. Factual information includes:

1. Dates and times
2. Names of people, places, or organisationns
3. Numerical data (statistics, measurements, quantities, etc.)
4. Historical events
5. Scientific facts
6. Definition of terms
7. Descriptions of processes or procedures
8. Verifiable claims or statements

Structure you JSON output as follows:

1. Use key-value pairs to represent each piece of factual information
2. Group related facts under common categories
3. Use arrays when multiple related facts are present
4. Nest objects as needed to represent hierachical relationships

Guidelines for handling information:

1. If a fact is uncertain or ambiguous, include it but add a "certainty" field with a value of "low","medium" or "high"
2. If dates are approximate, indicate this in the value (e.g., "circa 1900")
3. If numerical range are given, represent them as such
4. Omit opinions, subjective statements, or unverifiable claims

Before providing your final answer, use <scratchpad> tags to think through the process:

<scratchpad>
1. Identify the main topics or themes in the text
2. List the key categories of factual information present
3. Consider how to best structure this information in JSON format
4. Note any challenge ar ambiguities your encounter 
</scratchpad>

Now, provide your final JSON output containing all the factual information from the text. Enclose your JSON
within <json> tags. Ensure your JSON is properly formatted and valid.

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
        print(chunk)
        if isinstance(chunk, tuple) and chunk[0] == "content":
            content = chunk[1]
            print(colored(content, "green"), end="", flush=True)
            assistant_response += content
    return assistant_response


def character_generator(facts, book_description):
    # Replace placeholders like {{TEXT}} with real values,
    # Because the SDK does not support variables.

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f""" Your are tasked with generating detailed character descriptions based on a gaint text
                        and a book description. Your goals is to create at least 5 unique and well-developed characters
                        that fit both the provided text and the book's overall theme and setting.

First, carefully read and analyze the following text and use it creatively to create characters:

<text> Stay true to, and use the facts provided, the characters should be anchored around three facts
{facts}
</text>

Now, consider the description of the book:
<book_description>
{book_description}
</book_description>

Using the information from both the text and the book description, create at least 5 varied and diverse detailed
fictional character description. Stay away from clichés and repetitive descriptions, make characters exiting and
memorable. Do not use any actual names from the facts. Each character should:

1. Have a unique name that fits the setting and tone of the book
2. Include physical characteristics (age, appearance, etc.)
3. Describe personality traits and quirks
4. provide a brief background or backstory
5. Explain their potential role or significance in the story
6. Incorporate elements from both the provided text and book description

Before writing your final character descriptions, use the <scratchpad> tags to brainstorm and outline your ideas.
Consider how each character can relate to themes, settings, or events mentioned in the text and book description.

<scratchpad>
[Use this space to brainstorm and outline your character ideas]
</scratchpad>

Now, provide your detailed character description in JSON format. Enclose your JSON within <json> tags. the JSON
structure should be and array of character objects, each containing 'name' and 'description' fields be sure to enclose with <json> tags.

<json>
{{
    {{
        "name":"[Character Name]",
        "description": "[Detailed character desciption including physical characteristics, personally traits, background, and potential role in the story]"
    }},
}}
</json>

Ensure that your create at least 5 unique characters, but feel free to generate more if inspired by the text and book description.
Make each character distinct and memorable, with clear connections to the provided materials.""",
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
    # replace placeholders liek {{FACTS}} with real value.
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating a detailed plot for a book based on provided facts and
                        character descriptions. your goal is to wave these elements into a compelling narrative structure.

First, carefullyread and analyze the following facts and use them creatively to create a plot:

<facts> stay true to, and use the facts provided, the plot should be anchored around the facts
{facts}
</facts>

Now, review the character descriptions:
<character_descriptions>
{character_descriptions}
</character_descriptions>

To create a detailed plot:

1. Analyze the facts and character description, looking for potential connections, conflicts, and themes.
2. Determine a central conflict or goals that will drive the plot, based on the provided information.
3. identify a protagonist and, if applicable, an antagonist from the character descriptions.
4. Outline the basic structur of the plot, including:
    a. Exposition (introduction of characters and setting)
    b. Rising action (development of conflicts and relationship)
    c. Climax (the peak of tension or action)
    d. Falling action (events following the climx)
    e. Resolution (how the story concludes)

5. Incorporate the provided facts throughout the plot, ensuring they play significant roles in the story's development.
6. Develop character arcs for the main characters, showing how they change or grow throughout the story.
7. create subplots that intertwine with the main plot, adding depth and complexity to the narrative.
8. consider the pacing of the story, balancing action, dialogue and description.
9. Think about potential plot twists or suprises that could enhance the story while remaining consistent with the provided facts and character descriptions.
10. Ensure that all the major elements introduced in the plot are resolved or adressed by the end of the story.
11. Stay away from clichés and repetitive descriptions, make the plot engaging and memorable and unique.

Present your detailed plot outline as a JSON object with the following structure ensure it is enclose with the <json> tags:

<json>
{{
    "title": "[Provide a working title for the book]",
    "genre": "[Specify the genre based on the plot you've developed]",
    "setting": "[Description the primary setting(s) of the story]",
    "mainCharacters": [
        {{
            "name": "[Character name]",
            "role": "[Character's role in the story]"
        }}
    ],
    "plotSummary": "[Write a brief overview of the entire plot]",
    "plotStructure": {{
        "exposition":"[Describe the exposition]",
        "risingAction": "[Describe the rising action]",
        "climax": "[Describe the rising action]",
        "fallingAction": "[Describe the falling action]",
        "resolution": "[Describe the resolution]"
    }},
    "subplots":[
        {{
            "title":"[Subplot title]",
            "description": "[Brief description of the subplot]"
        }}
    ],
    "characterArcs":[
        {{
            "characters": "[Character Name]",
            "arc": "[Description of the character's development]"
        }}
    ],
    "themes": [
        "[Theme 1]",
        "[Theme 2]",
        "[Theme 3]",
    ],
    "keyPlotPoints" : [
        "[Key plot point 1]",
        "[Key plot point 2]",
        "[Key plot point 3]",
        "[Key plot point 4]",
        "[Key plot point 5]"
    ]
}}
</json>
Ensure that your plot outline is coherent, engaging, and make full use of the provided facts and character descriptions. 
the plot should be detailed enough to serve as a comprehensive guide for writing a full-length novel.""",
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


def chapter_outline_generator(facts, characters, plot, how_many_chapters):
    # replace placeholders liek {{FACTS}} with the real values.

    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating detailed chapter descriptions for a story based on provided facts, 
                        characters, plot and a specified number of chapters. Your goal is to craft enganging, non-cliché chapters outlines
                        that creatively incorporate the given elements.

Here are the inputs you will work with. Use them creatively to create enganging and unique chapter descriptions. Stay away from clinchés and repititve descriptions
and make sure the descriptions are enganging and memorable and unique.

<facts> stay true to the facts provided, chapter outlines should be anchored around the facts
{facts}
</facts>

<characters> stay true to the characters provided, and use them creatively in unique ways.
{characters}
</characters>

<plot> stay true to the plot provided, and use it creatively in unique ways.
{plot}
</plot>

This is exact number of chapters you want to create: {how_many_chapters}

Guidelines for creating detailed chapter descriptions:

1. Each chapter description should be 5-10 sentences long.
2. Incorporate elements from the facts, characters, and plot in unexpected ways.
3. Ensure a logical progression of events throughout the chapters.
4. Create tension, conflict, or character development in each chapter.
5. Avoid clinchés and predictable storylines
6. Use vivid language to set the scene and mood for each chapter.

When using the input information:
- Integrate facts naturally, into the story, don't just list them.
- Develop characters beyond their inital descriptions, showing growth or change.
- Use the plot as general guide. but free to add unexpected twists or subplots.

Output your chapters descriptions as a JSON object in the following format , enclosed within <json> tags:

<json>
{{
    "chapterDescriptions":[
        {{
            "chapterNumber": 1,
            "description": "your detailed description for chapter 1"
        }},
        {{
            "chapterNumber": 2,
            "description": "your detailed description for chapter 2"
        }}
    ]
}}
</json>
               
Remember to create unique and engaging chapter descriptions for each chapter, using the provided inputs creatively and
avoiding clichés. Ensure that each chapter advances the plot, develops the characters, or reveals important information
related to the facts provided.

Return your response as a valid JSON object containing chapter descriptions for the number of chapters specified in the 
<how_many_chapters> and makes sure you enclose it with <json>""",
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


async def chapter_generator_async(
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
):
    message = await model_.ainvoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are a skilled novelist tasked with creating a detailed chapter for a story based on provided information. Your goal is to craft a compelling, full-length chapter that fits seamlessly into the overall narrative while staying true to the established facts, characters, and plot.

You will be given the following information:

<facts> Stay true to the facts provided, the chapters should be anchored around these facts.
{facts}
</facts>

<characters> Stay true to the characters provided, and use them creatively in unique ways.
{characters}
</characters>

<plot> Stay true to the plot provided, and use it creatively in unique ways.
{plot}
</plot>

<chapters> Consider the general structure of the story and the chapters provided for the chapter you are creating.
{chapters}
</chapters>

<theme> Incorporate the identified themes and tones into the chapter.
{theme}
</theme>

<dialogues> Use the generated dialogues to enhance character interactions.
{dialogues}
</dialogues>

<settings> Describe the settings in detail to immerse the reader in the story's world.
{settings}
</settings>

<conflict> Include conflicts and resolutions that contribute to the story's progression.
{conflict}
</conflict>

<developer> Develop character arcs that are meaningful and contribute to the overall narrative.
{developer}
</developer>

<genre> Ensure that the chapter aligns with the identified genre and market analysis.
{genre}
</genre>

<current_chapter> This is the current chapter you are creating.
{current_chapter}
</current_chapter>

<chapter_number>
{chapter_number}
</chapter_number>

Your task is to create a detailed, full-length chapter for the specified chapter number. This chapter should be at least 4000 tokens long and should advance the story while remaining consistent with the overall narrative arc.

Follow these guidelines when crafting the chapter:

1. Begin with a brief outline of the chapter's key events and character interactions.
2. Develop rich, descriptive scenes that immerse the reader in the story's world.
3. Include dialogue that reflects each character's unique voice and personality.
4. Incorporate relevant details from the provided facts to enhance the story's authenticity.
5. Ensure that the chapter's events align with and advance the overall plot.
6. Create tension, conflict, or character development that contributes to the story's progression.
7. End the chapter in a way that entices the reader to continue to the next chapter.

Present your chapter within <chapter> tags. Use the following JSON structure:

<chapter>
"chapter_name": [chapter_name],
"title": "[descriptive chapter title]",
"content": "[full chapter text]"
</chapter>

Remember to stay true to the established facts, characters, and plot points provided. Your chapter should fit seamlessly into the larger narrative while offering a compelling and engaging reading experience.

Aim for a word count of approximately 4000-5000 words to ensure a full-length chapter. Be creative and descriptive, but always maintain consistency with the given story elements.""",
                    }
                ],
            }
        ]
    )
    print(message.content)
    return message.content


# Theme and Tone Analyzer
def analyze_theme_and_tone(facts, characters, plot, chapters):
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with analyzing the themes and tones present in the story's facts, characters, and plot. Your goal is to ensure consistency and depth in the narrative.

First, carefully read and analyze the following facts, characters, plot, and chapters:

<facts>
{facts}
</facts>

<characters>
{characters}
</characters>

<plot>
{plot}
</plot>

<chapters>
{chapters}
</chapters>

To analyze the themes and tones:

1. Identify the primary themes and their sub-themes, considering how they interact and evolve throughout the story.
2. Determine the overall tone and identify variations in tone within different parts of the story.
3. Ensure that the themes and tones are consistent throughout the story, considering emotional arcs and narrative style.
4. Adjust the narrative style and emotional arcs to align with the identified themes and tones, enhancing stylistic elements and voice consistency.
5. Provide chapter-specific adjustments that are contextually relevant, considering conflicts, resolutions, pacing, and structure.
6. Enhance reader engagement by analyzing the reader's emotional response and suggesting ways to improve emotional engagement.

Present your analysis as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "themes": [
        "[Theme 1]",
        "[Theme 2]",
        "[Theme 3]"
    ],
    "subThemes": [
        "[Sub-theme 1]",
        "[Sub-theme 2]"
    ],
    "tone": "[Overall tone of the story]",
    "toneVariations": [
        "[Tone variation in ChapterNumber]",
        "[Tone variation in ChapterNumber]"
    ],
    "narrativeStyle": "[Narrative style that aligns with the themes and tones]",
    "stylisticElements": [
        "[Stylistic element 1]",
        "[Stylistic element 2]"
    ],
    "Adjustments": [
        {{
            "chapter": "ChapterNumber",
            "suggestion": "your detailed suggestion for ChapterNumber"
        }},
        {{
            "chapter": "ChapterNumber",
            "suggestion": "your detailed suggestion for ChapterNumber"
        }}
    ],
    "readerEngagement": [
        {{
            "chapter": "ChapterNumber",
            "suggestion": "your suggestion for enhancing reader engagement in ChapterNumber"
        }},
        {{
            "chapter": "ChapterNumber",
            "suggestion": "your suggestion for enhancing reader engagement in ChapterNumber"
        }}
    ]
}}
</json>
Ensure that your analysis is detailed and provides clear guidance for maintaining consistency and depth in the narrative.""",
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


# Dialogue Generator
def generate_dialogues(characters, plot, chapters):
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with creating natural and engaging key dialogues for the characters. Your goal is to reflect each character's personality, background, and relationships, while also aligning with the plot and chapter contexts.

First, carefully read and analyze the following character descriptions, plot, and chapters:

<characters>
{characters}
</characters>

<plot>
{plot}
</plot>

<chapters>
{chapters}
</chapters>

To generate key dialogues:

1. Review the character profiles to understand their personalities, backgrounds, and relationships.
2. Consider the plot and chapter contexts to ensure dialogues are relevant and contribute to the story's progression.
3. Create dialogues that reflect each character's unique voice and manner of speaking.
4. Ensure that the dialogues are natural and contribute to the development of the plot and character relationships.
5. Include a variety of dialogue types, such as conversations, monologues, and exchanges.
6. You can have multiple key dialogues for your characters.

Present your dialogues as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "dialogues": [
        {{
            "character": "[Character name]",
            "dialogue": "[Character's dialogue]"
            "chapter": [Chapter nr]
        }}
    ]
}}
</json>
Ensure that your dialogues are engaging and accurately reflect each character's personality and role in the story, while also being contextually relevant to the plot and chapters.""",
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


# Setting and World-Building Agent
def generate_settings(facts, plot, debug=True):
    """
    Generate detailed and immersive settings for the story based on provided facts and plot.

    Args:
        facts (str): The factual background of the story.
        plot (str): The plot outline for the story.
        debug (bool): Whether to print debug information. Default is False.

    Returns:
        str: A JSON-formatted string with the generated settings.
    """
    # Ensure the inputs are strings
    if not isinstance(facts, str) or not isinstance(plot, str):
        raise ValueError("Both 'facts' and 'plot' must be strings.")

    # Prepare the prompt for the model
    prompt = f"""
    You are tasked with creating detailed and immersive settings for the story. Your goal is to generate descriptions of locations, cultures, and environments that are integral to the plot and character development.

    First, carefully read and analyze the following facts and plot:

    <facts>
    {facts}
    </facts>

    <plot>
    {plot}
    </plot>

    To generate settings:

    1. Identify the key locations and environments that are central to the plot.
    2. Create detailed descriptions of each setting, including physical characteristics, cultural aspects, and any relevant historical or environmental factors.
    3. Ensure that the settings are immersive and contribute to the overall atmosphere and tone of the story.
    4. Integrate the settings with the plot and character development, ensuring they play a significant role in the narrative.

    Use the scratchpad to brainstorm about your settings.

    <scratchpad>
        1. 
        2.
        3.
    </scratchpad>

    Present your settings as a JSON object with the following structure, enclosed with the <json> tags:

    <json>
    {{
        "settings": [
            {{
                "location": "[Location name]",
                "description": "[Detailed description of the location]"
            }}
        ]
    }}
    </json>
    Ensure that your settings are detailed and contribute to the overall depth and richness of the story.
    """

    try:
        # Invoke the model with the prompt
        response = model_.invoke(
            input=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )

        # Process the response from the model
        assistant_response = ""
        for chunk in response:
            if isinstance(chunk, tuple) and chunk[0] == "content":
                content = chunk[1]
                if debug:
                    print(colored(content, "blue"), end="", flush=True)
                assistant_response += content

        # Validate and return JSON response
        if "<json>" in assistant_response and "</json>" in assistant_response:
            json_response = (
                assistant_response.split("<json>")[1].split("</json>")[0].strip()
            )
            try:
                json.loads(json_response)  # Validate JSON structure
                return json_response
            except json.JSONDecodeError:
                print("Generated JSON is not valid.")
                return ""
        else:
            print("No JSON found in the response.")
            return ""

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


# Conflict and Resolution Agent
def generate_conflicts_and_resolutions(plot, chapters):
    # Implement conflict and resolution generation logic
    # Introduce conflicts and devise resolutions
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with ensuring that each chapter and the overall story have well-defined conflicts and satisfying resolutions. Your goal is to analyze the plot and chapters to introduce conflicts and devise resolutions that drive the narrative forward.

First, carefully read and analyze the following plot and chapters:

<plot>
{plot}
</plot>

<chapters>
{chapters}
</chapters>

To generate conflicts and resolutions:

1. Identify the main conflicts in the plot and each chapter.
2. Ensure that the conflicts are well-defined and contribute to the development of the story.
3. Devise satisfying resolutions for each conflict, ensuring they align with the overall narrative and character arcs.
4. Ensure that the resolutions provide closure and contribute to the overall progression of the story.

Present your conflicts and resolutions as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "conflicts": [
        {{
            "chapter": "[Chapter number]",
            "conflict": "[Description of the conflict]"
        }}
    ],
    "resolutions": [
        {{
            "chapter": "[Chapter number]",
            "resolution": "[Description of the resolution]"
        }}
    ]
}}
</json>
Ensure that your conflicts and resolutions are well-defined and contribute to the overall development of the story.""",
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


# Editing and Proofreading Agent
def edit_and_proofread(chapters):
    # Implement editing and proofreading logic
    # Provide suggestions for improvements and corrections
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with reviewing the generated content for grammatical errors, continuity issues, and stylistic consistency. Your goal is to provide suggestions for improvements and corrections to enhance the quality of the final manuscript.

First, carefully read and analyze the following chapters:

<chapters>
{chapters}
</chapters>

To edit and proofread:

1. Review each chapter for grammatical errors, spelling mistakes, and punctuation issues.
2. Ensure that the narrative flows smoothly and maintains continuity throughout the chapters.
3. Check for stylistic consistency, ensuring that the tone and voice remain consistent.
4. Provide suggestions for improvements and corrections to enhance the overall quality of the manuscript.

Present your edits and proofreading suggestions as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "edits": [
        {{
            "chapter": "[Chapter number]",
            "suggestions": "[List of suggestions for improvements and corrections]"
        }}
    ]
}}
</json>
Ensure that your suggestions are clear and actionable, contributing to the overall quality and readability of the manuscript.""",
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


# Character Development Agent
def develop_characters(characters, plot):
    # Implement character development logic
    # Ensure each character's arc is meaningful and contributes to the narrative
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with deepening character development throughout the story. Your goal is to ensure that each character's arc is meaningful and contributes to the overall narrative, including backstories, motivations, and growth.

First, carefully read and analyze the following characters and plot:

<characters>
{characters}
</characters>

<plot>
{plot}
</plot>

To develop characters:

1. Review each character's profile to understand their backstory, motivations, and role in the plot.
2. Ensure that each character's arc is meaningful and contributes to the overall narrative.
3. Develop backstories, motivations, and growth for each character, ensuring they align with the plot and contribute to the story's development.
4. Ensure that each character's development is consistent and logical, providing depth and complexity to the narrative.
5. Do not add extra characters, use the given characters.

Present your character development as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "characterDevelopment": [
        {{
            "character": "[Character name]",
            "backstory": "[Description of the character's backstory]"
            "arc": "[Description of the character's development]"
            "motivation": "[Description of the character's motivation]"
            "growth": "[Description of the character's growth]"
            "developmental milestones": [
                {{
                "event": "[Event name]",
                "impact":"[Description of the event's impact]"
                "contribution": "[Description of the event's contribution to the plot]"
                }}
            ]
        }}
    ]
}}
</json>
Ensure that your character development is detailed and contributes to the overall depth and richness of the story.""",
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


# Genre and Market Analysis Agent
def analyze_genre_and_market(facts, characters, plot):
    # Implement genre and market analysis logic
    # Suggest adjustments to align with market trends
    message = model_.invoke(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are tasked with analyzing the story's genre and potential market appeal. Your goal is to suggest adjustments to make the story more appealing to specific audiences and align with current market trends.

First, carefully read and analyze the following facts, characters, and plot:

<facts>
{facts}
</facts>

<characters>
{characters}
</characters>

<plot>
{plot}
</plot>

To analyze genre and market:

1. Identify the primary genre of the story based on the facts, characters, and plot.
2. Analyze the potential market appeal of the story, considering current trends and audience preferences.
3. Suggest adjustments to the story to make it more appealing to specific audiences and align with market trends.
4. Ensure that the adjustments are consistent with the overall narrative and character development.

Present your genre and market analysis as a JSON object with the following structure, enclosed with the <json> tags:

<json>
{{
    "genre": "[Primary genre of the story]",
    "marketAnalysis": "[Analysis of the story's potential market appeal]",
    "adjustments": "[Suggestions for adjustments to align with market trends]"
}}
</json>
Ensure that your analysis is detailed and provides clear guidance for making the story more appealing to specific audiences and aligning with market trends.""",
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


import json

from termcolor import colored


def json_check(text):
    """
    Check if the given text is in JSON format by querying a model.

    Args:
        text (str): The text to be checked for JSON format.

    Returns:
        str: The response from the model indicating whether the text is in JSON format.
    """
    # Ensure the text input is safely handled
    if not isinstance(text, str):
        raise ValueError("Input text must be a string.")

    # Prepare the prompt for the model
    prompt = f"""
    You are tasked with checking if the text is in JSON format.

    First, carefully check if <json> tags exist in the text.
    Then, validate the JSON structure to ensure it is valid.

    <text>
    {text}
    </text>

    If valid, return <json> <text> </json>.
    Otherwise, return an adjusted JSON structure using the format below:

    <json>
    [Adjusted JSON structure]
    </json>
    """

    try:
        # Invoke the model with the prompt
        response = model_.invoke(
            input=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )

        # Process the response from the model
        assistant_response = ""
        for chunk in response:
            if isinstance(chunk, tuple) and chunk[0] == "content":
                content = chunk[1]
                assistant_response += content

        return assistant_response

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


# client_openai = AsyncOpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY")
# )


# async def text_to_speech(text, chapter_name):
#     response = await client_openai.audio.speech.create(
#         model="tts-1",  # can be tts-1 or tts-1-hd (twice the price)
#         voice="alloy",
#         input=text,
#     )
#     with open(f"{chapter_name}.mp3", "wb") as file:
#         for chunk in response.iter_bytes():
#             file.write(chunk)
