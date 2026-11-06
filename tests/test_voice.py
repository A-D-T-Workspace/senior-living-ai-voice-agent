import pytest

from src.conversation.models import ConversationState
from src.voice.service import VoiceService

class FakeTranscriber:
    async def transcribe(self, audio_bytes):
        assert audio_bytes == b"fake-audio"
        return "I would like to arrange a tour."

class FakeSynthesizer:
    async def synthesize(self, text):
        assert text == "I can help arrange a tour."
        return b"fake-wav-audio"

class FakeConversationEngine:
    async def respond(self, state, caller_message):
        assert caller_message == "I would like to arrange a tour."
        return "I can help arrange a tour."

@pytest.mark.asyncio
async def test_voice_service_processes_audio():
    state = ConversationState(session_id="test-session")

    service = VoiceService(
        conversation_engine=FakeConversationEngine(),
        transcriber=FakeTranscriber(),
        synthesizer=FakeSynthesizer(),
    )

    result = await service.process_audio(
        state,
        b"fake-audio",
    )

    assert result["caller_text"] == (
        "I would like to arrange a tour."
    )
    assert result["response_text"] == (
        "I can help arrange a tour."
    )
    assert result["audio"] == b"fake-wav-audio"
    assert result["audio_format"] == "wav"

@pytest.mark.asyncio
async def test_voice_service_preserves_conversation_state():
    state = ConversationState(session_id="test-session")

    service = VoiceService(
        conversation_engine=FakeConversationEngine(),
        transcriber=FakeTranscriber(),
        synthesizer=FakeSynthesizer(),
    )

    await service.process_audio(state, b"fake-audio")

    assert state.session_id == "test-session"