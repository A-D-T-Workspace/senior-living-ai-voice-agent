import pytest

from src.agent.llm import OllamaClient
from src.agent.instructions import SYSTEM_INSTRUCTIONS

@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_generates_response():
    client = OllamaClient()

    messages = [
    {
        "role": "system",
        "content": SYSTEM_INSTRUCTIONS,
    },
    {
        "role": "user",
        "content": (
            "A caller is looking for a safe living arrangement "
            "for their 82-year-old mother. Respond empathetically "
            "and ask one thoughtful follow-up question."
        ),
    },
]

    response = await client.chat(messages)

    assert isinstance(response, str)
    assert len(response.strip()) > 0

    print("\nLlama response:")
    print(response)
