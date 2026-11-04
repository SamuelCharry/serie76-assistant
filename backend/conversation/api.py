"""REST contract for Android. Debug is opt-in and separate from public history."""

import os
from threading import BoundedSemaphore
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from backend.auth.api import require_user

from backend.app.contracts import ConversationRequest, ConversationResponse
from backend.catalog.db import connect
from .agent import AgentUnavailable, InvalidInteraction, run_agent
from . import store

router = APIRouter(prefix="/api")
CAPACITY = BoundedSemaphore(4)


def unavailable():
    return HTTPException(503, "Conversation service unavailable. Check backend configuration and try again.")


@router.get("/sessions")
def sessions(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=1000000), user=Depends(require_user)):
    try:
        with connect() as connection:
            return {"sessions": store.list_sessions(connection, limit, offset, owner_id=user["id"]), "limit": limit, "offset": offset}
    except psycopg.Error:
        raise unavailable() from None


@router.get("/sessions/{session_id}/messages")
def messages(session_id: UUID, limit: int = Query(100, ge=1, le=100), before: int | None = Query(None, ge=1), user=Depends(require_user)):
    try:
        with connect() as connection:
            session = store.get_session(connection, session_id, user["id"])
            rows = store.history(connection, session_id, limit + 1, before, owner_id=user["id"])
            has_more = len(rows) > limit
            rows = rows[-limit:]
            return {"session_id": session_id, "title": session["title"], "messages": rows,
                    "has_more": has_more, "next_before": rows[0]["sequence"] if rows and has_more else None}
    except store.MissingSession:
        raise HTTPException(404, "Conversation not found") from None
    except psycopg.Error:
        raise unavailable() from None


@router.post("/conversation", response_model=ConversationResponse)
def conversation(request: ConversationRequest, user=Depends(require_user)):
    if not CAPACITY.acquire(blocking=False):
        raise HTTPException(503, "The assistant is busy. Please try again shortly.")
    try:
        session_id = request.session_id or uuid4()
        with connect() as connection:
            with connection.transaction():
                # Reject a foreign identifier before locking or invoking the model.
                if request.session_id:
                    store.get_session(connection, session_id, user["id"])
                store.lock_session(connection, session_id)
                if request.session_id:
                    store.get_session(connection, session_id, user["id"])
                history = store.history(connection, session_id, 12, internal=True, owner_id=user["id"])
                context = store.recent_context(connection, session_id, user["id"])
                result = run_agent(connection, request.query, history, context, answers=request.answers,
                                   remove_filters=request.remove_filters, user_name=user.get("name"), action=request.action)
                message_id = store.append_turn(connection, session_id, request.query, result, new=request.session_id is None, owner_id=user["id"])
        return ConversationResponse(session_id=session_id, answer=result.answer,
                                    message_id=message_id, products=result.products,
                                    clarification=result.clarification, terms=result.terms,
                                    assumptions=result.assumptions,
                                    suggested_replies=result.suggested_replies, comparison=result.comparison,
                                    lead=result.lead, interaction=result.interaction,
                                    suggestions=result.suggestions, active_filters=result.active_filters,
                                    recommendation=result.recommendation)
    except InvalidInteraction as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc), "error_code": exc.code})
    except store.MissingSession:
        raise HTTPException(404, "Conversation not found") from None
    except store.BusySession:
        raise HTTPException(409, "A response is already being prepared for this conversation.") from None
    except AgentUnavailable as exc:
        # Nothing was persisted: the transaction rolled back with the failed turn.
        return JSONResponse(status_code=503, content={
            "detail": "Conversation service unavailable. Check backend configuration and try again.",
            "error_code": exc.code})
    except psycopg.Error:
        raise unavailable() from None
    finally:
        CAPACITY.release()


@router.get("/messages/{message_id}/debug", include_in_schema=False)
def debug(message_id: UUID, user=Depends(require_user)):
    if os.environ.get("DEV_DEBUG", "false").lower() != "true":
        raise HTTPException(404, "Not found")
    try:
        with connect() as connection:
            row = store.debug_for_message(connection, message_id, user["id"])
            if row is None:
                raise HTTPException(404, "Response not found")
            return row
    except psycopg.Error:
        raise unavailable() from None
