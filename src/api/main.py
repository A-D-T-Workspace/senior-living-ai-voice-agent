import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.config import get_settings
from src.conversation.state import create_conversation
from src.storage.conversation_store import ConversationStore
from src.voice import VoiceService
from src.scheduling.service import SchedulingService
from datetime import timedelta
from livekit.api import AccessToken, VideoGrants

settings = get_settings()
logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE = 10 * 1024 * 1024

conversation_store = ConversationStore()

session_locks: dict[str, asyncio.Lock] = {}
session_locks_guard = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await conversation_store.initialize()
    yield

app = FastAPI(
    title=settings.app_name,
    description="Intelligent Voice Sales and Appointment Booking Agent",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
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

async def get_session_lock(session_id: str) -> asyncio.Lock:
    async with session_locks_guard:
        if session_id not in session_locks:
            session_locks[session_id] = asyncio.Lock()

        return session_locks[session_id]

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
    state = create_conversation(session_id)

    await conversation_store.save(state)

    return {
        "session_id": session_id,
        "status": "active",
    }

@app.post("/sessions/{session_id}/livekit-token")
async def create_livekit_token(session_id: str):
    if not all([
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret,
    ]):
        raise HTTPException(
            status_code=503,
            detail="LiveKit is not configured.",
        )

    state = await conversation_store.get(session_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation session not found.",
        )

    if state.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Conversation session is not active.",
        )

    identity = f"visitor-{uuid4().hex}"

    token = (
        AccessToken(
            settings.livekit_api_key,
            settings.livekit_api_secret,
        )
        .with_identity(identity)
        .with_ttl(timedelta(minutes=15))
        .with_grants(
            VideoGrants(
                room_join=True,
                room=session_id,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=False,
            )
        )
    )

    return {
        "server_url": settings.livekit_url,
        "participant_token": token.to_jwt(),
        "identity": identity,
    }

@app.get("/sessions/{session_id}")
async def inspect_session(session_id: str):
    state = await conversation_store.get(session_id)

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

    content_type = (
        (audio.content_type or "")
        .split(";")[0]
        .strip()
        .lower()
    )

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

    session_lock = await get_session_lock(session_id)

    async with session_lock:
        state = await conversation_store.get(session_id)

        if state is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation session not found.",
            )

        try:
            result = await voice_service.process_audio(
                state,
                audio_bytes,
            )

            await conversation_store.save(state)

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
