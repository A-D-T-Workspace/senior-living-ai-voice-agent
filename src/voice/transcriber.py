import asyncio
import logging
from io import BytesIO

from faster_whisper import WhisperModel

from src.config import get_settings

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Transcribes caller audio and returns detected language metadata."""

    def __init__(self, model=None):
        self._model = model
        self._settings = get_settings()

    def _load_model(self):
        if self._model is None:
            self._model = WhisperModel(
                self._settings.whisper_model,
                device="cpu",
                compute_type="int8",
            )
        return self._model

    def _transcribe_with_language(self, audio_bytes: bytes) -> dict:
        if not audio_bytes:
            raise ValueError("Audio input cannot be empty.")

        model = self._load_model()

        segments, info = model.transcribe(
            BytesIO(audio_bytes),
            beam_size=5,
            vad_filter=True,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        )

        if not text:
            raise ValueError("No speech could be detected in the audio.")

        language = info.language

        logger.info(
            "Transcription completed. Detected language: %s",
            language,
        )

        return {
            "text": text,
            "language": language,
        }

    def _transcribe(self, audio_bytes: bytes) -> str:
        """Preserve the existing synchronous plain-text interface."""
        return self._transcribe_with_language(audio_bytes)["text"]

    async def transcribe_with_language(self, audio_bytes: bytes) -> dict:
        """Transcribe audio and return text with detected language."""
        return await asyncio.to_thread(
            self._transcribe_with_language,
            audio_bytes,
        )

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Preserve the existing asynchronous plain-text interface."""
        result = await self.transcribe_with_language(audio_bytes)
        return result["text"]
