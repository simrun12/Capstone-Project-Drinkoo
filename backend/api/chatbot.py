"""RAG-enhanced chatbot routes grounded in DRINKOO company data with semantic search."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .auth import get_current_user
from ..utils.auth import AuthenticatedUser
from ..utils.rag import get_rag_pipeline
from ..utils import observability as obs

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/ask")
def ask_chatbot(
    question: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Ask a RAG-enhanced question about DRINKOO company data.

    Uses semantic search + database queries for accurate, grounded responses.
    Logs every interaction; low-confidence answers are recorded as failures.
    """
    if not question or not question.strip():
        obs.log_event(
            event_type="chatbot_empty_question",
            category="chatbot",
            severity="warning",
            user=current_user.username,
            session_id=request.headers.get("x-session-id"),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty",
        )

    started = time.perf_counter()
    rag = get_rag_pipeline()
    result = rag.query(question.strip())
    duration_ms = int((time.perf_counter() - started) * 1000)

    confidence = result.get("confidence", "low")
    source = result.get("source")
    kb_context = result.get("kb_context")
    similarity = None
    if isinstance(kb_context, dict):
        similarity = kb_context.get("similarity")

    obs.log_event(
        event_type="chatbot_query",
        category="chatbot",
        severity="info" if confidence != "low" else "warning",
        user=current_user.username,
        session_id=request.headers.get("x-session-id"),
        path="/api/v1/chatbot/ask",
        duration_ms=duration_ms,
        success=confidence != "low",
        details={
            "question_length": len(question),
            "source": source,
            "confidence": confidence,
            "similarity": similarity,
        },
    )

    if confidence == "low":
        obs.log_chatbot_failure(
            question=question.strip(),
            answer=result.get("answer"),
            source=source,
            confidence=confidence,
            failure_reason="low_confidence_response",
            similarity_score=similarity,
            duration_ms=duration_ms,
            user=current_user.username,
            session_id=request.headers.get("x-session-id"),
        )

    return {
        "question": question,
        "answer": result["answer"],
        "source": result["source"],
        "confidence": confidence,
        "context": kb_context,
    }


@router.get("/context")
def get_chatbot_context(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    """Get information about available chatbot capabilities and knowledge base."""
    rag = get_rag_pipeline()
    kb_info = rag.get_kb_info()

    return {
        "knowledge_base": kb_info,
        "example_questions": [
            "How many customers does DRINKOO have?",
            "How many customers are in Maharashtra?",
            "Which SKU is the top seller?",
            "How many pending shipments are there?",
            "What states does DRINKOO serve?",
            "How do I track a shipment?",
            "What are SKU sizes?",
        ],
        "capabilities": [
            "Answer questions about customer distribution by state",
            "Identify top-performing SKUs",
            "Check shipment status distribution",
            "Provide company information",
            "Guide users on system features",
        ],
        "response_types": [
            "Database-grounded answers (high confidence)",
            "Knowledge-base answers (medium confidence)",
            "Helpful suggestions (low confidence)",
        ]
    }


@router.get("/kb-info")
def get_kb_info(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    """Get detailed knowledge base information."""
    rag = get_rag_pipeline()
    return {
        "knowledge_base_summary": rag.get_kb_info(),
        "message": "Knowledge base is loaded and ready for semantic search"
    }
