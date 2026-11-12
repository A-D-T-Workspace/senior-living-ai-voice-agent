import logging
import asyncio

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero

from src.agent.engine import ConversationEngine
from src.agent.livekit_llm import ConversationEngineLLM
from src.config import get_settings
from src.scheduling.service import SchedulingService
from src.storage.conversation_store import ConversationStore
from src.voice.livekit_stt import FasterWhisperSTT
from src.voice.livekit_tts import PiperTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class WillowBrookVoiceAgent(Agent):
    """Voice interface for the WillowBrook demonstration."""

    def __init__(self):
        super().__init__(
            instructions=(
                "You are the voice interface for SeniorLiving AI. "
                "The configured conversation engine controls all caller "
                "responses and applies the complete conversation policy. "
                "Do not generate independent factual answers or invent "
                "information about WillowBrook."
            )
        )

    async def on_enter(self) -> None:
        logger.info("WillowBrook agent on_enter() called")

        await self.session.say(
            "Hello, thank you for joining the WillowBrook Senior Living "
            "demonstration. I'm SeniorLiving AI. How can I help you today?",
            allow_interruptions=True,
            add_to_chat_ctx=True,
        )

        logger.info("WillowBrook greeting submitted to session")

async def entrypoint(ctx: JobContext) -> None:
    """Run one persistent LiveKit conversation."""

    session_id = ctx.job.room.name

    logger.info("Starting voice session: %s", session_id)

    store = ConversationStore(settings.database_url)
    await store.initialize()

    await ctx.connect()

    state = await store.get(session_id)

    if state is None:
        raise RuntimeError(
            f"No conversation state found for session {session_id}."
        )

    if state.status != "active":
        raise RuntimeError(
            f"Conversation session {session_id} is not active."
        )

    scheduling_service = SchedulingService()

    engine = ConversationEngine(
        scheduling_service=scheduling_service,
    )

    conversation_llm = ConversationEngineLLM(
        conversation_engine=engine,
        state=state,
        conversation_store=store,
    )

    session = AgentSession(
        stt=FasterWhisperSTT(),
        vad=silero.VAD.load(
            sample_rate=16000,
            force_cpu=True,
        ),
        llm=conversation_llm,
        tts=PiperTTS(),
    )

    agent = WillowBrookVoiceAgent()

    shutdown_event = asyncio.Event()

    async def on_job_shutdown(reason: str) -> None:
        logger.info("LiveKit job shutting down: %s", reason)
        shutdown_event.set()

    ctx.add_shutdown_callback(on_job_shutdown)

    try:
        await session.start(agent, room=ctx.room)
        await shutdown_event.wait()

    finally:
        try:
            await store.save(state)
            logger.info(
                "Conversation state saved: %s",
                session_id,
            )
        finally:
            await session.aclose()

        logger.info(
            "Voice session closed: %s",
            session_id,
        )

def main() -> None:
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.livekit_url or None,
            api_key=settings.livekit_api_key or None,
            api_secret=settings.livekit_api_secret or None,
        )
    )

if __name__ == "__main__":
    main()
