import re
from ai_tools.ai_youtube_summary import YouTubeSummarizer
from ai_tools.ai_rumble_summary import RumbleSummarizer


class VideoProcessingAgent:
    def __init__(self, transcribe):
        self.transcribe = transcribe
        self.youtube_summarizer = None
        self.rumble_summarizer = None

    def is_youtube_url(self, url):
        """Check if the provided URL is a valid YouTube URL."""
        youtube_regex = (
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$"
        )
        return re.match(youtube_regex, url) is not None

    def is_rumble_url(self, url):
        """Check if the provided URL is a valid Rumble URL."""
        rumble_regex = r"(https?://)?(www\.)?rumble\.(com)/.+$"
        return re.match(rumble_regex, url) is not None

    def get_summarizer(self, url):
        """Return the appropriate summarizer based on the URL."""
        if self.is_youtube_url(url):
            if self.youtube_summarizer is None:
                self.youtube_summarizer = YouTubeSummarizer(self.transcribe)
            return self.youtube_summarizer
        elif self.is_rumble_url(url):
            if self.rumble_summarizer is None:
                self.rumble_summarizer = RumbleSummarizer(self.transcribe)
            return self.rumble_summarizer
        else:
            return None

    def process_user_request(self, video_url):
        """
        Main method for processing user requests.
        Takes in a video URL (YouTube or Rumble), checks if it is valid, and performs summarization.
        """
        # Step 1: Validate the input URL
        summarizer = self.get_summarizer(video_url)
        if summarizer is None:
            return "Invalid URL. Please provide a valid YouTube or Rumble video link."

        # Step 2: Delegate summarization task to the appropriate tool (YouTube or Rumble)
        try:
            platform = "YouTube" if self.is_youtube_url(video_url) else "Rumble"
            print(f"Processing {platform} video: {video_url}")
            full_text, summary = summarizer.summarize(video_url)
            return full_text, summary

        except Exception as e:
            return None, f"An error occurred while processing the video: {str(e)}"

    def handle_user_input(self, user_input):
        """
        This method receives user input and determines if a YouTube or Rumble URL was given.
        If so, it calls process_user_request to summarize the video.
        """
        if (
            "youtube.com" in user_input
            or "youtu.be" in user_input
            or "rumble.com" in user_input
        ):
            return self.process_user_request(user_input)
        else:
            return (
                None,
                "I can only summarize YouTube or Rumble videos at the moment. Please provide a valid URL.",
            )


# Example usage
if __name__ == "__main__":
    agent = VideoProcessingAgent(transcribe=True)

    # Simulating user input for Rumble
    user_input = "https://rumble.com/v9abcx-sample-video.html"

    # Process user request
    full_text, summary = agent.handle_user_input(user_input)
    print(summary)
