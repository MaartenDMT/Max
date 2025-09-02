import asyncio
from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.ai_youtube_summary import YouTubeSummarizer

async def test_youtube_summary():
    """Test the YouTube summarization functionality."""
    # Use a short YouTube video for testing
    video_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"  # PSY - GANGNAM STYLE

    # Initialize the transcribe model
    transcribe_model = TranscribeFastModel()
    summarizer = YouTubeSummarizer(transcribe_model)

    try:
        result = await summarizer.summarize(video_url)
        if result["status"] == "success":
            print("Summary:")
            print(result["summary"])
            print("\nFull Transcript:")
            print(result["full_text"])
        else:
            print(f"Error: {result['message']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_youtube_summary())
