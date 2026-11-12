from livekit.agents import llm

from src.agent.livekit_llm import ConversationEngineLLM
from src.conversation.state import create_conversation

class FakeConversationEngine:
    async def respond(self, state, caller_message):
        assert caller_message == "I would like to learn about your community."
        return "Of course. I would be happy to tell you about our community."

async def test_livekit_llm_generates_response():
    state = create_conversation("livekit-test-session")

    adapter = ConversationEngineLLM(
        conversation_engine=FakeConversationEngine(),
        state=state,
    )

    context = llm.ChatContext()
    context.add_message(
        role="user",
        content="I would like to learn about your community.",
    )

    stream = adapter.chat(chat_ctx=context)
    response = await stream.collect()

    assert response.text == (
        "Of course. I would be happy to tell you about our community."
    )