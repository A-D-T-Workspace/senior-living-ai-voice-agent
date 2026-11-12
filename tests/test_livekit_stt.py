import pytest

from src.voice.livekit_stt import FasterWhisperSTT

class FakeAudioFrame:
    def to_wav_bytes(self):
        return b"fake-audio"

class FakeBuffer:
    samples_per_channel = 16000
    sample_rate = 16000

class FakeTranscriber:
    def __init__(self, language):
        self.language = language

    async def transcribe_with_language(self, audio_bytes):
        assert audio_bytes == b"fake-audio"

        return {
            "text": "Test transcription",
            "language": self.language,
        }

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "language",
    ["en", "yo", "ig", "ha"],
)
async def test_livekit_stt_preserves_detected_language(
    monkeypatch,
    language,
):
    from src.voice import livekit_stt

    monkeypatch.setattr(
        livekit_stt.utils,
        "combine_frames",
        lambda buffer: FakeAudioFrame(),
    )

    adapter = FasterWhisperSTT(
        transcriber=FakeTranscriber(language)
    )

    result = await adapter._recognize_impl(FakeBuffer())

    assert len(result.alternatives) == 1
    assert result.alternatives[0].text == "Test transcription"
    assert result.alternatives[0].language == language

@pytest.mark.asyncio
async def test_livekit_stt_handles_empty_transcription(monkeypatch):
    from src.voice import livekit_stt

    monkeypatch.setattr(
        livekit_stt.utils,
        "combine_frames",
        lambda buffer: FakeAudioFrame(),
    )

    class EmptyTranscriber:
        async def transcribe_with_language(self, audio_bytes):
            raise ValueError("No speech could be detected.")

    adapter = FasterWhisperSTT(transcriber=EmptyTranscriber())

    result = await adapter._recognize_impl(FakeBuffer())

    assert result.alternatives == []
