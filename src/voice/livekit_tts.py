import asyncio
import uuid
import wave

from io import BytesIO

from livekit import rtc
from livekit.agents import tts
from livekit.agents.types import APIConnectOptions

from src.voice.synthesizer import SpeechSynthesizer

class PiperTTS(tts.TTS):
    """LiveKit TTS adapter backed by the existing Piper synthesizer."""

    def __init__(self, synthesizer=None):
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=False,
                aligned_transcript=False,
            ),
            sample_rate=22050,
            num_channels=1,
        )

        self._synthesizer = synthesizer or SpeechSynthesizer()

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = APIConnectOptions(),
    ) -> tts.ChunkedStream:
        return PiperChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
        )

class PiperChunkedStream(tts.ChunkedStream):
    """Converts Piper WAV output into LiveKit audio frames."""

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        wav_bytes = await self._tts._synthesizer.synthesize(
            self._input_text
        )

        with wave.open(BytesIO(wav_bytes), "rb") as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            pcm_data = wav.readframes(wav.getnframes())

        if sample_rate != 22050:
            raise ValueError(
                f"Unexpected Piper sample rate: {sample_rate}"
            )

        if channels != 1 or sample_width != 2:
            raise ValueError(
                "Piper must produce mono, 16-bit PCM audio."
            )

        samples_per_frame = sample_rate // 50
        bytes_per_frame = samples_per_frame * channels * sample_width

        output_emitter.initialize(
            request_id=str(uuid.uuid4()),
            sample_rate=sample_rate,
            num_channels=channels,
            mime_type="audio/pcm",
            stream=False,
        )

        for offset in range(0, len(pcm_data), bytes_per_frame):
            frame_data = pcm_data[
                offset:offset + bytes_per_frame
            ]

            samples = len(frame_data) // (channels * sample_width)

            if samples == 0:
                continue

            frame = rtc.AudioFrame(
                data=frame_data,
                sample_rate=sample_rate,
                num_channels=channels,
                samples_per_channel=samples,
            )

            output_emitter.push_frame(frame)
