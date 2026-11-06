import asyncio
import logging
from io import BytesIO

from faster_whisper import WhisperModel

from src.config import get_settings

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Transcribes caller audio using faster-whisper."""

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

    def _transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise ValueError("Audio input cannot be empty.")

        model = self._load_model()

        segments, _ = model.transcribe(
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

        return text

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio without blocking the async event loop."""
        return await asyncio.to_thread(self._transcribe, audio_bytes)