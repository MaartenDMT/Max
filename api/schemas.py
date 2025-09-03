from typing import Dict, Literal, Optional, List, Any, Union

from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic.types import conint

# Base Response Models
class BaseResponse(BaseModel):
    status: Literal["success", "error"] = Field(..., description="Status of the operation (success/error).")
    message: Optional[str] = Field(None, description="Status message or error details.")

class ErrorResponse(BaseResponse):
    status: Literal["error"] = "error"
    code: Optional[int] = Field(None, description="Error code if applicable")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")

# AI Assistant Schemas


class SummarizeYoutubeRequest(BaseModel):
    video_url: HttpUrl = Field(..., description="The video URL to summarize (YouTube or Rumble).")


class SummarizeYoutubeResponse(BaseResponse):
    summary: Optional[str] = Field(None, description="The summarized text.")
    full_text: Optional[str] = Field(None, description="The full transcribed text.")


class ChatbotRequest(BaseModel):
    mode: Literal["critique", "reflecting"] = Field(..., description="The LLM mode.")
    summary: str = Field(..., description="A short summary of the content.")
    full_text: str = Field(..., description="The full text content for processing.")


class ChatbotResponse(BaseResponse):
    result: Optional[str] = Field(
        None, description="The result from the chatbot processing."
    )


class MusicGenerationRequest(BaseModel):
    prompt: str = Field(
        ..., description="Description of the music loop (e.g., 'hip hop beat loop')."
    )
    bpm: conint(ge=40, le=240) = Field(..., description="Beats per minute for the loop (40-240).")
    duration: Optional[conint(ge=5, le=300)] = Field(30, description="Duration of the loop in seconds (5-300).")


class MusicGenerationResponse(BaseResponse):
    file_path: Optional[str] = Field(
        None, description="Path to the generated music file."
    )


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The research query (min 3 chars).")


class ResearchResponse(BaseResponse):
    result: Optional[str] = Field(None, description="The research result.")
    summary: Optional[str] = Field(
        None, description="The summarized text (for summarization tasks)."
    )


class WebsiteSummarizeRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL of the website to summarize.")
    question: str = Field(
        ..., description="The question to ask about the website content."
    )


class WebsiteSummarizeResponse(BaseResponse):
    summary: Optional[str] = Field(None, description="The summarized text.")
    keywords: Optional[List[str]] = Field(
        None, description="Keywords extracted from the summary."
    )


class WebsiteResearchRequest(BaseModel):
    category: str = Field(
        ..., description="The research category (e.g., 'book_research_urls')."
    )
    question: str = Field(..., description="The research question.")


class WebsiteResearchResponse(BaseResponse):
    research_result: Optional[str] = Field(None, description="The research result.")


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


class WriterTaskResponse(BaseResponse):
    output: Optional[str] = Field(None, description="The output of the writing task.")


# System Assistant Schemas


class SystemCommandRequest(BaseModel):
    command: str = Field(
        ...,
        description="The system command to execute (e.g., 'shutdown', 'open app notepad').",
    )
    # Additional fields for specific commands can be added here if needed
    # For example, for 'open_app', you might have:
    # app_name: Optional[str] = Field(None, description="Name of the application to open.")


class SystemCommandResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional data returned by the command (e.g., battery percentage).",
    )


# Orchestrator Schemas
class OrchestratorRunWorkflowRequest(BaseModel):
    query: str = Field(..., description="The user's query or prompt.")
    session_id: Optional[str] = Field("default", description="Optional session ID for conversation memory.")


class OrchestratorRunWorkflowResponse(BaseResponse):
    final_response: Optional[str] = Field(None, description="The final response from the orchestrator.")
    session_id: Optional[str] = Field(None, description="The session ID associated with the response.")


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's query or prompt.")

class QueryResponse(BaseResponse):
    response: Optional[str] = Field(None, description="The AI's response.")
    timestamp: str = Field(..., description="Timestamp of the response.")

class AnalysisRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to be analyzed.")
    analysis_type: Optional[str] = Field("general", description="Type of analysis to perform.")

class AnalysisResponse(BaseResponse):
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="Result of the analysis.")
    analysis_type: Optional[str] = Field(None, description="Type of analysis performed.")
    timestamp: str = Field(..., description="Timestamp of the analysis.")

class WebsiteRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL of the website to analyze.")
    question: Optional[str] = Field(None, description="Specific question about the website content.")

class WebsiteResponse(BaseResponse):
    summary: Optional[str] = Field(None, description="Summary of the website content.")
    url: HttpUrl = Field(..., description="URL of the analyzed website.")
    question: Optional[str] = Field(None, description="Question asked about the website content.")
    timestamp: str = Field(..., description="Timestamp of the analysis.")
