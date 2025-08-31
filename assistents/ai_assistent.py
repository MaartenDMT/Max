import asyncio
import json
from typing import Optional

from agents.chatbot_agent import ChatbotAgent
from agents.music_agent import MusicCreationAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.research_agent import AIResearchAgent
from agents.video_agent import VideoProcessingAgent
from ai_tools.agent_tools import BookWriterTool, StoryWriterTool

# Import the necessary BaseTools directly
from ai_tools.crew_tools import WebPageResearcherTool, WebsiteSummarizerTool

# Removed: from agents.webpage_agent import WebsiteProcessingAgent
# Removed: from agents.writer_agent import AIWriterAgent
from utils.loggers import LoggerSetup


class AIAssistant:
    def __init__(self, tts_model, transcribe, speak, listen):
        self.transcribe = transcribe
        self.tts_model = tts_model

        # These will be placeholders for API context
        self._speak = speak
        self._listen = listen

        # Store agent context for session
        self.session_context = {
            "last_command": None,
            "websites_visited": [],
            "youtube_summaries": [],
        }

        # Initialize OrchestratorAgent
        self.orchestrator_agent = OrchestratorAgent()

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("AIAssistant", "ai_assistant.log")

        # llm mode
        self.llm_mode = None

        # Log initialization
        self.logger.info("AI Assistant initialized.")

    # Placeholder for speak in API context
    async def _speak_api(self, message: str):
        self.logger.info(f"API Speak: {message}")
        return {"message": message}

    # Placeholder for listen in API context
    async def _listen_api(self):
        self.logger.info("API Listen: No direct listening in API context.")
        return ""

    def set_llm_mode(self, mode=None) -> dict:
        """Set the LLM mode in ChatbotAgent (e.g., critique, reflecting)."""
        self.llm_mode = mode
        if mode in ["critique", "reflecting"]:
            self._load_agent("chatbot")
            self.logger.info(f"{mode.capitalize()} mode enabled via ChatbotAgent.")
            return {
                "status": "success",
                "message": f"{mode.capitalize()} mode enabled.",
            }
        else:
            self.llm_mode = None
            self.logger.info("Invalid mode selected, no LLM mode enabled.")
            return {"status": "error", "message": "Invalid mode selected."}

    # API-compatible methods for each functionality

    async def _handle_chatbot_api(
        self, mode: str, summary: str, full_text: str
    ) -> dict:
        """Handle chatbot-related tasks for API."""
        try:
            self._load_agent("chatbot")
            result = await self.chatbot_agent.process_with_current_mode(
                mode, summary, full_text
            )
            return {"result": result.get("result"), "error": result.get("error")}
        except Exception as e:
            self.logger.error(f"Error during chatbot task: {str(e)}")
            return {"error": f"Error during chatbot task: {str(e)}"}

    async def _summarize_youtube_api(self, video_url: str) -> dict:
        """Handle YouTube summarization task asynchronously for API."""
        try:
            if not video_url:
                self.logger.warning("No YouTube URL provided.")
                return {"status": "error", "message": "No valid YouTube URL provided."}

            self.logger.info(f"Received YouTube URL: {video_url}")
            self._load_agent("youtube")

            result = await asyncio.to_thread(
                self.youtube_agent.handle_user_input, video_url
            )

            # Ensure result is a dictionary before proceeding
            if not isinstance(result, dict):
                self.logger.error(
                    f"YouTube summarization returned non-dict result: {result}"
                )
                return {
                    "status": "error",
                    "message": "Unexpected summarization result format.",
                }

            if result.get("status") == "success":
                full_text = str(result.get("full_text", ""))  # Ensure string
                summary = str(result.get("summary", ""))  # Ensure string

                if self.llm_mode is not None:
                    self._load_agent("chatbot")
                    critique_result = (
                        await self.chatbot_agent.process_with_current_mode(
                            self.llm_mode, summary, full_text
                        )
                    )
                    summary_with_critique = {
                        "summary": summary,
                        "critique": critique_result.get("result"),
                        "critique_error": critique_result.get("error"),
                    }
                    self.logger.info("YouTube video summarized with critique")
                    return {
                        "status": "success",
                        "summary": json.dumps(summary_with_critique),
                        "full_text": full_text,
                    }
                else:
                    self.logger.info("YouTube video summarized")
                    return {
                        "status": "success",
                        "summary": summary,
                        "full_text": full_text,
                    }
            else:
                self.logger.error(
                    f"YouTube summarization failed: {result.get('message')}"
                )
                return {
                    "status": "error",
                    "message": result.get("message", "Failed to summarize video."),
                }
        except Exception as e:
            self.logger.error(f"Error during YouTube summarization: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred during summarization: {str(e)}",
            }

    async def _learn_site_api(self, url: str, question: str) -> dict:
        """Handle website summarization task for API."""
        try:
            if not url:
                return {"status": "error", "message": "No website URL provided."}
            if not question:
                return {"status": "error", "message": "No question provided."}

            self.logger.info(f"Received website URL: {url} with question: {question}")
            self.session_context["websites_visited"].append(url)
            # Directly use WebsiteSummarizerTool (async-safe)
            summarizer_tool = WebsiteSummarizerTool()
            result = await summarizer_tool._arun(
                url=url, question=question
            )

            # Ensure result is a dictionary before proceeding
            if not isinstance(result, dict):
                try:  # Attempt to parse if it's a JSON string
                    result = json.loads(result)
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Website summarization returned non-dict/non-json result: {result}"
                    )
                    return {
                        "status": "error",
                        "message": "Unexpected summarization result format.",
                    }

            if result.get("summary"):  # Check for 'summary' key in the result
                self.logger.info(f"Website summarized: {result.get('summary')}")
                return {
                    "status": "success",
                    "summary": result.get("summary"),
                    "keywords": result.get("keywords"),
                }
            else:
                self.logger.warning("No summary generated for the website.")
                return {
                    "status": "error",
                    "message": result.get(
                        "error", "Sorry, I couldn't generate a summary."
                    ),
                }
        except Exception as e:
            self.logger.error(f"Error during site summarization: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred while processing the website: {str(e)}",
            }

    async def _research_site_api(self, category: str, question: str) -> dict:
        """Handle website research task for API."""
        try:
            if not category:
                return {"status": "error", "message": "No research category provided."}
            if not question:
                return {"status": "error", "message": "No research question provided."}

            self.logger.info(
                f"Received research category: {category} with question: {question}"
            )
            # Directly use WebPageResearcherTool (async-safe)
            researcher_tool = WebPageResearcherTool()
            result = await researcher_tool._arun(
                category=category, question=question
            )

            # Ensure result is a dictionary before proceeding
            if not isinstance(result, dict):
                try:  # Attempt to parse if it's a JSON string
                    result = json.loads(result)
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Website research returned non-dict/non-json result: {result}"
                    )
                    return {
                        "status": "error",
                        "message": "Unexpected research result format.",
                    }

            if result.get("research_result"):  # Check for 'research_result' key
                self.logger.info(f"Research result: {result.get('research_result')}")
                return {
                    "status": "success",
                    "research_result": result.get("research_result"),
                }
            else:
                self.logger.warning("No research result generated.")
                return {
                    "status": "error",
                    "message": result.get(
                        "error", "Sorry, I couldn't perform the research."
                    ),
                }
        except Exception as e:
            self.logger.error(f"Error during site research: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred while processing the research: {str(e)}",
            }

    async def _make_loop_api(
        self, prompt: str, bpm: int, duration: Optional[int] = 30
    ) -> dict:
        """Handle music loop generation task for API."""
        try:
            if not prompt or not bpm:
                return {
                    "status": "error",
                    "message": "Invalid prompt or BPM for music loop.",
                }

            self.logger.info(f"Music loop request with prompt: {prompt} and BPM: {bpm}")
            self._load_agent("music")

            # Ensure duration is an int, default to 30 if None (as per schema default)
            actual_duration = duration if duration is not None else 30
            user_input_for_music_agent = (
                f"Generate a {bpm} BPM {prompt} loop for {actual_duration} seconds"
            )
            output = await asyncio.to_thread(
                self.music_agent.handle_user_request, user_input_for_music_agent
            )

            if output.get("status") == "success":
                self.logger.info(f"Music loop generated: {output.get('file_path')}")
                return {
                    "status": "success",
                    "message": output.get("message"),
                    "file_path": output.get("file_path"),
                }
            else:
                self.logger.warning(
                    f"Music loop generation failed: {output.get('message')}"
                )
                return {
                    "status": "error",
                    "message": output.get("message", "Failed to generate music loop."),
                }
        except Exception as e:
            self.logger.error(f"Error during loop making: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred during loop making: {str(e)}",
            }

    async def _handle_research_api(self, query: str) -> dict:
        """Handle research-related tasks for API."""
        try:
            if not query:
                return {"status": "error", "message": "No research query provided."}

            self.logger.info(f"Research query: {query}")
            self._load_agent("research")

            research_result = await self.research_agent.handle_research(query)

            if research_result.get("status") == "success":
                self.logger.info(f"Research result: {research_result.get('result')}")
                return {"status": "success", "result": research_result.get("result")}
            else:
                self.logger.error(f"Research failed: {research_result.get('message')}")
                return {
                    "status": "error",
                    "message": research_result.get(
                        "message", "Failed to perform research."
                    ),
                }
        except Exception as e:
            self.logger.error(f"Error during research task: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred during research: {str(e)}",
            }

    async def _handle_summarization_api(self, text_to_summarize: str) -> dict:
        """Handle text summarization for API."""
        try:
            if not text_to_summarize:
                return {
                    "status": "error",
                    "message": "No text provided for summarization.",
                }

            self.logger.info("Text summarization request received.")
            self._load_agent("research")

            summary_result = await self.research_agent.handle_text_summarization(
                text_to_summarize
            )

            if summary_result.get("status") == "success":
                self.logger.info(f"Summarized text: {summary_result.get('summary')}")
                return {"status": "success", "summary": summary_result.get("summary")}
            else:
                self.logger.error(
                    f"Text summarization failed: {summary_result.get('message')}"
                )
                return {
                    "status": "error",
                    "message": summary_result.get(
                        "message", "Failed to summarize text."
                    ),
                }
        except Exception as e:
            self.logger.error(f"Error during text summarization: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred during summarization: {str(e)}",
            }

    async def _handle_writer_task_api(
        self,
        task_type: str,
        book_description: Optional[str] = None,
        num_chapters: Optional[int] = None,
        text_content: Optional[str] = None,
    ) -> dict:
        """Handle writing-related tasks for API."""
        try:
            # Directly use StoryWriterTool or BookWriterTool
            if task_type == "story":
                if not book_description or not text_content:
                    return {
                        "status": "error",
                        "message": "For 'story' task, 'book_description' and 'text_content' are required.",
                    }
                writer_tool = StoryWriterTool()
                story_output = await writer_tool._arun(
                    book_description=book_description, text_content=text_content
                )
                # The _run method of StoryWriterTool returns a JSON string, so parse it
                try:
                    story_output_dict = json.loads(story_output)
                    return {
                        "status": "success",
                        "output": story_output_dict.get("story_output"),
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Failed to parse story output.",
                    }
            elif task_type == "book":
                if not book_description or not num_chapters or not text_content:
                    return {
                        "status": "error",
                        "message": "For 'book' task, 'book_description', 'num_chapters', and 'text_content' are required.",
                    }
                book_tool = BookWriterTool()
                book_output = await book_tool._arun(
                    book_description=book_description,
                    num_chapters=num_chapters,
                    text_content=text_content,
                )
                # The _run method of BookWriterTool returns a JSON string, so parse it
                try:
                    book_output_dict = json.loads(book_output)
                    return {
                        "status": "success",
                        "output": book_output_dict.get("book_output"),
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Failed to parse book output.",
                    }
            else:
                return {
                    "status": "error",
                    "message": "Invalid writer task type. Please specify 'story' or 'book'.",
                }
        except Exception as e:
            self.logger.error(f"Error during writing task: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred during writing task: {str(e)}",
            }

    def _load_agent(self, agent_type):
        """Load the specific agent when it's first needed."""
        if agent_type == "youtube" and not hasattr(self, "youtube_agent"):
            self.youtube_agent = VideoProcessingAgent(self.transcribe)
            self.logger.info("YouTube agent loaded.")
        # Removed: elif agent_type == "website" and not hasattr(self, "web_agent"):
        # Removed:     self.web_agent = WebsiteProcessingAgent()
        # Removed:     self.logger.info("Website agent loaded.")
        elif agent_type == "music" and not hasattr(self, "music_agent"):
            self.music_agent = MusicCreationAgent()
            self.logger.info("Music agent loaded.")
        elif agent_type == "research" and not hasattr(self, "research_agent"):
            self.research_agent = AIResearchAgent()
            self.logger.info("AIResearchAgent loaded.")
        elif agent_type == "chatbot" and not hasattr(self, "chatbot_agent"):
            self.chatbot_agent = ChatbotAgent()  # Load ChatbotAgent
            self.logger.info("ChatbotAgent loaded.")
        # Removed: elif agent_type == "writer assistent" and not hasattr(self, "writer_agent"):
        # Removed:     self.writer_agent = AIWriterAgent(speak=lambda x: x)
        # Removed:     self.logger.info("AIWriterAssistant loaded.")
