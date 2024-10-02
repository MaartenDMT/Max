import os
import re

import yt_dlp
from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama

from utils.loggers import LoggerSetup


class YouTubeSummarizer:
    def __init__(
        self, transcribe_model, download_path="data/audio/", output_path="data/text/"
    ):
        """
        Initialize YouTubeSummarizer with an external transcribe model (from AIAssistant).
        """
        self.transcribe_model = (
            transcribe_model  # Use the transcribe model from AIAssistant
        )
        self.download_path = download_path
        self.output_path = output_path
        self.audio_filename = os.path.join(self.download_path, "youtube_audio.wav")

        # LangChain component for summarization
        self.llm = ChatOllama(model="llama3.1", temperature=0.7, num_predict=-1)

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "YouTubeSummarizer", "youtube_summarizer.log"
        )

        # Log initialization
        self.logger.info("YouTube Summarizer initialized.")

    def get_video_info(self, video_url):
        """Extract information from a YouTube video, including the title."""
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
            self.logger.info(f"Video info extracted for {video_url}")
            self.logger.info(f"Video tags: {info_dict.get('tags', [])}")
            return info_dict
        except Exception as e:
            self.logger.error(f"Error extracting video info: {e}")

    def clean_title(self, title):
        """Remove special characters from the title and format it for a file name."""
        return re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")

    def download_audio(self, video_url):
        """Download audio from a YouTube video."""
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "wav",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": os.path.join(self.download_path, "youtube_audio.%(ext)s"),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            self.logger.info(f"Audio downloaded for {video_url}")
        except Exception as e:
            self.logger.error(f"Error downloading audio: {e}")

    def transcribe_audio(self):
        """Transcribe the audio using the external transcribe model."""
        try:
            self.logger.info("Transcribing audio using the provided transcribe model.")
            # Use the external transcribe model from AIAssistant to transcribe audio
            transcription = self.transcribe_model.transcribe(self.audio_filename)
            self.logger.info("Audio transcription completed.")
            return transcription
        except Exception as e:
            self.logger.error(f"Error during audio transcription: {e}")

    def split_text(self, text, max_chunk_size=4000):
        """Split text into chunks suitable for LLM processing."""
        import re

        # Split the text into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Estimate the token length (approximate 1 token ~ 4 characters)
            estimated_tokens = len(current_chunk) // 4 + len(sentence) // 4
            if estimated_tokens <= max_chunk_size:
                current_chunk += " " + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def create_chain(self, summary_length="detailed"):
        """Create a summarization chain with summary length control."""
        try:
            if summary_length == "brief":
                prompt_text = "Provide a brief summary based on the following content:\n\n{context}"
            else:
                prompt_text = """
                You are an expert summarizer. Read the following transcript of a conversation and provide a detailed summary that addresses the following key points:

                1. **Core Topics**: What are the main subjects or topics being discussed?
                2. **Key Arguments**: Highlight the most important arguments made and the supporting evidence or details.
                3. **Insights and Takeaways**: What insights, lessons, or conclusions are emphasized?
                4. **Examples and Data**: Provide relevant examples or data points that illustrate or support the content.
                5. **Organized Summary**: Ensure the summary is well-organized and clearly written in sections.

                Please focus on summarizing the content without adding any additional information or taking any actions.

                Transcript:
                {context}
                """

            # Define the template using PromptTemplate
            prompt_template = PromptTemplate(
                input_variables=["context"], template=prompt_text
            )

            # Create the LLMChain with the template and the ChatOllama model
            chain = prompt_template | self.llm
            self.logger.info("Chain created for summarization.")

            return chain
        except Exception as e:
            self.logger.error(f"Error creating chain: {e}")

    def process_chat(self, chain, text_chunk):
        """Process the summarization for a text chunk and return a response."""
        try:
            response = chain.invoke({"context": text_chunk})
            # Ensure that response is extracted correctly
            if isinstance(response, str):
                return response.strip()
            elif isinstance(response, AIMessage):
                return response.content.strip()
            else:
                return str(response).strip()
        except Exception as e:
            self.logger.error(f"Error during summarization: {e}")
            return None

    def save_text(self, text, filename):
        """Save text to a file."""
        output_file = os.path.join(self.output_path, filename)
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)

    def save_md(self, text, filename, title):
        """Save text to a Markdown file."""
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        output_file = os.path.join(self.output_path, filename)

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(f"# {title}\n\n")
            file.write(text)

        self.logger.info(f"Markdown file saved: {output_file}")

    def summarize_youtube(self, video_url, summary_length="detailed"):
        """Main method to summarize a YouTube video."""
        try:
            self.logger.info(f"Summarization started for {video_url}")

            video_info = self.get_video_info(video_url)
            cleaned_title = self.clean_title(video_info["title"])
            transcription_filename = f"{cleaned_title}_full.txt"
            transcription_filepath = os.path.join(
                self.output_path, transcription_filename
            )

            # Step 1: Get or create the transcription
            if os.path.exists(transcription_filepath):
                self.logger.info(
                    f"Transcription file already exists: {transcription_filepath}"
                )
                with open(transcription_filepath, "r", encoding="utf-8") as file:
                    transcribed_text = file.read()
            else:
                self.download_audio(video_url)
                transcribed_text = self.transcribe_audio()

                if not transcribed_text:
                    self.logger.error(
                        "Transcription failed. Empty transcription received."
                    )
                    return None, "Transcription failed. Please try again."

                # Save the full transcription
                self.save_text(transcribed_text, transcription_filename)
                self.logger.info(
                    f"Full transcription saved to {transcription_filepath}"
                )

            # Step 2: Split the transcription into chunks
            max_chunk_size = 4000  # Adjust based on your LLM's context window
            chunks = self.split_text(transcribed_text, max_chunk_size)

            self.logger.info(f"Transcription split into {len(chunks)} chunks.")

            # Step 3: Create the summarization chain
            chain = self.create_chain(summary_length=summary_length)
            if not chain:
                self.logger.error("Failed to create summarization chain.")
                return transcribed_text, "Summarization chain creation failed."

            # Step 4: Summarize each chunk
            summaries = []
            for idx, chunk in enumerate(chunks):
                self.logger.info(f"Summarizing chunk {idx + 1}/{len(chunks)}")
                summary = self.process_chat(chain, chunk)
                if summary:
                    summaries.append(f"### Summary of Part {idx + 1}\n{summary}\n")
                else:
                    self.logger.error(f"Summarization failed for chunk {idx + 1}.")

            if not summaries:
                self.logger.error("No summaries were generated.")
                return transcribed_text, "Summarization failed."

            # Step 5: Combine summaries
            combined_summary = "\n".join(summaries)

            # Optional: Summarize the combined summaries to create an overall summary
            overall_summary = self.process_chat(chain, combined_summary)
            if overall_summary:
                combined_summary = (
                    f"# Overall Summary\n{overall_summary}\n\n{combined_summary}"
                )

            # Step 6: Save the combined summary
            summary_filename = f"{cleaned_title}_summary.md"
            self.save_md(combined_summary, summary_filename, video_info["title"])
            self.logger.info(f"Summary saved to {summary_filename}")

            # Step 7: Return both full text and summary
            self.logger.info("Summarization successfully completed.")
            return transcribed_text, combined_summary

        except Exception as e:
            self.logger.error(f"Error during YouTube summarization: {e}")
            return None, f"An error occurred while processing the video: {str(e)}"
