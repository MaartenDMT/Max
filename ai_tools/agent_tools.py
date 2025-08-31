import asyncio
import json

# V-- THE MOST IMPORTANT FIX: Import BaseTool from crewai, NOT langchain --V
# CrewAI optional: provide a minimal BaseTool shim if not installed
try:
    from crewai.tools import BaseTool  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    class BaseTool:  # minimal shim
        name: str = "BaseTool"
        description: str = ""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def _run(self, *args, **kwargs):
            raise NotImplementedError("BaseTool shim: _run not implemented")

        async def _arun(self, *args, **kwargs):
            raise NotImplementedError("BaseTool shim: _arun not implemented")
from langchain_core.messages import \
    AIMessage  # Keep if AIMessage is still used by LLM responses

from agents.video_agent import VideoProcessingAgent
from ai_tools.ai_bookwriter.bookwriter import BookWriter
# (Assuming these imports are correct and the modules exist)
from ai_tools.ai_llm.llm_critique import CritiqueLLM
from ai_tools.ai_llm.llm_reflecting import ReflectingLLM
from ai_tools.ai_music_generation import MusicLoopGenerator
from ai_tools.ai_research_agent import AIResearchTools
from ai_tools.ai_write_assistent.writer import WriterAssistant

# Initialize dependencies
_chatbot_llm_modes = {"reflecting": ReflectingLLM(), "critique": CritiqueLLM()}
_music_loop_generator_instance = MusicLoopGenerator()
_research_tools_instance = AIResearchTools()
_video_processing_agent_instance = VideoProcessingAgent(transcribe=None)
_writer_assistant_instance = WriterAssistant()
_book_writer_instance = BookWriter()


# Removed ChatbotToolInput - arguments are inferred from _arun signature
class ChatbotTool(BaseTool):
    name: str = "Chatbot Tool"
    description: str = (
        "Processes text using a specified LLM mode (critique or reflecting). "
        "Useful for getting critiques or reflections on provided content. "
        "Input: 'mode' (str), 'summary' (str), and 'full_text' (str)."
    )
    # Removed args_schema: CrewAI BaseTool infers from _arun method signature

    async def _arun(self, mode: str, summary: str, full_text: str) -> str:
        try:
            mode = mode.strip().lower()
            if mode not in _chatbot_llm_modes:
                return json.dumps(
                    {
                        "error": f"Invalid mode: {mode}. Available modes: {', '.join(_chatbot_llm_modes.keys())}"
                    }
                )
            content = f"Summary:\n{summary.strip()}\n\nFull Text:\n{full_text.strip()}"
            response = await _chatbot_llm_modes[mode]._handle_query(content, [])
            if isinstance(response, AIMessage):
                return json.dumps({"result": response.content})
            if isinstance(
                response, str
            ):  # Handle cases where response might already be a string
                return json.dumps({"result": response})
            return json.dumps({"result": str(response)})
        except Exception as e:
            return json.dumps({"error": f"Error in Chatbot Tool: {str(e)}"})

    # _run is synchronous, so it calls _arun via a private loop when safe
    def _run(self, mode: str, summary: str, full_text: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # When already in an event loop, run in a worker thread
            return asyncio.run(asyncio.to_thread(self._arun, mode, summary, full_text))
        return asyncio.run(self._arun(mode=mode, summary=summary, full_text=full_text))


chatbot_tool = ChatbotTool()


# Removed MusicGenerationToolInput
class MusicGenerationTool(BaseTool):
    name: str = "Music Generation Tool"
    description: str = (
        "Generates a music loop based on a prompt and BPM. "
        "Input: 'bpm' (int) and 'prompt' (str)."
    )
    # Removed args_schema

    async def _arun(self, bpm: int, prompt: str) -> str:
        try:
            loop_file = await asyncio.to_thread(
                _music_loop_generator_instance.generate_loop, prompt=prompt, bpm=bpm
            )
            if loop_file:
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Music loop generated: {loop_file}",
                        "file_path": loop_file,
                    }
                )
            else:
                return json.dumps(
                    {"status": "error", "message": "Failed to generate music loop."}
                )
        except Exception as e:
            return json.dumps({"error": f"Error in Music Generation Tool: {str(e)}"})

    def _run(self, bpm: int, prompt: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, bpm, prompt))
        return asyncio.run(self._arun(bpm=bpm, prompt=prompt))


music_generation_tool = MusicGenerationTool()


# Removed ResearchAgentToolInput
class ResearchAgentTool(BaseTool):
    name: str = "Research Agent Tool"
    description: str = (
        "Performs general research using various tools like Wikipedia, DuckDuckGo, and file operations. "
        "Input: 'query' (str)."
    )
    # Removed args_schema

    async def _arun(self, query: str) -> str:
        try:
            response = await asyncio.to_thread(
                _research_tools_instance.process_chat, query
            )
            return json.dumps({"research_result": response})
        except Exception as e:
            return json.dumps({"error": f"Error in Research Agent Tool: {str(e)}"})

    def _run(self, query: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, query))
        return asyncio.run(self._arun(query=query))


research_agent_tool = ResearchAgentTool()


