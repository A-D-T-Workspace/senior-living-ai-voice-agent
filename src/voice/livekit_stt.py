import uuid
import logging

from livekit.agents import stt, utils

from src.voice.transcriber import AudioTranscriber

logger = logging.getLogger(__name__)

class FasterWhisperSTT(stt.STT):
    """LiveKit STT adapter with automatic multilingual detection."""

    def __init__(self, transcriber=None):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False,
                offline_recognize=True,
            )
        )

        self._transcriber = transcriber or AudioTranscriber()

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language=None,
        conn_options=None,
    ) -> stt.SpeechEvent:

        logger.info("STT transcription invoked")
        logger.info(
            "STT received audio frame: %d samples at %d Hz",
            buffer.samples_per_channel,
            buffer.sample_rate,
        )

        audio_frame = utils.combine_frames(buffer)
        audio_bytes = audio_frame.to_wav_bytes()

        try:
            result = await self._transcriber.transcribe_with_language(
                audio_bytes
            )

            text = result["text"]
            detected_language = result["language"]

            logger.info(
                "STT transcription successful. Language: %s | Text: %s",
                detected_language,
                text,
            )

        except ValueError as exc:
            logger.warning("STT produced no transcript: %s", exc)
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                request_id=str(uuid.uuid4()),
                alternatives=[],
            )

        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            request_id=str(uuid.uuid4()),
            alternatives=[
                stt.SpeechData(
                    language=detected_language,
                    text=text,
                    confidence=0.0,
                )
            ],
        )
