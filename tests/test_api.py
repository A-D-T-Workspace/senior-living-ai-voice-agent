import pytest
from fastapi.testclient import TestClient

from src.api import main

class FakeVoiceService:
    async def process_audio(self, state, audio_bytes):
        assert audio_bytes == b"fake-browser-audio"

        return {
            "caller_text": "I would like to arrange a tour.",
            "response_text": "I can help arrange a tour.",
            "audio": b"fake-wav-response",
            "audio_format": "wav",
        }

@pytest.fixture
def client(monkeypatch, tmp_path):
    from src.storage.conversation_store import ConversationStore

    store = ConversationStore(
        f"sqlite:///{tmp_path / 'test_api.db'}"
    )

    import asyncio
    asyncio.run(store.initialize())

    monkeypatch.setattr(
        main,
        "conversation_store",
        store,
    )

    monkeypatch.setattr(
        main,
        "voice_service",
        FakeVoiceService(),
    )

    return TestClient(main.app)

@pytest.mark.parametrize(
    "content_type",
    [
        "audio/wav",
        "audio/webm",
        "audio/webm;codecs=opus",
    ],
)
def test_voice_endpoint_accepts_supported_audio(client, content_type):
    session = client.post("/sessions")
    session_id = session.json()["session_id"]

    response = client.post(
        "/voice/process",
        data={"session_id": session_id},
        files={
            "audio": (
                "recording.webm",
                b"fake-browser-audio",
                content_type,
            )
        },
    )

    assert response.status_code == 200
    assert response.content == b"fake-wav-response"
    assert response.headers["content-type"] == "audio/wav"

def test_voice_endpoint_rejects_unsupported_audio(client):
    session = client.post("/sessions")
    session_id = session.json()["session_id"]

    response = client.post(
        "/voice/process",
        data={"session_id": session_id},
        files={
            "audio": (
                "recording.txt",
                b"fake-browser-audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415