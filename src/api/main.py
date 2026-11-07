import asyncio
import logging
from collections import OrderedDict
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config import get_settings
from src.conversation.state import create_conversation
from src.conversation.models import ConversationState
from src.voice import VoiceService
from src.scheduling.service import SchedulingService

settings = get_settings()
logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE = 10 * 1024 * 1024
MAX_SESSIONS = 500

app = FastAPI(
    title=settings.app_name,
    description="Intelligent Voice Sales and Appointment Booking Agent",
    version="0.1.0",
    debug=settings.debug,
)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

scheduling_service = SchedulingService()
voice_service = VoiceService(
    scheduling_service=scheduling_service
)
sessions: OrderedDict[str, ConversationState] = OrderedDict()
session_lock = asyncio.Lock()

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "senior-living-ai-api",
    }

@app.post("/sessions")
async def create_session():
    session_id = str(uuid4())

    async with session_lock:
        sessions[session_id] = create_conversation(session_id)

        while len(sessions) > MAX_SESSIONS:
            sessions.popitem(last=False)

    return {
        "session_id": session_id,
        "status": "active",
    }

@app.get("/sessions/{session_id}")
async def inspect_session(session_id: str):
    async with session_lock:
        state = sessions.get(session_id)

        if state is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found.",
            )

        return state.model_dump(mode="json")

@app.post("/voice/process")
async def process_voice(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):

    supported_audio_types = {
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
        "audio/mp4",
    }

    content_type = (audio.content_type or "").split(";")[0].strip().lower()

    if content_type not in supported_audio_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {content_type or 'unknown'}.",
        )

    audio_bytes = await audio.read(MAX_AUDIO_SIZE + 1)

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Audio file cannot be empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file exceeds the 10 MB limit.",
        )

    async with session_lock:
        state = sessions.get(session_id)

        if state is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found.",
            )

        sessions.move_to_end(session_id)

    try:
        result = await voice_service.process_audio(
            state,
            audio_bytes,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Voice processing failed.")

        raise HTTPException(
            status_code=500,
            detail="Voice processing failed. Please try again.",
        ) from exc

    return Response(
        content=result["audio"],
        media_type="audio/wav",
        headers={
            "X-Caller-Text": result["caller_text"][:1000],
            "X-Agent-Response": result["response_text"][:1000],
            "X-Audio-Format": "wav",
        },
    )