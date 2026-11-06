import uuid
import asyncio

from src.agent.engine import ConversationEngine
from src.conversation.state import create_conversation

async def main():
    message = (
        "My mother is 82 years old. "
        "She currently lives with me, but we are looking "
        "for a private suite because she would prefer her own space."
    )

    engine = ConversationEngine()
    state = create_conversation(session_id=str(uuid.uuid4()))
    
    await engine._extract_discovery_answers(state, message)

    print("\nHYBRID DISCOVERY EXTRACTION RESULTS")
    print("=" * 50)

    for question, answer in state.discovery_answers.items():
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer}")

if __name__ == "__main__":
    asyncio.run(main())
