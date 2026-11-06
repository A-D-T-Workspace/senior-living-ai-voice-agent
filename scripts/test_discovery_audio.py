from pathlib import Path

from src.voice.synthesizer import SpeechSynthesizer

def main():
    text = (
        "My mother is 82 years old. "
        "She currently lives with me, but we are looking "
        "for a private suite because she would prefer her own space."
    )

    synthesizer = SpeechSynthesizer()
    audio = synthesizer._synthesize(text)

    output_path = Path("outputs/discovery_test.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)

    print("Discovery test audio generated successfully.")
    print(f"Saved to: {output_path}")
    print(f"Audio size: {len(audio):,} bytes")

if __name__ == "__main__":
    main()