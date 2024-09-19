import os
import re

import yt_dlp
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from utils.loggers import LoggerSetup
from langchain_core.messages import AIMessage


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

    def create_chain(self, summary_length="detailed"):
        """Create a summarization chain with summary length control."""
        try:
            if summary_length == "brief":
                prompt_text = (
                    "Provide a brief summary based on the following content: {context}"
                )
            else:
                prompt_text = """
                Read the following content and provide a detailed summary that addresses the following key points:
                1. ## Core Topics: What are the main subjects or topics being discussed?
                2. ## Key Arguments: Highlight the most important arguments made and the supporting evidence or details.
                3. ## Insights and Takeaways: What insights, lessons, or conclusions are emphasized?
                4. ## Examples and Data: Provide relevant examples or data points that illustrate or support the content.
                5. ## Summarize Clearly in x sections: Make sure the summary is well-organized and clearly written in sections.
                Content: {context}
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

    def process_chat(self, chain, transcribed_text):
        """Process the summarization using the chain and return a response."""
        try:
            response = chain.invoke({transcribed_text})

            # Log the response for debugging
            self.logger.info(f"Raw response from LLM: {response}")

            # If the response is an AIMessage, extract the content
            if isinstance(response, AIMessage):
                return response.content  # Extract the string content from AIMessage
            return response

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

        print(f"Markdown file saved: {output_file}")

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

            # Step 1: Check if transcription file exists, skip downloading if found
            if os.path.exists(transcription_filepath):
                self.logger.info(
                    f"Transcription file already exists: {transcription_filepath}"
                )
                with open(transcription_filepath, "r", encoding="utf-8") as file:
                    transcribed_text = file.read()
            else:
                # Download and transcribe the video if transcription does not exist
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

            # Step 2: Create a summarization chain and summarize the content
            chain = self.create_chain(summary_length=summary_length)
            if not chain:
                self.logger.error("Failed to create summarization chain.")
                return transcribed_text, "Summarization chain creation failed."

            summary = self.process_chat(chain, transcribed_text)

            if not summary:
                self.logger.error("Summarization failed. No response from LLM.")
                return transcribed_text, "Summarization failed."

            # Step 3: Save the summary
            summary_filename = f"{cleaned_title}_summary.md"
            self.save_md(summary, summary_filename, video_info["title"])
            self.logger.info(f"Summary saved to {summary_filename}")

            # Step 4: Return both full text and summary
            self.logger.info("Summarization successfully completed.")
            return transcribed_text, summary

        except Exception as e:
            self.logger.error(f"Error during YouTube summarization: {e}")
            return None, f"An error occurred while processing the video: {str(e)}"
