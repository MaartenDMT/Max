import os
import re

try:
    import yt_dlp
    _YTDLP_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    yt_dlp = None
    _YTDLP_AVAILABLE = False
import datetime

try:
    from langchain.prompts import PromptTemplate  # optional
except Exception:  # pragma: no cover - optional dependency
    class PromptTemplate:  # minimal shim for tests
        def __init__(self, input_variables, template):
            self.template = template

        def __or__(self, other):
            # Compose into a simple callable chain
            return other

try:
    from langchain_core.messages import AIMessage  # optional
except Exception:  # pragma: no cover - optional dependency
    class AIMessage:  # minimal shim
        def __init__(self, content):
            self.content = content

MAX_CHUNK_SIZE = 2048


def get_video_info(video_url, logger):
    """Extract video information."""
    if not _YTDLP_AVAILABLE:
        logger.error("yt_dlp is not installed; cannot extract video info.")
        return None

    try:
        ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_url, download=False)
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def clean_title(title):
    """Remove special characters from a title."""
    return re.sub(r"[^\w\s-]", "", title).strip()


def download_audio(video_url, download_path, logger):
    """Download audio from a video."""
    if not _YTDLP_AVAILABLE:
        logger.error("yt_dlp is not installed; cannot download audio.")
        return None

    try:
        filename = "audio.%(ext)s"
        ydl_opts = {
            "format": "bestaudio/worst",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(download_path, filename),
            "noplaylist": True,
            "quiet": True,
        }
        # Disable the range requests (HTTP Error 416) by not attempting to resume
        ydl_opts["resumable"] = False

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        logger.error(f"Failed to download audio: {e}")
        return None


def transcribe_audio(audio_filepath, transcribe_model, logger):
    """Transcribe audio using Whisper."""
    try:
        result = transcribe_model.transcribe(audio_filepath)
        logger.info("Audio transcription completed.")
        return result
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        return None


def split_text(text, max_chunk_size=MAX_CHUNK_SIZE):
    """Split text into manageable chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        estimated_tokens = (len(current_chunk) + len(sentence)) // 4
        if estimated_tokens <= max_chunk_size:
            current_chunk += " " + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(sentence) // 4 > max_chunk_size:
                for i in range(0, len(sentence), max_chunk_size * 4):
                    chunks.append(sentence[i : i + max_chunk_size * 4].strip())
                current_chunk = ""
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def create_chain(llm, summary_length="detailed"):
    """Create a summarization chain."""
    prompt_text = (
        "Provide a brief summary based on the following content:\n\n{context}"
        if summary_length == "brief"
        else """
You are an expert summarizer. Read the following context and provide a detailed summary **following this exact format**:

### Summary of Part X

Begin with a brief introduction summarizing the overall theme of the discussion.

Then, for each main topic discussed, present it as a header and explain what was said about it in bullet points. Follow this structure:

### [Topic Name]

- Key point 1 about the topic.
- Key point 2 about the topic.
- Additional details, examples, or speaker recommendations related to the topic.

Continue this format for each topic.

Conclude with any overall insights or themes emphasized by the speaker.

### Please ensure that:
- Each topic is clearly highlighted as a header.
- Under each topic, you provide detailed bullet points explaining what was said.
- The summary strictly adheres to this format without adding or omitting any sections.

context:
{context}
"""
    )
    prompt_template = PromptTemplate(input_variables=["context"], template=prompt_text)
    # If llm is None (optional dependency), return a passthrough that echoes context
    if llm is None:
        class _Echo:
            def invoke(self, inputs):
                ctx = inputs.get("context", "")
                return f"### Summary of Part X\n\n{ctx[:200]}"  # simple echo for tests
        return _Echo()
    return prompt_template | llm


def process_chat(chain, text_chunk, part_number, logger):
    """Generate summary for a text chunk."""
    try:
        response = chain.invoke({"context": text_chunk})
        if isinstance(response, str):
            return f"### Summary of Part {part_number}\n\n" + response.strip()
        elif isinstance(response, AIMessage):
            return f"### Summary of Part {part_number}\n\n" + response.content.strip()
        return f"### Summary of Part {part_number}\n\n" + str(response).strip()
    except Exception as e:
        logger.error(f"Failed to process chat for part {part_number}: {e}")
        return ""


def save_text(text, filename, output_path):
    """Save text to a file."""
    output_file = os.path.join(output_path, filename)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)


def save_md(text, filename, title, meta, output_path, logger):
    """Save summary as Markdown."""
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open(os.path.join(output_path, filename), "w", encoding="utf-8") as file:
            file.write(f"{meta}\n")
            file.write(f"# {title}\n\n")
            file.write(text)
    except Exception as e:
        logger.error(f"Failed to save markdown file: {e}")


def meta_data(cleaned_title, url, channel, input="youtube"):
    return f"""---
status: inputs/summary
medium: video/{input}
channel: "[[{channel}]]"
up:
- "[[{cleaned_title} Concept Map.canvas|{cleaned_title} Concept Map]]"
created-date: {datetime.datetime.now()}
updated-date: <% tp.date.now("YYYY-MM-DD HH:MM") %>
tags:
- rumble
link: {url}
---
"""
