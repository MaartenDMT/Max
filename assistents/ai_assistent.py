"""
Enhanced AI Assistant with Memory Management and State Persistence
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from agents.orchestrator_agent import OrchestratorAgent
from agents.chatbot_agent import ChatbotAgent
from agents.music_agent import MusicCreationAgent
from agents.research_agent import AIResearchAgent
from agents.video_agent import VideoProcessingAgent
from ai_tools.agent_tools import BookWriterTool, StoryWriterTool
from ai_tools.speech.speech_to_text import TranscribeFastModel
from ai_tools.crew_tools import WebPageResearcherTool, WebsiteSummarizerTool
from utils.database import Conversation, SessionLocal, init_db
from utils.loggers import LoggerSetup


class DatabaseMemoryManager:
    """Manages persistent memory and conversation context using a database"""

    def __init__(self):
        self.logger = LoggerSetup().get_logger("DatabaseMemoryManager", "memory_manager.log")
        init_db()

    def _db_session(self):
        return SessionLocal()

    def create_session(self, user_id: str = None) -> str:
        """Create a new conversation session in the database"""
        session_id = f"{user_id or 'anonymous'}_{uuid.uuid4().hex[:8]}"
        with self._db_session() as db:
            new_conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(new_conversation)
            db.commit()
            self.logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session context from the database"""
        with self._db_session() as db:
            conversation = db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            ).scalar_one_or_none()
            if conversation:
                return {
                    "session_id": conversation.session_id,
                    "user_preferences": conversation.user_preferences or {},
                    "conversation_history": conversation.conversation_history or [],
                    "last_topics": conversation.last_topics or [],
                    "agent_memory": conversation.agent_memory or {},
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                }
        return None

    def update_session_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context in the database"""
        with self._db_session() as db:
            conversation = db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            ).scalar_one_or_none()
            if conversation:
                conversation.updated_at = datetime.now()
                conversation.user_preferences = context.get("user_preferences", {})
                conversation.conversation_history = context.get("conversation_history", [])
                conversation.last_topics = context.get("last_topics", [])
                conversation.agent_memory = context.get("agent_memory", {})
                db.commit()

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary from the database"""
        context = self.get_session_context(session_id)
        if not context:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "created_at": context["created_at"].isoformat() if context["created_at"] else None,
            "updated_at": context["updated_at"].isoformat() if context["updated_at"] else None,
            "total_interactions": len(context["conversation_history"]),
            "topics_discussed": context["last_topics"],
            "user_preferences": context["user_preferences"],
            "session_duration_minutes": (
                (datetime.now() - context["created_at"]).total_seconds() / 60 
                if context["created_at"] else 0
            ),
        }

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions from the database"""
        with self._db_session() as db:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_delete = db.scalars(
                select(Conversation).where(Conversation.updated_at < cutoff_time)
            ).all()
            for session in sessions_to_delete:
                self.logger.info(f"Cleaned up old session: {session.session_id}")
                db.delete(session)
            db.commit()


class AIAssistant:
    """
    Enhanced AI Assistant with:
    - Persistent memory management
    - Session-based conversations
    - Enhanced orchestration
    - Improved error handling
    - Backward compatibility
    """

    def __init__(self, tts_model=None, transcribe=None, speak=None, listen=None):
        # Legacy compatibility
        self.transcribe = transcribe
        self.tts_model = tts_model
        self._speak = speak
        self._listen = listen

        # Enhanced components
        self.memory_manager = DatabaseMemoryManager()
        self.orchestrator = OrchestratorAgent()

        # Session context
        self.current_session_id = None
        self.session_context = {
            "last_command": None,
            "websites_visited": [],
            "youtube_summaries": [],
            "active_tasks": []
        }

        # Lazy initialize agent instances for backward compatibility
        self._youtube_agent = None
        self._music_agent = None
        self._research_agent = None
        self._chatbot_agent = None

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("AIAssistant", "ai_assistant.log")

        # Legacy agent support
        self.llm_mode = None

        self.logger.info("AI Assistant initialized with enhanced capabilities.")

    def start_new_session(self, user_id: str = None) -> str:
        """Start a new conversation session"""
        session_id = self.memory_manager.create_session(user_id)
        self.current_session_id = session_id
        self.logger.info(f"Started new session: {session_id}")
        return session_id

    def set_session(self, session_id: str) -> bool:
        """Set active session"""
        context = self.memory_manager.get_session_context(session_id)
        if context:
            self.current_session_id = session_id
            self.logger.info(f"Set active session: {session_id}")
            return True
        else:
            self.logger.warning(f"Session not found: {session_id}")
            return False

    async def process_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Process user query with enhanced orchestration"""

        # Use provided session or create new one
        if session_id:
            if not self.set_session(session_id):
                session_id = self.start_new_session()
        else:
            session_id = self.current_session_id or self.start_new_session()

        try:
            # Process with enhanced orchestrator using legacy-style call expected by tests
            resp_obj = await self.orchestrator.run_workflow(query, session_id)
            # Normalize orchestrator output to a string
            if isinstance(resp_obj, str):
                final = resp_obj
                status = "success"
            else:
                final = getattr(resp_obj, "final_response", "")
                status = getattr(resp_obj, "status", "error")
            return {"status": status, "response": final}
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process query: {str(e)}",
                "response": "",
                "session_id": session_id
            }

    # Enhanced API methods with memory awareness

    async def _handle_research_api(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Enhanced research with session memory"""

        session_id = session_id or self.current_session_id or self.start_new_session()

        try:
            # Add research context to query
            enhanced_query = f"Research and analyze: {query}. Provide comprehensive insights and actionable recommendations."

            response = await self.orchestrator.run_workflow(enhanced_query, session_id)
            if not isinstance(response, str):
                response = getattr(response, "final_response", "")

            # Update session context
            context = self.memory_manager.get_session_context(session_id)
            if context:
                context["last_topics"].append(f"Research: {query}")
                context["agent_memory"]["last_research"] = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "summary": response[:100] + "..." if len(response) > 100 else response
                }
                self.memory_manager.update_session_context(session_id, context)

            return {
                "status": "success",
                "research_result": response,
                "session_id": session_id,
                "query": query
            }

        except Exception as e:
            self.logger.error(f"Research API error: {str(e)}")
            return {
                "status": "error",
                "message": f"Research failed: {str(e)}"
            }

    async def _handle_analysis_api(self, data: str, analysis_type: str = "general", session_id: str = None) -> Dict[str, Any]:
        """Enhanced analysis with memory context"""

        session_id = session_id or self.current_session_id or self.start_new_session()

        try:
            # Context-aware analysis prompt
            context = self.memory_manager.get_session_context(session_id)
            context_info = ""

            if context and context["last_topics"]:
                context_info = f"Given our previous discussion about {', '.join(context['last_topics'][-3:])}, "

            enhanced_query = f"{context_info}Please analyze the following data for {analysis_type} insights: {data}"

            response = await self.orchestrator.run_workflow(enhanced_query, session_id)
            if not isinstance(response, str):
                response = getattr(response, "final_response", "")

            # Update session memory
            if context:
                context["last_topics"].append(f"Analysis: {analysis_type}")
                context["agent_memory"]["last_analysis"] = {
                    "type": analysis_type,
                    "timestamp": datetime.now().isoformat(),
                    "summary": response[:100] + "..." if len(response) > 100 else response
                }
                self.memory_manager.update_session_context(session_id, context)

            return {
                "status": "success",
                "analysis_result": response,
                "analysis_type": analysis_type,
                "session_id": session_id
            }

        except Exception as e:
            self.logger.error(f"Analysis API error: {str(e)}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }

    async def _learn_site_api(self, url: str, question: str, session_id: str = None) -> Dict[str, Any]:
        """Enhanced website learning with memory"""

        session_id = session_id or self.current_session_id or self.start_new_session()

        try:
            if not url or not question:
                return {"status": "error", "message": "URL and question are required."}

            # Track visited websites in session
            context = self.memory_manager.get_session_context(session_id)
            if context:
                if "websites_visited" not in context["agent_memory"]:
                    context["agent_memory"]["websites_visited"] = []
                context["agent_memory"]["websites_visited"].append({
                    "url": url,
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                })

            # Use enhanced orchestrator for website analysis
            enhanced_query = f"Analyze the website {url} to answer: {question}. Provide comprehensive insights and key takeaways."

            response = await self.orchestrator.run_workflow(enhanced_query, session_id)
            if not isinstance(response, str):
                response = getattr(response, "final_response", "")

            # Update session context
            if context:
                context["last_topics"].append(f"Website: {url}")
                self.memory_manager.update_session_context(session_id, context)

            return {
                "status": "success",
                "summary": response,
                "url": url,
                "question": question,
                "session_id": session_id
            }

        except Exception as e:
            self.logger.error(f"Website learning error: {str(e)}")
            return {
                "status": "error",
                "message": f"Website analysis failed: {str(e)}"
            }

    async def get_session_insights(self, session_id: str = None) -> Dict[str, Any]:
        """Get insights and summary for current session"""

        session_id = session_id or self.current_session_id
        if not session_id:
            return {"status": "error", "message": "No active session"}

        summary = self.memory_manager.get_session_summary(session_id)
        context = self.memory_manager.get_session_context(session_id)

        insights = {
            "session_summary": summary,
            "key_topics": context["last_topics"] if context else [],
            "recent_activities": context["conversation_history"][-5:] if context and context["conversation_history"] else [],
            "user_preferences": context["user_preferences"] if context else {},
            "agent_memory": context["agent_memory"] if context else {}
        }

        return {
            "status": "success",
            "insights": insights,
            "session_id": session_id
        }

    async def set_user_preference(self, key: str, value: Any, session_id: str = None) -> Dict[str, Any]:
        """Set user preference for session"""

        session_id = session_id or self.current_session_id or self.start_new_session()
        context = self.memory_manager.get_session_context(session_id)

        if context:
            context["user_preferences"][key] = value
            self.memory_manager.update_session_context(session_id, context)
            return {
                "status": "success",
                "message": f"Preference '{key}' set to '{value}'",
                "session_id": session_id
            }
        else:
            return {
                "status": "error",
                "message": "Session not found"
            }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions from the database"""
        with self.memory_manager._db_session() as db:
            sessions = db.scalars(select(Conversation)).all()
            return [self.memory_manager.get_session_summary(s.session_id) for s in sessions]

    # Backwards-compatible methods from original AIAssistant

    async def _summarize_youtube_api(self, video_url: str) -> dict:
        """Handle YouTube summarization task asynchronously for API."""
        try:
            if not video_url:
                self.logger.warning("No YouTube URL provided.")
                return {"status": "error", "message": "No valid YouTube URL provided."}

            self.logger.info(f"Received YouTube URL: {video_url}")
            # Get youtube agent using lazy loading
            youtube_agent = self._load_agent("youtube")
            if youtube_agent is None:
                return {"status": "error", "message": "Failed to load YouTube agent"}

            # Call the async method directly to avoid issues with awaiting a sync method
            result = await youtube_agent._handle_user_input_async(video_url)

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
                    # Get chatbot agent using lazy loading
                    chatbot_agent = self._load_agent("chatbot")
                    if chatbot_agent is None:
                        return {"status": "error", "message": "Failed to load chatbot agent"}

                    critique_result = (
                        await chatbot_agent.process_with_current_mode(
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
            music_agent = self._load_agent("music")
            if music_agent is None:
                return {"status": "error", "message": "Failed to load music agent"}

            # Ensure duration is an int, default to 30 if None (as per schema default)
            actual_duration = duration if duration is not None else 30
            user_input_for_music_agent = (
                f"Generate a {bpm} BPM {prompt} loop for {actual_duration} seconds"
            )
            output = await asyncio.to_thread(
                music_agent.handle_user_request, user_input_for_music_agent
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

    async def _handle_research_api_legacy(self, query: str) -> dict:
        """Handle research-related tasks for API."""
        try:
            if not query:
                return {"status": "error", "message": "No research query provided."}

            self.logger.info(f"Research query: {query}")
            # Get research agent using lazy loading
            research_agent = self._load_agent("research")
            if research_agent is None:
                return {"status": "error", "message": "Failed to load research agent"}

            research_result = await research_agent.handle_research(query)

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

            research_agent = self._load_agent("research")
            if research_agent is None:
                return {"status": "error", "message": "Failed to load research agent"}

            summary_result = await research_agent.handle_text_summarization(
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
        try:
            if agent_type == "youtube":
                if self._youtube_agent is None:
                    # Lazy load transcribe model if needed
                    self._youtube_agent = VideoProcessingAgent(self._get_transcribe())
                    self.logger.info("YouTube agent loaded on demand.")
                return self._youtube_agent
            elif agent_type == "music":
                if self._music_agent is None:
                    self._music_agent = MusicCreationAgent()
                    self.logger.info("Music agent loaded on demand.")
                return self._music_agent
            elif agent_type == "research":
                if self._research_agent is None:
                    self._research_agent = AIResearchAgent()
                    self.logger.info("Research agent loaded on demand.")
                return self._research_agent
            elif agent_type == "chatbot":
                if self._chatbot_agent is None:
                    self._chatbot_agent = ChatbotAgent()  # Load ChatbotAgent
                    self.logger.info("ChatbotAgent loaded on demand.")
                return self._chatbot_agent
            else:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading agent {agent_type}: {str(e)}")
            return None

    def set_llm_mode(self, mode=None) -> dict:
        """Set the LLM mode in ChatbotAgent (e.g., critique, reflecting, casual, professional, etc.)."""
        self.llm_mode = mode
        # List of supported modes
        supported_modes = ["critique", "reflecting", "casual", "professional", "creative", "analytical"]
        if mode in supported_modes:
            self._load_agent("chatbot")
            self.logger.info(f"{mode.capitalize()} mode enabled via ChatbotAgent.")
            return {
                "status": "success",
                "message": f"{mode.capitalize()} mode enabled.",
            }
        else:
            self.llm_mode = None
            self.logger.info("Invalid mode selected, no LLM mode enabled.")
            return {"status": "error", "message": f"Invalid mode selected. Supported modes: {', '.join(supported_modes)}"}

    async def _start_conversation_mode(self, query: str) -> dict:
        """Start a conversation with the chatbot in the specified mode."""
        try:
            # Extract mode from query (e.g., "chat with casual mode" -> "casual")
            query = query.lower().strip()
            mode = None
            
            # Check for specific modes
            if "casual" in query:
                mode = "casual"
            elif "professional" in query:
                mode = "professional"
            elif "creative" in query:
                mode = "creative"
            elif "analytical" in query:
                mode = "analytical"
            elif "critique" in query:
                mode = "critique"
            elif "reflect" in query:
                mode = "reflecting"
            else:
                return {"error": "Please specify a mode: casual, professional, creative, analytical, critique, or reflecting"}
            
            # Set the mode and inform the user
            self.llm_mode = mode
            self._load_agent("chatbot")
            self.logger.info(f"{mode.capitalize()} mode enabled via ChatbotAgent.")
            
            return {
                "status": "success",
                "message": f"Conversation mode set to {mode}. You can now chat with me in this mode.",
                "mode": mode
            }
        except Exception as e:
            self.logger.error(f"Error setting conversation mode: {str(e)}")
            return {"status": "error", "message": f"Error setting conversation mode: {str(e)}"}

    async def _process_conversation_input(self, user_input: str) -> dict:
        """Process user input when in conversation mode."""
        try:
            if not self.llm_mode:
                return {"error": "No conversation mode set. Use 'chat with [mode]' first."}
            
            # Get chatbot agent using lazy loading
            chatbot_agent = self._load_agent("chatbot")
            if chatbot_agent is None:
                return {"error": "Failed to load chatbot agent"}
            
            # Process the conversation
            result = await chatbot_agent.process_conversation_mode(
                self.llm_mode, user_input, []
            )
            
            if "error" in result:
                return {"error": result["error"]}
            
            return {"result": result["result"]}
        except Exception as e:
            self.logger.error(f"Error processing conversation input: {str(e)}")
            return {"error": f"Error processing conversation input: {str(e)}"}

    # Placeholder for speak in API context
    async def _speak_api(self, message: str):
        self.logger.info(f"API Speak: {message}")
        return {"message": message}

    # Placeholder for listen in API context
    async def _listen_api(self):
        self.logger.info("API Listen: No direct listening in API context.")
        return ""

    # Cleanup and maintenance

    def cleanup_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        self.memory_manager.cleanup_old_sessions(max_age_hours)

    def cleanup(self):
        """Clean up resources used by the AI assistant."""
        self.logger.info("Cleaning up AI assistant resources...")
        # Add any necessary cleanup code here
        # For now, we're just logging that cleanup was called
        self.logger.info("AI assistant cleanup completed.")


# Backwards-compatible export expected by tests
# PersistentMemoryManager used to be the name; keep it as an alias to DatabaseMemoryManager
PersistentMemoryManager = DatabaseMemoryManager