# Removed VideoSummarizerToolInput
class VideoSummarizerTool(BaseTool):
    name: str = "Video Summarizer Tool"
    description: str = (
        "Summarizes YouTube or Rumble videos. " "Input: 'video_url' (str)."
    )
    # Removed args_schema

    async def _arun(self, video_url: str) -> str:
        try:
            result = await asyncio.to_thread(
                _video_processing_agent_instance.handle_user_input, video_url
            )
            if result.get("status") == "success":
                return json.dumps(
                    {
                        "summary": result.get("summary"),
                        "full_text": result.get("full_text"),
                    }
                )
            else:
                return json.dumps(
                    {"error": result.get("message", "Failed to summarize video.")}
                )
        except Exception as e:
            return json.dumps({"error": f"Error in Video Summarizer Tool: {str(e)}"})

    def _run(self, video_url: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, video_url))
        return asyncio.run(self._arun(video_url=video_url))


video_summarizer_tool = VideoSummarizerTool()


# Removed StoryWriterToolInput
class StoryWriterTool(BaseTool):
    name: str = "Story Writer Tool"
    description: str = (
        "Creates a story based on a given book description and initial text content. "
        "Input: 'book_description' (str) and 'text_content' (str)."
    )
    # Removed args_schema

    async def _arun(self, book_description: str, text_content: str) -> str:
        try:
            story_output = await asyncio.to_thread(
                _writer_assistant_instance.create_story,
                book_description,
                text_content,
            )
            return json.dumps({"story_output": story_output})
        except Exception as e:
            return json.dumps({"error": f"Error in Story Writer Tool: {str(e)}"})

    def _run(self, book_description: str, text_content: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(
                asyncio.to_thread(self._arun, book_description, text_content)
            )
        return asyncio.run(
            self._arun(book_description=book_description, text_content=text_content)
        )


story_writer_tool = StoryWriterTool()


# Removed BookWriterToolInput
class BookWriterTool(BaseTool):
    name: str = "Book Writer Tool"
    description: str = (
        "Creates a book based on a given book description, number of chapters, and initial text content. "
        "Input: 'book_description' (str), 'num_chapters' (int), and 'text_content' (str)."
    )
    # Removed args_schema

    async def _arun(
        self, book_description: str, num_chapters: int, text_content: str
    ) -> str:
        try:
            book_output = await asyncio.to_thread(
                _book_writer_instance.create_story,
                book_description,
                num_chapters,
                text_content,
            )
            return json.dumps({"book_output": book_output})
        except Exception as e:
            return json.dumps({"error": f"Error in Book Writer Tool: {str(e)}"})

    def _run(self, book_description: str, num_chapters: int, text_content: str) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(
                asyncio.to_thread(
                    self._arun, book_description, num_chapters, text_content
                )
            )
        return asyncio.run(
            self._arun(
                book_description=book_description,
                num_chapters=num_chapters,
                text_content=text_content,
            )
        )


book_writer_tool = BookWriterTool()

# Example usage (for testing purposes)
if __name__ == "__main__":

    async def test_all_tools():
        # Test ChatbotTool
        print("Testing Chatbot Tool (Critique mode)...")
        chatbot_result = await chatbot_tool._arun(
            mode="critique",
            summary="This is a short summary.",
            full_text="This is the full text of the document.",
        )
        print(f"Chatbot Result: {chatbot_result}\n")

        print("Testing Chatbot Tool (Reflecting mode)...")
        chatbot_result_reflect = await chatbot_tool._arun(
            mode="reflecting",
            summary="This is a short summary.",
            full_text="This is the full text of the document.",
        )
        print(f"Chatbot Result (Reflecting): {chatbot_result_reflect}\n")

        # Test MusicGenerationTool
        print("Testing Music Generation Tool...")
        music_result = await music_generation_tool._arun(
            bpm=140, prompt="jazz fusion loop"
        )
        print(f"Music Result: {music_result}\n")

        # Test ResearchAgentTool
        print("Testing Research Agent Tool...")
        research_result = await research_agent_tool._arun(
            query="What is the capital of France?"
        )
        print(f"Research Result: {research_result}\n")

        # Test VideoSummarizerTool
        print("Testing Video Summarizer Tool...")
        video_result = await video_summarizer_tool._arun(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )  # Example URL
        print(f"Video Summary Result: {video_result}\n")

        # Test StoryWriterTool
        print("Testing Story Writer Tool...")
        story_result = await story_writer_tool._arun(
            book_description="A short story about a cat detective.",
            text_content="The cat, named Whiskers, wore a tiny trench coat and a fedora. He prowled the dimly lit alleys of the city, a shadow among shadows.",
        )
        print(f"Story Writer Result: {story_result}\n")

        # Test BookWriterTool
        print("Testing Book Writer Tool...")
        book_result = await book_writer_tool._arun(
            book_description="A sci-fi novel outline about a space colony.",
            num_chapters=3,
            text_content="The year is 2342. Humanity has colonized Mars. A new threat emerges from the depths of the red planet.",
        )
        print(f"Book Writer Result: {book_result}\n")

    asyncio.run(test_all_tools())
