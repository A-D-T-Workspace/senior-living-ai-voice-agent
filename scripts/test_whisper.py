import asyncio
from pathlib import Path

from src.voice.transcriber import AudioTranscriber

async def main():
    audio_path = Path("outputs/piper_test.wav")

    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    audio_bytes = audio_path.read_bytes()

    transcriber = AudioTranscriber()
    transcription = await transcriber.transcribe(audio_bytes)

    print("\nWHISPER TRANSCRIPTION TEST")
    print("--------------------------")
    print("Original audio: outputs/piper_test.wav")
    print(f"Transcription: {transcription}")

if __name__ == "__main__":
    asyncio.run(main())