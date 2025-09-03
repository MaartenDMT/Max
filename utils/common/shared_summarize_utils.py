import os
import re

try:
    import yt_dlp
    _YTDLP_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    yt_dlp = None
    _YTDLP_AVAILABLE = False
import datetime
import logging  # Added import
from typing import List, Optional, TypedDict  # Added import

import yt_dlp
from langchain.chains import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain_core.language_models import BaseLanguageModel  # Added import
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from ai_tools.speech.speech_to_text import TranscribeFastModel  # Added import

_YTDLP_AVAILABLE = True # Assuming yt_dlp is always available now

MAX_CHUNK_SIZE = 2048


class VideoInfo(TypedDict):
    title: str
    uploader: str
    # Add other relevant keys from ydl.extract_info if needed


def get_video_info(video_url: str, logger: logging.Logger) -> Optional[VideoInfo]:
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


def clean_title(title: str) -> str:
    """Remove special characters from a title."""
    return re.sub(r"[^\w\s-]", "", title).strip()


def download_audio(video_url: str, download_path: str, logger: logging.Logger) -> None:
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


def transcribe_audio(audio_filepath: str, transcribe_model: TranscribeFastModel, logger: logging.Logger) -> Optional[str]:
    """Transcribe audio using Whisper."""
    try:
        result = transcribe_model.transcribe(audio_filepath)
        logger.info("Audio transcription completed.")
        return result
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        return None


def split_text(text: str, max_chunk_size: int = MAX_CHUNK_SIZE) -> List[str]:
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


def create_chain(llm: BaseLanguageModel, summary_length: str = "detailed") -> LLMChain:
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

    # Explicitly create an LLMChain and then use load_summarize_chain
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    chain = load_summarize_chain(llm_chain, chain_type="stuff") # Changed chain_type to "stuff" for simplicity

    return chain


# --- Optional: LCEL-based summarization helper (non-breaking) ---
class LCELSummarizeChain:
    """Lightweight wrapper to mimic LLMChain shape using LCEL under the hood.

    Exposes .llm and .prompt so existing helper (process_chat) can still work
    by formatting the prompt and invoking llm directly, while also allowing
    direct runnable invocation via .invoke({"context": ...}).
    """

    def __init__(self, llm: BaseLanguageModel, prompt: PromptTemplate):
        self.llm = llm
        self.prompt = prompt
        # Build runnable: PromptTemplate -> LLM -> String output
        # Always coerce PromptValue to string before invoking the LLM to support
        # simple test doubles (DummyLLM) and non-LCEL LLMs.
        def _llm_node(x, _llm=llm):
            # Convert PromptValue to string if needed
            if hasattr(x, "to_string") and callable(getattr(x, "to_string")):
                x_in = x.to_string()
            elif hasattr(x, "text"):
                x_in = x.text
            else:
                x_in = str(x)

            # Prefer .invoke if available, otherwise treat as callable
            if hasattr(_llm, "invoke") and callable(getattr(_llm, "invoke")):
                return _llm.invoke(x_in)
            elif callable(_llm):
                return _llm(x_in)
            # Fallback: best-effort string conversion
            return str(x_in)

        # Compose LCEL pipeline using the callable node
        self._runnable = self.prompt | _llm_node | StrOutputParser()

    def invoke(self, inputs: dict):
        return self._runnable.invoke(inputs)


def create_chain_lcel(llm: BaseLanguageModel, summary_length: str = "detailed") -> LCELSummarizeChain:
    """Create a summarization chain using LCEL (Prompt | LLM | StrOutputParser).

    This does not replace the legacy create_chain to avoid breaking behavior,
    but provides a modern alternative for modules that want to migrate.
    """
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
    prompt = PromptTemplate(input_variables=["context"], template=prompt_text)
    if llm is None:
        # Mirror the legacy echo behavior for optional dependency scenarios
        class _Echo:
            def __init__(self, prompt):
                self.llm = None
                self.prompt = prompt

            def invoke(self, inputs):
                ctx = inputs.get("context", "")
                return f"### Summary of Part X\n\n{ctx[:200]}"

        return _Echo(prompt)

    return LCELSummarizeChain(llm=llm, prompt=prompt)


def process_chat(chain: LLMChain, text_chunk: str, part_number: int, logger: logging.Logger) -> str:
    """Generate summary for a text chunk."""
    try:
        # The 'chain' object here is actually the LLMChain from create_chain
        # So, chain.llm is the actual LLM model
        # And chain.prompt is the prompt template

        # Format the prompt directly
        formatted_prompt = chain.prompt.format(context=text_chunk)

        # Directly invoke the LLM
        response = chain.llm.invoke(formatted_prompt)

        # Extract content, ensuring it's a string
        content = ""
        if isinstance(response, str):
            content = response
        elif isinstance(response, AIMessage):
            content = response.content
        else:
            content = str(response) # Fallback for unexpected types

        # Ensure content is a string before stripping
        final_content = str(content)

        return f"### Summary of Part {part_number}\n\n" + final_content.strip()
    except Exception as e:
        logger.error(f"Failed to process chat for part {part_number}: {e}")
        return ""


def save_text(text: str, filename: str, output_path: str) -> None:
    """Save text to a file."""
    output_file = os.path.join(output_path, filename)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)


def save_md(text: str, filename: str, title: str, meta: str, output_path: str, logger: logging.Logger) -> None:
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


def meta_data(cleaned_title: str, url: str, channel: str, input: str = "youtube") -> str:
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
