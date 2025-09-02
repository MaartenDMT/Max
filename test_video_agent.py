import asyncio
from ai_tools.speech.speech_to_text import TranscribeFastModel
from agents.video_agent import VideoProcessingAgent

async def test_video_agent():
    # Test the VideoProcessingAgent directly.
    # Initialize the transcribe model
    transcribe_model = TranscribeFastModel()
    
    # Initialize the video agent
    video_agent = VideoProcessingAgent(transcribe_model)
    
    # Test YouTube summarization
    video_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"  # PSY - GANGNAM STYLE
    print(f"Testing YouTube summarization for: {video_url}")
    
    # Test the async method directly
    result = await video_agent._handle_user_input_async(video_url)
    
    print("Result:")
    print(result)
    
    if result.get("status") == "success":
        print("\nSummary:")
        print(result.get("summary"))
    else:
        print(f"\nError: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(test_video_agent())