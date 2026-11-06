import asyncio
import logging
import wave
from io import BytesIO
from pathlib import Path

import numpy as np
from piper import PiperVoice

from src.config import get_settings

logger = logging.getLogger(__name__)

class SpeechSynthesizer:
    """Generates WAV speech using a local Piper voice."""

    def __init__(self, voice=None):
        self._voice = voice
        self._settings = get_settings()

    def _load_voice(self):
        if self._voice is None:
            model_path = Path(self._settings.piper_voice)

            if not model_path.is_file():
                raise FileNotFoundError(
                    f"Piper voice model not found: {model_path}"
                )

            self._voice = PiperVoice.load(model_path)

        return self._voice

    def _synthesize(self, text: str) -> bytes:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        voice = self._load_voice()
        chunks = list(voice.synthesize(text.strip()))

        if not chunks:
            raise RuntimeError("Piper generated no audio.")

        sample_rate = chunks[0].sample_rate
        sample_width = chunks[0].sample_width
        channels = chunks[0].sample_channels

        if any(
            chunk.sample_rate != sample_rate
            or chunk.sample_width != sample_width
            or chunk.sample_channels != channels
            for chunk in chunks
        ):
            raise RuntimeError("Piper returned inconsistent audio formats.")

        audio = np.concatenate(
            [chunk.audio_float_array for chunk in chunks],
            axis=0,
        )

        if sample_width != 2:
            raise RuntimeError(
                f"Unsupported Piper sample width: {sample_width}"
            )

        pcm = (
            np.clip(audio, -1.0, 1.0) * 32767
        ).astype("<i2")

        buffer = BytesIO()

        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(sample_width)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())

        return buffer.getvalue()

    async def synthesize(self, text: str) -> bytes:
        """Generate WAV audio without blocking the event loop."""
        return await asyncio.to_thread(self._synthesize, text)