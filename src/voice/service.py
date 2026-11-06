from src.agent.engine import ConversationEngine
from src.conversation.models import ConversationState
from src.voice.transcriber import AudioTranscriber
from src.voice.synthesizer import SpeechSynthesizer
from src.scheduling.service import SchedulingService

class VoiceService:
    """Connects speech recognition, conversation, and speech synthesis."""

    def __init__(
        self,
        conversation_engine=None,
        transcriber=None,
        synthesizer=None,
        scheduling_service=None,
    ):
        self.engine = conversation_engine or ConversationEngine(
            scheduling_service=scheduling_service
        )
        self.transcriber = transcriber or AudioTranscriber()
        self.synthesizer = synthesizer or SpeechSynthesizer()
        
    async def process_audio(
        self,
        state: ConversationState,
        audio_bytes: bytes,
    ) -> dict:
        """Process caller audio and return text plus generated speech."""

        caller_text = await self.transcriber.transcribe(audio_bytes)

        response_text = await self.engine.respond(
            state,
            caller_text,
        )

        response_audio = await self.synthesizer.synthesize(
            response_text
        )

        return {
            "caller_text": caller_text,
            "response_text": response_text,
            "audio": response_audio,
            "audio_format": "wav",
        }