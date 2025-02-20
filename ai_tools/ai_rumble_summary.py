import os
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

    def summarize(self, video_url, summary_length="detailed"):
        try:
            self.logger.info(f"Summarization started for {video_url}")
            video_info = get_video_info(video_url, self.logger)
            cleaned_title = clean_title(video_info["title"])
            channel = video_info.get("uploader", "Unknown")

            transcription_filename = f"{cleaned_title}_full.txt"
            transcription_filepath = os.path.join(
                self.output_path, transcription_filename
            )

            if os.path.exists(transcription_filepath):
                self.logger.info(
                    f"Using existing transcription: {transcription_filepath}"
                )
                with open(transcription_filepath, "r", encoding="utf-8") as file:
                    transcribed_text = file.read()
            else:
                download_audio(video_url, self.download_path, self.logger)
                transcribed_text = transcribe_audio(
                    self.audio_filename, self.transcribe_model, self.logger
                )
                if not transcribed_text:
                    return None, "Transcription failed."
                save_text(transcribed_text, transcription_filename, self.output_path)

            chunks = split_text(transcribed_text, MAX_CHUNK_SIZE)
            self.logger.info(f"Transcription split into {len(chunks)} chunks.")

            chain = create_chain(self.llm, summary_length)
            if not chain:
                return transcribed_text, "Failed to create summarization chain."

            summaries = []
            for idx, chunk in enumerate(chunks):
                self.logger.info(f"Summarizing chunk {idx + 1}/{len(chunks)}")
                summary = process_chat(chain, chunk, idx + 1, self.logger)
                if summary:
                    summaries.append(f"## Summary of Part {idx + 1}\n{summary}\n")

            self.logger.info(
                f"Total summaries generated: {len(summaries)} out of {len(chunks)}"
            )

            if not summaries:
                return transcribed_text, "Summarization failed."

            combined_summary = "\n".join(summaries)

            summary_filename = f"{cleaned_title}.md"
            meta = meta_data(cleaned_title, video_url, channel, "rumble")
            save_md(
                combined_summary,
                summary_filename,
                video_info["title"],
                meta,
                self.output_path,
                self.logger,
            )

            self.logger.info(f"Summary saved to {summary_filename}")
            return transcribed_text, combined_summary
        except Exception as e:
            self.logger.error(f"Error during Rumble summarization: {e}")
            return None, f"An error occurred: {str(e)}"
        finally:
            if os.path.exists(self.audio_filename):
                os.remove(self.audio_filename)
