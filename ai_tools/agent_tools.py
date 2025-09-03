import asyncio
import json

from typing import Type

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

from ai_tools.tool_schemas import (
    ChatbotToolInput,
    ChatbotToolOutput,
    MusicGenerationToolInput,
    MusicGenerationToolOutput,
    ResearchAgentToolInput,
    ResearchAgentToolOutput,
    VideoSummarizerToolInput,
    VideoSummarizerToolOutput,
    StoryWriterToolInput,
    StoryWriterToolOutput,
    BookWriterToolInput,
    BookWriterToolOutput,
    ToolResponse
)

from agents.video_agent import VideoProcessingAgent
from ai_tools.ai_bookwriter.bookwriter import BookWriter
# (Assuming these imports are correct and the modules exist)
from ai_tools.ai_llm.llm_critique import CritiqueLLM
from ai_tools.ai_llm.llm_reflecting import ReflectingLLM
from ai_tools.ai_music_generation import MusicLoopGenerator
from ai_tools.ai_research_agent import AIResearchTools
from ai_tools.ai_write_assistent.writer import WriterAssistant

from ai_tools.speech.speech_to_text import TranscribeFastModel

from agents.chatbot_agent import ChatbotAgent

# Initialize dependencies
_chatbot_agent_instance = ChatbotAgent()
_music_loop_generator_instance = MusicLoopGenerator()
_research_tools_instance = AIResearchTools()
_video_processing_agent_instance = VideoProcessingAgent(transcribe=TranscribeFastModel())
_writer_assistant_instance = WriterAssistant()
_book_writer_instance = BookWriter()


class ChatbotTool(BaseTool):
    name: str = "Chatbot Tool"
    description: str = (
        "Processes text using a specified LLM mode (critique or reflecting). "
        "Useful for getting critiques or reflections on provided content. "
        "Input: 'mode' (str), 'summary' (str), and 'full_text' (str)."
    )
    args_schema: Type[ChatbotToolInput] = ChatbotToolInput


    async def _arun(self, input: ChatbotToolInput) -> ChatbotToolOutput:
        try:
            mode = input.mode.strip().lower()
            llm = _chatbot_agent_instance.get_llm(mode)
            if llm is None:
                return ChatbotToolOutput(
                    status="error",
                    error=f"Invalid mode: {mode}. Available modes: {', '.join(_chatbot_agent_instance.llm_factories.keys())}"
                )
            content = f"Summary:\n{input.summary.strip()}\n\nFull Text:\n{input.full_text.strip()}"
            response = await llm._handle_query(content, [])
            if isinstance(response, AIMessage):
                return ChatbotToolOutput(result=response.content)
            if isinstance(response, str):
                return ChatbotToolOutput(result=response)
            return ChatbotToolOutput(result=str(response))
        except Exception as e:
            return ChatbotToolOutput(status="error", error=f"Error in Chatbot Tool: {str(e)}")

    def _run(self, input: ChatbotToolInput) -> ChatbotToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, input))
        return asyncio.run(self._arun(input=input))


chatbot_tool = ChatbotTool()



class MusicGenerationTool(BaseTool):
    name: str = "Music Generation Tool"
    description: str = (
        "Generates a music loop based on a prompt and BPM. "
        "Input: 'bpm' (int) and 'prompt' (str)."
    )
    args_schema: Type[MusicGenerationToolInput] = MusicGenerationToolInput

    async def _arun(self, input: MusicGenerationToolInput) -> MusicGenerationToolOutput:
        try:
            loop_file = await asyncio.to_thread(
                _music_loop_generator_instance.generate_loop, prompt=input.prompt, bpm=input.bpm, duration=input.duration
            )
            if loop_file:
                return MusicGenerationToolOutput(
                    status="success",
                    message=f"Music loop generated: {loop_file}",
                    file_path=loop_file,
                )
            else:
                return MusicGenerationToolOutput(
                    status="error", message="Failed to generate music loop."
                )
        except Exception as e:
            return MusicGenerationToolOutput(status="error", error=f"Error in Music Generation Tool: {str(e)}")

    def _run(self, input: MusicGenerationToolInput) -> MusicGenerationToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, input))
        return asyncio.run(self._arun(input=input))


