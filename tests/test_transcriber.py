import pytest

from src.voice.transcriber import AudioTranscriber

class FakeSegment:
    def __init__(self, text):
        self.text = text

class FakeTranscriptionInfo:
    def __init__(self, language):
        self.language = language

class FakeWhisperModel:
    def __init__(self, text, language):
        self.text = text
        self.language = language

    def transcribe(self, audio, **kwargs):
        return (
            iter([FakeSegment(self.text)]),
            FakeTranscriptionInfo(self.language),
        )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "language",
    ["en", "yo", "ig", "ha"],
)
async def test_transcribe_with_language_returns_detected_language(language):
    transcriber = AudioTranscriber(
        model=FakeWhisperModel(
            text="Test transcription",
            language=language,
        )
    )

    result = await transcriber.transcribe_with_language(b"fake-audio")

    assert result["text"] == "Test transcription"
    assert result["language"] == language

def test_transcribe_preserves_plain_text_interface():
    transcriber = AudioTranscriber(
        model=FakeWhisperModel(
            text="Hello there",
            language="en",
        )
    )

    result = transcriber._transcribe(b"fake-audio")

    assert result == "Hello there"

def test_transcribe_rejects_empty_audio():
    transcriber = AudioTranscriber(
        model=FakeWhisperModel(
            text="Hello",
            language="en",
        )
    )

    with pytest.raises(ValueError, match="Audio input cannot be empty"):
        transcriber._transcribe(b"")