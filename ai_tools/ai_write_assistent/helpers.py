import json
import logging
import re
import shutil
from pathlib import Path


def clean_up(where="writer"):
    """
    Moves the 'all_chapters.json' file from the source directory to the destination directory.
    If the file already exists in the destination directory, appends a counter to the filename to avoid overwriting.
    Removes the file if it is empty or contains only "{}".
    """
    if "bookwriter" in where:
        src_path = Path("chapters/all_chapters.json")
        dst_dir = Path("data/archives")
        dst_base_name = "all_chapters.json"
    else:
        src_path = Path("json/facts.json")
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
        if re.search(r"<json>(.*?)</json>", response, re.DOTALL):
            json_match = re.search(r"<json>(.*?)</json>", response, re.DOTALL)
            if not json_match:
                print("Error: No JSON found in the response")

            json_str = json_match.group(1).strip()
        else:
            json_str = response

        # Attempt to parse the JSON string
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format: {e}")
            return None

        # Save the valid JSON to a file
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)

        print(f"JSON successfully extracted and saved to {output_file}")
        return json_data

    except Exception as e:
        print(f"Error occurred while extracting JSON: {e}")
        return None

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


def split_text(text, max_chunk_size=2048):
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


def process_text_in_chunks(agent_function, text, *args, **kwargs):
    """Process the text in chunks using the specified agent function."""
    chunks = split_text(text)
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


def process_json_in_chunks(agent_function, text, *args, **kwargs):
    chunks = split_text(text)
    combined_data = {}

    for idx, chunk in enumerate(chunks):
        logging.info(f"Processing chunk {idx + 1}/{len(chunks)}")
        result = agent_function(chunk, *args, **kwargs)
        if result:
            # Extract JSON between <json> and </json>
            json_text = re.search(r"<json>(.*?)</json>", result, re.DOTALL)
            if json_text:
                json_content = json_text.group(1).strip()
                try:
                    json_result = json.loads(json_content)
                    # Merge json_result into combined_data
                    combined_data = merge_json(combined_data, json_result)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decoding error in chunk {idx + 1}: {e}")
            else:
                logging.error(f"No JSON found in chunk {idx + 1}")
        else:
            logging.error(f"Failed to process chunk {idx + 1}")

    return json.dumps(combined_data, indent=2)


def merge_json(combined_data, new_data):
    for key, value in new_data.items():
        if key in combined_data:
            if isinstance(combined_data[key], list) and isinstance(value, list):
                combined_data[key].extend(value)
            elif isinstance(combined_data[key], dict) and isinstance(value, dict):
                combined_data[key] = merge_json(combined_data[key], value)
            else:
                # Handle conflicting keys (could be customized)
                pass
        else:
            combined_data[key] = value
    return combined_data
