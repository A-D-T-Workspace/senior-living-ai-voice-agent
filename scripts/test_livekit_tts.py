import asyncio
import wave
from pathlib import Path

from src.voice.livekit_tts import PiperTTS

async def main():
    adapter = PiperTTS()

    stream = adapter.synthesize(
        "Hello, welcome to our senior living community."
    )

    audio = await stream.collect()

    output_path = Path("outputs/livekit_tts_test.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(audio.num_channels)
        wav.setsampwidth(2)
        wav.setframerate(audio.sample_rate)
        wav.writeframes(audio.data.tobytes())

    print("Audio generated successfully.")
    print("Sample rate:", audio.sample_rate)
    print("Channels:", audio.num_channels)
    print("Saved:", output_path)

if __name__ == "__main__":
    asyncio.run(main())