"""
Enhanced API Router with Memory Management and Session Support
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.schemas import (AnalysisRequest, AnalysisResponse, QueryRequest,
                         QueryResponse, ResearchRequest, ResearchResponse,
                         WebsiteRequest, WebsiteResponse)
from assistents.enhanced_ai_assistant import EnhancedAIAssistant

# Enhanced request/response models with session support

class SessionRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User identifier for session")
    session_id: Optional[str] = Field(None, description="Existing session ID")


class SessionResponse(BaseModel):
    status: str
    session_id: str
    message: str
    created_at: str


class EnhancedQueryRequest(QueryRequest):
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for this query")
    context_aware: bool = Field(True, description="Use conversation context")


class EnhancedQueryResponse(QueryResponse):
    session_id: str
    conversation_context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None


class SessionInsightsRequest(BaseModel):
    session_id: Optional[str] = None


class SessionInsightsResponse(BaseModel):
    status: str
    insights: Dict[str, Any]
    session_id: str


class PreferenceRequest(BaseModel):
    key: str
    value: Any
    session_id: Optional[str] = None


class PreferenceResponse(BaseModel):
    status: str
    message: str
    session_id: str


# Global assistant instance
enhanced_assistant = EnhancedAIAssistant()

# Create enhanced router
enhanced_ai_router = APIRouter(prefix="/enhanced-ai", tags=["Enhanced AI Assistant"])


@enhanced_ai_router.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """Create a new conversation session with memory"""
    try:
        session_id = enhanced_assistant.start_new_session(request.user_id)

        return SessionResponse(
            status="success",
            session_id=session_id,
            message="Session created successfully",
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@enhanced_ai_router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status and basic info"""
    try:
        summary = enhanced_assistant.memory_manager.get_session_summary(session_id)

        if "error" in summary:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": "active",
            "session_info": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


