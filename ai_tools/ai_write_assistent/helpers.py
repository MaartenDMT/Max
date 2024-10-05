import json
import logging
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


def clean_up():
    """
    Moves the 'all_chapters.json' file from the source directory to the destination directory.
    If the file already exists in the destination directory, appends a counter to the filename to avoid overwriting.
    Removes the file if it is empty or contains only "{}".
    """
    src_path = Path("chapters/all_chapters.json")
    dst_dir = Path("data/archives")
    dst_base_name = "all_chapters.json"

    # Check if the source file exists
    if not src_path.exists():
        print(f"Source file {src_path} does not exist.")
        return

    # Check if the file is empty or contains only '{}'
    if src_path.stat().st_size == 0 or src_path.read_text().strip() == "{}":
        print(f"File {src_path} is empty or contains only '{{}}'. Removing the file.")
        src_path.unlink()
        return

    # Ensure the destination directory exists
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Determine the new filename if the base name already exists in the destination directory
    dst_path = dst_dir / dst_base_name
    counter = 1
    while dst_path.exists():
        dst_path = dst_dir / f"all_chapters_{counter}.json"
        counter += 1

    # Move the file to the destination directory
    shutil.move(str(src_path), str(dst_path))
    print(f"File moved to {dst_path}")


def get_file_contents(file_path):
    """
    Returns the content of a text file
    """

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error file not found")
        return None
    except IOError:
        print(f"Error: unable to read file at {file_path}")
        return None


def extract_and_save_json(response, output_file):
    """_summary_
    Extract JSON from the response and saves it to a file.

    Args:
        response (_type_): _description_
        output_file (_type_): _description_
    """
    try:
        # extract JSON content using regex
        json_match = re.search(r"<json>(.*?)</json>", response, re.DOTALL)
        if not json_match:
            print("Error: No JSON found in the response")
            return False

        json_str = json_match.group(1).strip()

        # parse JSON to ensure its valid
        json_data = json.loads(json_str)

        # write JSOn to file
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)

        print(f"JSON succesfully extracted and saved to {output_file}")

        return json_data

    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the response")
        return False
    except IOError:
        print(f"Error: unable to read file at {output_file}")
        return False


def parse_chapter(chapter_text):
    """
    Parse the chapter text which is in a JSON-like format.
    """
    try:
        # Convert the chapter text to a proper JSON format
        # Ensure that the text is wrapped in braces and uses proper quotes
        if not chapter_text.startswith("{"):
            chapter_text = "{" + chapter_text

        if not chapter_text.endswith("}"):
            chapter_text = chapter_text + "}"

        # Fix common JSON formatting issues
        chapter_text = (
            chapter_text.replace("“", '"').replace("”", '"').replace("'", '"')
        )
        chapter_json = json.loads(chapter_text)

        # Extract chapter number, title, and content
        chapter_num_str = chapter_json.get("chapter", "").split(":")[1].strip()
        chapter_num = int(chapter_num_str)
        chapter_title = chapter_json.get("title", "").strip()
        chapter_content_text = chapter_json.get("content", "").strip()

        return chapter_num, chapter_title, chapter_content_text

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logging.error(f"Error parsing chapter text: {e}")
        return None


def add_chapter_to_dict(chapter_data, all_chapters):
    """
    Add a parsed chapter to the all_chapters dictionary.
    """
    if chapter_data:
        chapter_num, chapter_title, chapter_content_text = chapter_data

        # Create chapter dictionary
        chapter_dict = {
            "chapter_number": chapter_num,
            "title": chapter_title,
            "content": chapter_content_text,
        }

        # Add chapter to all_chapters dictionary
        all_chapters[f"chapter {chapter_num}"] = chapter_dict
        logging.info(f"Chapter {chapter_num} generated and saved.")
    else:
        logging.error("Failed to add chapter to dictionary due to parsing errors.")
