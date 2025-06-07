from pydantic import BaseModel, Field
from typing import Optional, Dict

# AI Assistant Schemas


class SummarizeYoutubeRequest(BaseModel):
    video_url: str = Field(..., description="The YouTube video URL to summarize.")


class SummarizeYoutubeResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    summary: Optional[str] = Field(None, description="The summarized text.")
    full_text: Optional[str] = Field(None, description="The full transcribed text.")
    message: Optional[str] = Field(None, description="Error or success message.")


class ChatbotRequest(BaseModel):
    mode: str = Field(..., description="The LLM mode (e.g., 'critique', 'reflecting').")
    summary: str = Field(..., description="A short summary of the content.")
    full_text: str = Field(..., description="The full text content for processing.")


class ChatbotResponse(BaseModel):
    result: Optional[str] = Field(
        None, description="The result from the chatbot processing."
    )
    error: Optional[str] = Field(
        None, description="Error message if the operation failed."
    )


class MusicGenerationRequest(BaseModel):
    prompt: str = Field(
        ..., description="Description of the music loop (e.g., 'hip hop beat loop')."
    )
    bpm: int = Field(..., description="Beats per minute for the loop.")
    duration: Optional[int] = Field(30, description="Duration of the loop in seconds.")


class MusicGenerationResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    message: Optional[str] = Field(None, description="Success or error message.")
    file_path: Optional[str] = Field(
        None, description="Path to the generated music file."
    )
    error: Optional[str] = Field(
        None, description="Error message if the operation failed."
    )


class ResearchRequest(BaseModel):
    query: str = Field(..., description="The research query.")


class ResearchResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    result: Optional[str] = Field(None, description="The research result.")
    summary: Optional[str] = Field(
        None, description="The summarized text (for summarization tasks)."
    )
    error: Optional[str] = Field(
        None, description="Error message if the operation failed."
    )


class WebsiteSummarizeRequest(BaseModel):
    url: str = Field(..., description="The URL of the website to summarize.")
    question: str = Field(
        ..., description="The question to ask about the website content."
    )


class WebsiteSummarizeResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    summary: Optional[str] = Field(None, description="The summarized text.")
    keywords: Optional[list[str]] = Field(
        None, description="Keywords extracted from the summary."
    )
    message: Optional[str] = Field(None, description="Error or success message.")


class WebsiteResearchRequest(BaseModel):
    category: str = Field(
        ..., description="The research category (e.g., 'book_research_urls')."
    )
    question: str = Field(..., description="The research question.")


class WebsiteResearchResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    research_result: Optional[str] = Field(None, description="The research result.")
    message: Optional[str] = Field(None, description="Error or success message.")


class WriterTaskRequest(BaseModel):
    task_type: str = Field(
        ..., description="Type of writing task (e.g., 'story', 'book')."
    )
    book_description: Optional[str] = Field(
        None, description="Description of the book/story."
    )
    num_chapters: Optional[int] = Field(
        None, description="Number of chapters for a book."
    )
    text_content: Optional[str] = Field(
        None, description="Initial text content for the story/book."
    )


class WriterTaskResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    output: Optional[str] = Field(None, description="The output of the writing task.")
    message: Optional[str] = Field(None, description="Error or success message.")


# System Assistant Schemas


class SystemCommandRequest(BaseModel):
    command: str = Field(
        ...,
        description="The system command to execute (e.g., 'shutdown', 'open app notepad').",
    )
    # Additional fields for specific commands can be added here if needed
    # For example, for 'open_app', you might have:
    # app_name: Optional[str] = Field(None, description="Name of the application to open.")


class SystemCommandResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/error).")
    message: Optional[str] = Field(
        None, description="Result or error message of the command."
    )
    data: Optional[Dict] = Field(
        None,
        description="Additional data returned by the command (e.g., battery percentage).",
    )
