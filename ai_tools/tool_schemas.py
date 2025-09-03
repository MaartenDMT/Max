from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, Literal, List
from pydantic.types import conint

# Base Tool Response Model
class ToolResponse(BaseModel):
    status: str = Field("success", description="Status of the tool operation (success/error).")
    message: Optional[str] = Field(None, description="Status message or details.")
    error: Optional[str] = Field(None, description="Error message if the operation failed.")

# Chatbot Tool
class ChatbotToolInput(BaseModel):
    mode: Literal["critique", "reflecting"] = Field(..., description="The LLM mode.")
    summary: str = Field(..., description="A short summary of the content.")
    full_text: str = Field(..., description="The full text content for processing.")

class ChatbotToolOutput(ToolResponse):
    result: Optional[str] = Field(None, description="The result from the chatbot processing.")

# Music Generation Tool
class MusicGenerationToolInput(BaseModel):
    bpm: conint(ge=40, le=240) = Field(..., description="Beats per minute for the loop (40-240).")
    prompt: str = Field(..., description="Description of the music loop (e.g., 'hip hop beat loop').")
    duration: Optional[conint(ge=5, le=300)] = Field(30, description="Duration of the loop in seconds (5-300).")

class MusicGenerationToolOutput(ToolResponse):
    file_path: Optional[str] = Field(None, description="Path to the generated music file.")

# Research Agent Tool
class ResearchAgentToolInput(BaseModel):
    query: str = Field(..., min_length=3, description="The research query (min 3 chars).")

class ResearchAgentToolOutput(ToolResponse):
    research_result: Optional[str] = Field(None, description="The research result.")

# Video Summarizer Tool
class VideoSummarizerToolInput(BaseModel):
    video_url: HttpUrl = Field(..., description="The video URL to summarize (YouTube or Rumble).")

class VideoSummarizerToolOutput(ToolResponse):
    summary: Optional[str] = Field(None, description="The summarized text.")
    full_text: Optional[str] = Field(None, description="The full transcribed text.")

# Story Writer Tool
class StoryWriterToolInput(BaseModel):
    book_description: str = Field(..., description="Description of the book/story.")
    text_content: str = Field(..., description="Initial text content for the story/book.")

class StoryWriterToolOutput(ToolResponse):
    story_output: Optional[str] = Field(None, description="The output of the writing task.")

# Book Writer Tool
class BookWriterToolInput(BaseModel):
    book_description: str = Field(..., description="Description of the book/story.")
    num_chapters: conint(ge=1) = Field(..., description="Number of chapters for a book.")
    text_content: str = Field(..., description="Initial text content for the story/book.")

class BookWriterToolOutput(ToolResponse):
    book_output: Optional[str] = Field(None, description="The output of the writing task.")

# Website Summarize Tool (from lc_tools.py)
class WebsiteSummarizeToolInput(BaseModel):
    url: HttpUrl = Field(..., description="The web page URL.")
    question: str = Field(..., description="The question to answer from the page.")

class WebsiteSummarizeToolOutput(ToolResponse):
    summary: Optional[str] = Field(None, description="The summarized text.")
    keywords: Optional[List[str]] = Field(None, description="Keywords extracted from the summary.")

# Web Research Tool (from lc_tools.py)
class WebResearchToolInput(BaseModel):
    category: str = Field(..., description="Research category or topic bucket.")
    question: str = Field(..., description="Concrete research question.")

class WebResearchToolOutput(ToolResponse):
    research_result: Optional[str] = Field(None, description="The research result.")

# Research Tool (general, from lc_tools.py)
class ResearchToolInput(BaseModel):
    query: str = Field(..., description="Research prompt or question.")

class ResearchToolOutput(ToolResponse):
    output: Optional[str] = Field(None, description="The research result.")
