import asyncio
import wave
from pathlib import Path

from src.voice.synthesizer import SpeechSynthesizer

async def main():
    synthesizer = SpeechSynthesizer()

    text = (
        "Hello, and welcome to WillowBrook Senior Living. "
        "I can help you learn about our community "
        "and arrange an introductory tour."
    )

    audio = await synthesizer.synthesize(text)

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "piper_test.wav"
    output_path.write_bytes(audio)

    with wave.open(str(output_path), "rb") as wav:
        print("\nPIPER AUDIO TEST")
        print("----------------")
        print(f"File: {output_path}")
        print(f"Channels: {wav.getnchannels()}")
        print(f"Sample rate: {wav.getframerate()} Hz")
        print(f"Sample width: {wav.getsampwidth()} bytes")
        print(f"Duration: {wav.getnframes() / wav.getframerate():.2f} seconds")
        print(f"File size: {output_path.stat().st_size:,} bytes")

if __name__ == "__main__":
    asyncio.run(main())