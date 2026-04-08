from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import asyncio
import json

from app.core.logger import logger

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[list] = None


@router.post("/query")
async def chat_query(request: ChatRequest):
    """
    Send a query to the AI assistant
    """
    logger.info(f"Chat query: {request.message[:50]}...")

    # Simple echo response for now (will be replaced with RAG)
    response_text = f"I received your query: '{request.message}'. I'll process it with RAG soon!"

    if request.stream:
        return StreamingResponse(
            stream_response(request.message, request.session_id),
            media_type="text/event-stream"
        )

    return ChatResponse(
        response=response_text,
        session_id=request.session_id or "default",
        sources=[]
    )


async def stream_response(message: str, session_id: Optional[str]) -> AsyncGenerator[str, None]:
    """Stream response character by character"""
    response = f"Processing: {message}\n\n"

    for char in response:
        yield json.dumps({"token": char}) + "\n"
        await asyncio.sleep(0.05)


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    return {
        "session_id": session_id,
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"}
        ]
    }