music_generation_tool = MusicGenerationTool()


class ResearchAgentTool(BaseTool):
    name: str = "Research Agent Tool"
    description: str = (
        "Performs general research using various tools like Wikipedia, DuckDuckGo, and file operations. "
        "Input: 'query' (str)."
    )
    args_schema: Type[ResearchAgentToolInput] = ResearchAgentToolInput

    async def _arun(self, input: ResearchAgentToolInput) -> ResearchAgentToolOutput:
        try:
            response = await asyncio.to_thread(
                _research_tools_instance.process_chat, input.query
            )
            return ResearchAgentToolOutput(research_result=response)
        except Exception as e:
            return ResearchAgentToolOutput(status="error", error=f"Error in Research Agent Tool: {str(e)}")

    def _run(self, input: ResearchAgentToolInput) -> ResearchAgentToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, input))
        return asyncio.run(self._arun(input=input))


research_agent_tool = ResearchAgentTool()


class VideoSummarizerTool(BaseTool):
    name: str = "Video Summarizer Tool"
    description: str = (
        "Summarizes YouTube or Rumble videos. " "Input: 'video_url' (str)."
    )
    args_schema: Type[VideoSummarizerToolInput] = VideoSummarizerToolInput

    async def _arun(self, input: VideoSummarizerToolInput) -> VideoSummarizerToolOutput:
        try:
            result = await asyncio.to_thread(
                _video_processing_agent_instance.handle_user_input, input.video_url
            )
            if result.get("status") == "success":
                return VideoSummarizerToolOutput(
                    summary=result.get("summary"),
                    full_text=result.get("full_text"),
                )
            else:
                return VideoSummarizerToolOutput(
                    status="error", error=result.get("message", "Failed to summarize video.")
                )
        except Exception as e:
            return VideoSummarizerToolOutput(status="error", error=f"Error in Video Summarizer Tool: {str(e)}")

    def _run(self, input: VideoSummarizerToolInput) -> VideoSummarizerToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(asyncio.to_thread(self._arun, input))
        return asyncio.run(self._arun(input=input))


video_summarizer_tool = VideoSummarizerTool()


class StoryWriterTool(BaseTool):
    name: str = "Story Writer Tool"
    description: str = (
        "Creates a story based on a given book description and initial text content. "
        "Input: 'book_description' (str) and 'text_content' (str)."
    )
    args_schema: Type[StoryWriterToolInput] = StoryWriterToolInput

    async def _arun(self, input: StoryWriterToolInput) -> StoryWriterToolOutput:
        try:
            story_output = await asyncio.to_thread(
                _writer_assistant_instance.create_story,
                input.book_description,
                input.text_content,
            )
            return StoryWriterToolOutput(story_output=story_output)
        except Exception as e:
            return StoryWriterToolOutput(status="error", error=f"Error in Story Writer Tool: {str(e)}")

    def _run(self, input: StoryWriterToolInput) -> StoryWriterToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(
                asyncio.to_thread(self._arun, input)
            )
        return asyncio.run(
            self._arun(input=input)
        )


story_writer_tool = StoryWriterTool()


class BookWriterTool(BaseTool):
    name: str = "Book Writer Tool"
    description: str = (
        "Creates a book based on a given book description, number of chapters, and initial text content. "
        "Input: 'book_description' (str), 'num_chapters' (int), and 'text_content' (str)."
    )
    args_schema: Type[BookWriterToolInput] = BookWriterToolInput

    async def _arun(
        self, input: BookWriterToolInput
    ) -> BookWriterToolOutput:
        try:
            book_output = await asyncio.to_thread(
                _book_writer_instance.create_story,
                input.book_description,
                input.num_chapters,
                input.text_content,
            )
            return BookWriterToolOutput(book_output=book_output)
        except Exception as e:
            return BookWriterToolOutput(status="error", error=f"Error in Book Writer Tool: {str(e)}")

    def _run(self, input: BookWriterToolInput) -> BookWriterToolOutput:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run(
                asyncio.to_thread(
                    self._arun, input
                )
            )
        return asyncio.run(
            self._arun(
                input=input
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
