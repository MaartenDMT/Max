"""
Enhanced AI Assistant with Memory Management and State Persistence
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.enhanced_orchestrator_agent import (
    ConversationContext,
    EnhancedOrchestratorAgent,
)
from utils.loggers import LoggerSetup


class PersistentMemoryManager:
    """Manages persistent memory and conversation context"""

    def __init__(self, storage_path: str = "data/memory"):
        self.storage_path = storage_path
        self.sessions: Dict[str, ConversationContext] = {}
        self.logger = LoggerSetup().get_logger("MemoryManager", "memory_manager.log")

    def create_session(self, user_id: str = None) -> str:
        """Create a new conversation session"""
        session_id = f"{user_id or 'anonymous'}_{uuid.uuid4().hex[:8]}"
        context = ConversationContext(session_id=session_id)
        self.sessions[session_id] = context
        self.logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session_context(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve session context"""
        return self.sessions.get(session_id)

    def update_session_context(self, session_id: str, context: ConversationContext):
        """Update session context"""
        context.updated_at = datetime.now()
        self.sessions[session_id] = context

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        context = self.sessions.get(session_id)
        if not context:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "total_interactions": len(context.conversation_history),
            "topics_discussed": context.last_topics,
            "user_preferences": context.user_preferences,
            "session_duration_minutes": (datetime.now() - context.created_at).total_seconds() / 60
        }

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        current_time = datetime.now()
        sessions_to_remove = []

        for session_id, context in self.sessions.items():
            age_hours = (current_time - context.updated_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            self.logger.info(f"Cleaned up old session: {session_id}")


class EnhancedAIAssistant:
    """
    Enhanced AI Assistant with:
    - Persistent memory management
    - Session-based conversations
    - Enhanced orchestration
    - Improved error handling
    """

    def __init__(self, tts_model=None, transcribe=None, speak=None, listen=None):
        # Legacy compatibility
        self.transcribe = transcribe
        self.tts_model = tts_model
        self._speak = speak
        self._listen = listen

        # Enhanced components
        self.memory_manager = PersistentMemoryManager()
        self.orchestrator = EnhancedOrchestratorAgent(enable_memory=True)

        # Session context
        self.current_session_id = None
        self.session_context = {
            "last_command": None,
            "websites_visited": [],
            "youtube_summaries": [],
            "active_tasks": []
        }

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("EnhancedAIAssistant", "enhanced_ai_assistant.log")

        # Legacy agent support
        self.llm_mode = None

        self.logger.info("Enhanced AI Assistant initialized with memory management.")

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
            # Process with enhanced orchestrator
            response = await self.orchestrator.run_workflow(query, session_id)

            # Update session context
            context = self.memory_manager.get_session_context(session_id)
            if context:
                context.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "response": response[:200] + "..." if len(response) > 200 else response
                })
                self.memory_manager.update_session_context(session_id, context)

            return {
                "status": "success",
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process query: {str(e)}",
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

            # Update session context
            context = self.memory_manager.get_session_context(session_id)
            if context:
                context.last_topics.append(f"Research: {query}")
                context.agent_memory["last_research"] = {
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

            if context and context.last_topics:
                context_info = f"Given our previous discussion about {', '.join(context.last_topics[-3:])}, "

            enhanced_query = f"{context_info}Please analyze the following data for {analysis_type} insights: {data}"

            response = await self.orchestrator.run_workflow(enhanced_query, session_id)

            # Update session memory
            if context:
                context.last_topics.append(f"Analysis: {analysis_type}")
                context.agent_memory["last_analysis"] = {
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
                if "websites_visited" not in context.agent_memory:
                    context.agent_memory["websites_visited"] = []
                context.agent_memory["websites_visited"].append({
                    "url": url,
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                })

            # Use enhanced orchestrator for website analysis
            enhanced_query = f"Analyze the website {url} to answer: {question}. Provide comprehensive insights and key takeaways."

            response = await self.orchestrator.run_workflow(enhanced_query, session_id)

            # Update session context
            if context:
                context.last_topics.append(f"Website: {url}")
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
            "key_topics": context.last_topics if context else [],
            "recent_activities": context.conversation_history[-5:] if context else [],
            "user_preferences": context.user_preferences if context else {},
            "agent_memory": context.agent_memory if context else {}
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
            context.user_preferences[key] = value
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
        """Get list of active sessions"""

        sessions = []
        for session_id in self.memory_manager.sessions.keys():
            summary = self.memory_manager.get_session_summary(session_id)
            sessions.append(summary)

        return sessions

    # Legacy compatibility methods

    def set_llm_mode(self, mode=None) -> dict:
        """Legacy LLM mode setting"""
        self.llm_mode = mode
        return {
            "status": "success" if mode in ["critique", "reflecting"] else "error",
            "message": f"Mode set to {mode}" if mode in ["critique", "reflecting"] else "Invalid mode"
        }

    async def _handle_chatbot_api(self, mode: str, summary: str, full_text: str) -> dict:
        """Legacy chatbot handler"""
        session_id = self.current_session_id or self.start_new_session()
        query = f"As a {mode} assistant, analyze: {summary}. Full context: {full_text}"
        return await self.process_query(query, session_id)

    # Cleanup and maintenance

    def cleanup_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        self.memory_manager.cleanup_old_sessions(max_age_hours)

    async def _speak_api(self, message: str):
        """API speak placeholder"""
        self.logger.info(f"API Speak: {message}")
        return {"message": message}

    async def _listen_api(self):
        """API listen placeholder"""
        self.logger.info("API Listen: No direct listening in API context.")
        return ""


# Usage example and testing
if __name__ == "__main__":
    async def test_enhanced_assistant():
        assistant = EnhancedAIAssistant()

        print("\n--- Testing Enhanced AI Assistant ---")

        # Test session management
        session_id = assistant.start_new_session("test_user")
        print(f"Created session: {session_id}")

        # Test basic query
        result1 = await assistant.process_query("Hello, I'm interested in AI trends", session_id)
        print(f"Query 1 Result: {result1}")

        # Test research with memory
        result2 = await assistant._handle_research_api("latest developments in machine learning", session_id)
        print(f"Research Result: {result2}")

        # Test analysis with context
        result3 = await assistant._handle_analysis_api("ML trends data from research", "strategic", session_id)
        print(f"Analysis Result: {result3}")

        # Test session insights
        insights = await assistant.get_session_insights(session_id)
        print(f"Session Insights: {insights}")

        # Test user preferences
        pref_result = await assistant.set_user_preference("analysis_depth", "detailed", session_id)
        print(f"Preference Set: {pref_result}")

        # Test active sessions
        active_sessions = assistant.get_active_sessions()
        print(f"Active Sessions: {active_sessions}")

    asyncio.run(test_enhanced_assistant())
