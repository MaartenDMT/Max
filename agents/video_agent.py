import re

from ai_tools.ai_rumble_summary import RumbleSummarizer
from ai_tools.ai_youtube_summary import YouTubeSummarizer


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

    async def process_user_request(self, video_url: str) -> dict:
        """
        Main method for processing user requests.
        Takes in a video URL (YouTube or Rumble), checks if it is valid, and performs summarization.
        Returns a dictionary with full_text, summary, and status.
        """
        # Step 1: Validate the input URL
        if not isinstance(video_url, str) or not video_url.strip():
            return {
                "status": "error",
                "message": "No video URL provided.",
            }
        summarizer = self.get_summarizer(video_url)
        if summarizer is None:
            return {
                "status": "error",
                "message": "Invalid URL. Please provide a valid YouTube or Rumble video link.",
            }

        # Step 2: Delegate summarization task to the appropriate tool (YouTube or Rumble)
        try:
            platform = "YouTube" if self.is_youtube_url(video_url) else "Rumble"
            # print(f"Processing {platform} video: {video_url}") # Removed print statement
            result = await summarizer.summarize(video_url)

            # Check if the result is successful
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "full_text": result.get("full_text"),
                    "summary": result.get("summary"),
                    "summary_file": result.get("summary_file"),
                }
            else:
                # Return the error message from the summarizer
                return {
                    "status": "error",
                    "message": result.get("message", "Summarization failed."),
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"An error occurred while processing the video: {str(e)}",
            }

    async def _handle_user_input_async(self, user_input: str) -> dict:
        """
        This method receives user input and determines if a YouTube or Rumble URL was given.
        If so, it calls process_user_request to summarize the video.
        Returns a dictionary with the result.
        """
        if not isinstance(user_input, str) or not user_input.strip():
            return {
                "status": "error",
                "message": "No input provided.",
            }
        if (
            "youtube.com" in user_input
            or "youtu.be" in user_input
            or "rumble.com" in user_input
        ):
            return await self.process_user_request(user_input)
        else:
            return {
                "status": "error",
                "message": "I can only summarize YouTube or Rumble videos at the moment. Please provide a valid URL.",
            }

    def handle_user_input(self, user_input: str) -> dict:
        """Synchronous wrapper for compatibility in tools/tests.
        Ensures a concrete dict is returned even when called from within an async test.
        """
        import asyncio
        import threading

        # Detect if we're already inside a running event loop
        try:
            asyncio.get_running_loop()
            running = True
        except RuntimeError:
            running = False

        if not running:
            # Use a dedicated event loop synchronously
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self._handle_user_input_async(user_input))
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        # If an event loop is already running (e.g., pytest-asyncio), run the coroutine in a separate thread
        result_holder: dict = {}
        error_holder: dict = {}

        def _runner():
            try:
                # Create an isolated loop for the coroutine
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    res = loop.run_until_complete(self._handle_user_input_async(user_input))
                    result_holder["result"] = res
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()
            except Exception as e:  # pragma: no cover
                error_holder["error"] = e

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join()

        if error_holder:
            return {"status": "error", "message": str(error_holder["error"]) }
        return result_holder.get("result", {"status": "error", "message": "Unknown error"})


# Example usage (removed interactive parts for API readiness)
# if __name__ == "__main__":
#     agent = VideoProcessingAgent(transcribe=True)

#     # Simulating user input for Rumble
#     user_input = "https://rumble.com/v9abcx-sample-video.html"

#     # Process user request
#     full_text, summary = agent.handle_user_input(user_input)
#     print(summary)