@enhanced_ai_router.post("/query", response_model=EnhancedQueryResponse)
async def enhanced_query(request: EnhancedQueryRequest):
    """Process query with enhanced memory and context awareness"""
    try:
        # Set user preferences if provided
        if request.user_preferences and request.session_id:
            for key, value in request.user_preferences.items():
                await enhanced_assistant.set_user_preference(key, value, request.session_id)

        # Process the query
        result = await enhanced_assistant.process_query(
            request.query,
            request.session_id
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        # Get conversation context if requested
        context = None
        if request.context_aware:
            insights = await enhanced_assistant.get_session_insights(result["session_id"])
            if insights["status"] == "success":
                context = insights["insights"]

        return EnhancedQueryResponse(
            status="success",
            response=result["response"],
            timestamp=result["timestamp"],
            session_id=result["session_id"],
            conversation_context=context,
            suggestions=_generate_suggestions(request.query, context)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@enhanced_ai_router.post("/research", response_model=ResearchResponse)
async def enhanced_research(request: ResearchRequest):
    """Enhanced research with session memory"""
    try:
        result = await enhanced_assistant._handle_research_api(
            request.query,
            getattr(request, 'session_id', None)
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return ResearchResponse(
            status="success",
            research_result=result["research_result"],
            timestamp=datetime.now().isoformat(),
            query=result["query"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@enhanced_ai_router.post("/analysis", response_model=AnalysisResponse)
async def enhanced_analysis(request: AnalysisRequest):
    """Enhanced analysis with context awareness"""
    try:
        result = await enhanced_assistant._handle_analysis_api(
            request.data,
            getattr(request, 'analysis_type', 'general'),
            getattr(request, 'session_id', None)
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return AnalysisResponse(
            status="success",
            analysis_result=result["analysis_result"],
            analysis_type=result["analysis_type"],
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@enhanced_ai_router.post("/website/analyze", response_model=WebsiteResponse)
async def enhanced_website_analysis(request: WebsiteRequest):
    """Enhanced website analysis with memory tracking"""
    try:
        result = await enhanced_assistant._learn_site_api(
            request.url,
            request.question,
            getattr(request, 'session_id', None)
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return WebsiteResponse(
            status="success",
            summary=result["summary"],
            url=result["url"],
            question=result["question"],
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")


@enhanced_ai_router.post("/session/insights", response_model=SessionInsightsResponse)
async def get_session_insights(request: SessionInsightsRequest):
    """Get comprehensive session insights and memory"""
    try:
        insights = await enhanced_assistant.get_session_insights(request.session_id)

        if insights["status"] == "error":
            raise HTTPException(status_code=404, detail=insights["message"])

        return SessionInsightsResponse(
            status="success",
            insights=insights["insights"],
            session_id=insights["session_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@enhanced_ai_router.post("/session/preference", response_model=PreferenceResponse)
async def set_user_preference(request: PreferenceRequest):
    """Set user preference for session"""
    try:
        result = await enhanced_assistant.set_user_preference(
            request.key,
            request.value,
            request.session_id
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return PreferenceResponse(
            status="success",
            message=result["message"],
            session_id=result["session_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set preference: {str(e)}")


@enhanced_ai_router.get("/sessions/active")
async def get_active_sessions():
    """Get list of all active sessions"""
    try:
        sessions = enhanced_assistant.get_active_sessions()
        return {
            "status": "success",
            "active_sessions": sessions,
            "total_count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@enhanced_ai_router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a conversation session"""
    try:
        context = enhanced_assistant.memory_manager.get_session_context(session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")

        # Remove session from memory
        if session_id in enhanced_assistant.memory_manager.sessions:
            del enhanced_assistant.memory_manager.sessions[session_id]

        return {
            "status": "success",
            "message": f"Session {session_id} ended successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@enhanced_ai_router.post("/sessions/cleanup")
async def cleanup_old_sessions(background_tasks: BackgroundTasks, max_age_hours: int = 24):
    """Clean up old sessions (background task)"""
    try:
        background_tasks.add_task(enhanced_assistant.cleanup_sessions, max_age_hours)
        return {
            "status": "success",
            "message": f"Cleanup task scheduled for sessions older than {max_age_hours} hours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule cleanup: {str(e)}")


@enhanced_ai_router.get("/session/{session_id}/export")
async def export_session_data(session_id: str):
    """Export session data for backup or analysis"""
    try:
        context = enhanced_assistant.memory_manager.get_session_context(session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")

        export_data = {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "conversation_context": context.model_dump() if hasattr(context, "model_dump") else dict(context),
            "session_summary": enhanced_assistant.memory_manager.get_session_summary(session_id)
        }

        return export_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")


@enhanced_ai_router.get("/health")
async def health_check():
    """Enhanced health check with memory status"""
    try:
        # Get active sessions count from the database
        active_sessions = len(enhanced_assistant.get_active_sessions())

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "enhanced_assistant": "operational",
                "memory_manager": "operational",
                "orchestrator": "operational"
            },
            "metrics": {
                "active_sessions": active_sessions,
                "memory_enabled": enhanced_assistant.orchestrator.enable_memory
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Streaming response for long-running tasks
@enhanced_ai_router.post("/query/stream")
async def stream_enhanced_query(request: EnhancedQueryRequest):
    """Stream query response for real-time interaction"""

    async def generate_stream():
        try:
            # Start processing
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Starting query processing...'})}\n\n"

            # Process query
            result = await enhanced_assistant.process_query(request.query, request.session_id)

            if result["status"] == "error":
                yield f"data: {json.dumps({'status': 'error', 'message': result['message']})}\n\n"
                return

            # Stream response in chunks
            response_text = result["response"]
            chunk_size = 50

            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield f"data: {json.dumps({'status': 'streaming', 'chunk': chunk})}\n\n"
                await asyncio.sleep(0.1)  # Small delay for streaming effect

            # Final response
            yield f"data: {json.dumps({'status': 'complete', 'session_id': result['session_id']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/plain")


# Helper functions

def _generate_suggestions(query: str, context: Optional[Dict[str, Any]]) -> List[str]:
    """Generate follow-up suggestions based on query and context"""

    suggestions = []
    query_lower = query.lower()

    # Basic suggestions based on query type
    if "research" in query_lower:
        suggestions.extend([
            "Analyze the research findings",
            "Get more specific data on this topic",
            "Compare with alternative approaches"
        ])
    elif "analyze" in query_lower or "analysis" in query_lower:
        suggestions.extend([
            "Explore implementation strategies",
            "Identify potential risks",
            "Research related case studies"
        ])
    elif "explain" in query_lower or "how" in query_lower:
        suggestions.extend([
            "Get practical examples",
            "Learn about best practices",
            "Explore related concepts"
        ])

    # Context-based suggestions
    if context and "key_topics" in context:
        topics = context["key_topics"]
        if topics:
            recent_topic = topics[-1] if topics else ""
            suggestions.append(f"Continue exploring {recent_topic}")

    return suggestions[:3]  # Return max 3 suggestions
