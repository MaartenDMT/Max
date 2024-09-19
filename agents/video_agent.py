import re

from ai_tools.ai_youtube_summary import YouTubeSummarizer


class VideoProcessingAgent:
    def __init__(self, transcribe):
        self.transcribe = transcribe
        self.summarizer = YouTubeSummarizer(transcribe)

    def is_youtube_url(self, url):
        """Check if the provided URL is a valid YouTube URL."""
        youtube_regex = (
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$"
        )
        return re.match(youtube_regex, url) is not None

    def process_user_request(self, video_url):
        """
        Main method for processing user requests.
        Takes in a YouTube video URL, checks if it is valid, and performs summarization.
        """
        # Step 1: Validate the input URL
        if not self.is_youtube_url(video_url):
            return "Invalid URL. Please provide a valid YouTube video link."

        # Step 2: Delegate summarization task to the YouTubeSummarizer tool
        try:
            print(f"Processing YouTube video: {video_url}")
            full_text, summary = self.summarizer.summarize_youtube(video_url)
            return full_text, summary

        except Exception as e:
            return f"An error occurred while processing the video: {str(e)}"

    def handle_user_input(self, user_input):
        """
        This method receives user input and determines if a YouTube URL was given.
        If so, it calls process_user_request to summarize the video.
        """
        if "youtube.com" in user_input or "youtu.be" in user_input:
            return self.process_user_request(user_input)
        else:
            return (
                None,
                "I can only summarize YouTube videos at the moment. Please provide a YouTube link.",
            )


# Example usage
if __name__ == "__main__":
    agent = VideoProcessingAgent()

    # Simulating user input
    user_input = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Process user request
    full_text, summary = agent.handle_user_input(user_input)
    print(summary)
