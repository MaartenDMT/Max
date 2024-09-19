import asyncio
import json
import os

from helpers import extract_and_save_json, get_file_contents

from agents import chapter_generator_async  # text_to_speech
from agents import (
    chapter_outline_generator,
    character_generator,
    get_facts,
    plot_generator,
)
from ai_tools import *

# Read the pre-story text
text_source = "story.txt"
user_input_description = input("Enter a description of the book: ")
user_input_how_many_chapters = input(
    "Enter how many chapters you want the book to have: "
)

book_description = user_input_description
book_chapters = user_input_how_many_chapters

text = get_file_contents(f"data/{text_source}")

# 1. fact-AI getting the facts from the pre-story
fact_response = get_facts(text)

# Save the fact to a JSON file
facts = str(extract_and_save_json(fact_response, "json/facts.json"))

# 2. character-AI getting the characters from the facts made from fact-AI and the book-description
characters_response = character_generator(facts, book_description)

# Save the characters to a JSON File
characters = str(extract_and_save_json(characters_response, "json/characters.json"))

# 3. plot-AI getting the plot from the fact-AI and the character-AI
plot_response = plot_generator(facts, characters)

# save the plot to a JSON File
plot = str(extract_and_save_json(plot_response, "json/plot.json"))

# 4. Chapter-AI getting the info frm: facts-AI, characters-AI, plot-AI aswell the amount of chapters
chapter_response = chapter_outline_generator(facts, characters, plot, book_chapters)

# Save the chapters to a JSON File
chapters = (extract_and_save_json(chapter_response, "json/chapters.json"))[
    "chapterDescriptions"
]

# print(f"here are the chapters descriptions for your book: {chapters}")


# 5. create the story using facts, character plot and chapters.
async def generate_and_save_chapters(facts, character, plot, chapters):
    all_chapters = {}
    tasks = []

    for chapter in chapters:
        print(f"generating chapter {chapter['chapterNumber']}")
        chapter_number = chapter["chapterNumber"]
        current_chapter = chapter["description"]
        task = asyncio.create_task(
            generate_and_save_chapter(
                facts,
                character,
                plot,
                chapters,
                current_chapter,
                chapter_number,
                all_chapters,
            )
        )
        tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

    # Save all chapters to a single JSON FIle
    os.makedirs("chapters", exist_ok=True)
    filename = "chapters/all_chapters.json"
    with open(filename, "w") as f:
        json.dump(all_chapters, f, indent=2)
    print(f"all chapters saved to {filename}")


async def generate_and_save_chapter(
    facts, characters, plot, chapters, current_chapter, chapter_number, all_chapters
):
    chapter_content = await chapter_generator_async(
        facts, characters, plot, chapters, current_chapter, chapter_number
    )

    # Extract chapter content from the response
    chapter_text = chapter_content.split("<chapter>")[1].split("<chapter>")[0]

    # Parse the chapter text to extract chapter number, title, and content
    lines = chapter_text.strip().split("\n")
    chapter_number = lines[0].split(":")[1].strip().strip('"').strip(",")
    chapter_title = lines[1].strip().strip('"').strip(",")
    chapter_content = "\n".join(lines[2:]).strip().strip('"')

    # create chapter dictionary
    chapter_dict = {
        "chapter_number": chapter_number,
        "title": chapter_title,
        "content": chapter_content,
    }

    # add chapter to all_chapters dictionary in correct order
    all_chapters[f"chapter {chapter_number}"] = chapter_dict


# run the async function to generate and save all chapters
asyncio.run(generate_and_save_chapters(facts, characters, plot, chapters))

""" 
async def generate_chapter_audios(all_chapters):
    audio_tasks = []
    for chapter_key, chapter_data in all_chapters.items():
        chapter_number = chapter_data["chapter_number"]
        chapter_title = chapter_data['title'].split(': ')[1].strip('"')
        chapter_content = chapter_data['content'].split(': ')[1].strip('"')

        # Split content into chunks of 4000 characters (approximately 4096 characters)
        chunks = [chapter_content[i:i+4000]
                  for i in range(0, len(chapter_content), 4000)]

        for i, chunk in enumerate(chunks):
            # Prepare the text for audio generation
            audio_text = f"chapter {chapter_number}" + (
                f" part {i+1}" if i > 0 else "") + f". {chapter_title}.\n\n{chunk}"

            # ensure the audio_text doesn't exceed 4096 characters
            if len(audio_text) > 4096:
                audio_text = audio_text[:4093] + "..."

            # create a task for each chunk's audio generation
            task = asyncio.create_task(text_to_speech(
                audio_text, f"chapters/chapters_{chapter_number}_part_{i+1}_audio"))
            audio_tasks.append(task)

    # wait for all audio generation task to complete
    await asyncio.gather(*audio_tasks)
    print("all chapters audio parts have been generated")

    # merge audio files for each chapter
    merge_chapter_audios(all_chapters)


def merge_chapter_audios(all_chapters):
    all_audio = []
    sample_rate = None


    for chapter_key in sorted(all_chapters.keys(), key=lambda x: int(x.split('_')[1])):
        chapter_number = all_chapters[chapter_key]['chapter_number']
        chapter_parts = sorted([f for f in os.listdir('chapters') if f.startswith(
                        f"chapter_{chapter_number}_part_") and f.endswith('_audio.mp3')])

        for part in chapter_parts:
            data, rate = sf.read(os.path.join('chapters', part))
            if sample_rate is None:
                sampel_rate = rate
            all_audio.append(data)

        # concatenate all audio data
        merged_audio = np.concatenate(all_audio)

        # save merged audio as MP3
        sf.write('chapters/full_audiobook.mp3', merged_audio, sampel_rate,format="mp3")
        print("Full audiobook has been created as MP3")
        
    # load the generated chapters
    with open('chapters/all_chapters.json', 'r') as f:
        all_chapters=json.load(f)
        
    #generate audio for all chapter simultaneously
    asyncio.run(generate_chapter_audios(all_chapters))
    
"""
