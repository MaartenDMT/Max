import os
import asyncio  # Import asyncio for to_thread
from langchain_ollama import ChatOllama

from utils.loggers import LoggerSetup
from utils.common.shared_summarize_utils import (
    get_video_info,
    clean_title,
    download_audio,
    transcribe_audio,
    split_text,
    create_chain,
    process_chat,
    save_md,
    save_text,
    meta_data,
)

MAX_CHUNK_SIZE = 2048


class RumbleSummarizer:
    def __init__(
        self, transcribe_model, download_path="data/audio/", output_path="data/text/"
    ):
        self.transcribe_model = transcribe_model
        self.download_path = download_path
        self.output_path = output_path
        self.audio_filename = os.path.join(self.download_path, "audio.wav")

        self.llm = ChatOllama(
            model="deepseek-r1:latest", temperature=0.2, num_predict=-1
        )

        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("RumbleSummarizer", "rumble_summarizer.log")
        self.logger.info("Rumble Summarizer initialized.")

    async def summarize(
        self, video_url: str, summary_length: str = "detailed"
    ) -> dict:  # Marked as async
        try:
            self.logger.info(f"Summarization started for {video_url}")
            video_info = await asyncio.to_thread(get_video_info, video_url, self.logger)
            if not video_info:
                return {
                    "status": "error",
                    "message": "Failed to retrieve video information.",
                }

            cleaned_title = await asyncio.to_thread(clean_title, video_info["title"])
            channel = video_info.get("uploader", "Unknown")

            transcription_filename = f"{cleaned_title}_full.txt"
            transcription_filepath = os.path.join(
                self.output_path, transcription_filename
            )

            transcribed_text = ""
            if await asyncio.to_thread(os.path.exists, transcription_filepath):
                self.logger.info(
                    f"Using existing transcription: {transcription_filepath}"
                )
                with open(transcription_filepath, "r", encoding="utf-8") as file:
                    transcribed_text = await asyncio.to_thread(file.read)
            else:
                await asyncio.to_thread(
                    download_audio, video_url, self.download_path, self.logger
                )
                transcribed_text = await asyncio.to_thread(
                    transcribe_audio,
                    self.audio_filename,
                    self.transcribe_model,
                    self.logger,
                )
                if not transcribed_text:
                    return {"status": "error", "message": "Transcription failed."}
                await asyncio.to_thread(
                    save_text,
                    transcribed_text,
                    transcription_filename,
                    self.output_path,
                )

            chunks = await asyncio.to_thread(
                split_text, transcribed_text, MAX_CHUNK_SIZE
            )
            self.logger.info(f"Transcription split into {len(chunks)} chunks.")

            chain = await asyncio.to_thread(create_chain, self.llm, summary_length)
            if not chain:
                return {
                    "status": "error",
                    "message": "Failed to create summarization chain.",
                }

            summaries = []
            for idx, chunk in enumerate(chunks):
                self.logger.info(f"Summarizing chunk {idx + 1}/{len(chunks)}")
                summary = await asyncio.to_thread(
                    process_chat, chain, chunk, idx + 1, self.logger
                )
                if summary:
                    summaries.append(f"## Summary of Part {idx + 1}\n{summary}\n")

            self.logger.info(
                f"Total summaries generated: {len(summaries)} out of {len(chunks)}"
            )

            if not summaries:
                return {"status": "error", "message": "Summarization failed."}

            combined_summary = "\n".join(summaries)

            summary_filename = f"{cleaned_title}.md"
            meta = await asyncio.to_thread(
                meta_data, cleaned_title, video_url, channel, "rumble"
            )
            await asyncio.to_thread(
                save_md,
                combined_summary,
                summary_filename,
                video_info["title"],
                meta,
                self.output_path,
                self.logger,
            )

            self.logger.info(f"Summary saved to {summary_filename}")
            return {
                "status": "success",
                "full_text": transcribed_text,
                "summary": combined_summary,
                "summary_file": summary_filename,
            }
        except Exception as e:
            self.logger.error(f"Error during Rumble summarization: {e}")
            return {"status": "error", "message": f"An error occurred: {str(e)}"}
        finally:
            if await asyncio.to_thread(os.path.exists, self.audio_filename):
                await asyncio.to_thread(os.remove, self.audio_filename)
