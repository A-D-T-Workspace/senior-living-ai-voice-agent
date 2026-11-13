import uuid

from livekit.agents import llm
from livekit.agents.types import APIConnectOptions

from src.agent.engine import ConversationEngine
from src.conversation.models import ConversationState
from src.storage.conversation_store import ConversationStore

class ConversationEngineLLM(llm.LLM):
    """LiveKit LLM adapter backed by the existing ConversationEngine."""

    def __init__(
        self,
        conversation_engine: ConversationEngine,
        state: ConversationState,
        conversation_store: ConversationStore | None = None,
        language_context: dict | None = None,
    ):
        super().__init__()
        self._engine = conversation_engine
        self._state = state
        self._conversation_store = conversation_store
        self._language_context = language_context or {"language": "en"}

    @property
    def model(self) -> str:
        return "ollama-conversation-engine"

    @property
    def provider(self) -> str:
        return "local-ollama"

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = APIConnectOptions(),
        parallel_tool_calls=None,
        tool_choice=None,
        extra_kwargs=None,
    ) -> llm.LLMStream:
        return ConversationEngineLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )

class ConversationEngineLLMStream(llm.LLMStream):
    """Runs the existing conversation engine and emits its response."""

    async def _run(self) -> None:
        messages = self._chat_ctx.messages()

        latest_user_message = next(
            (
                message.text_content
                for message in reversed(messages)
                if message.role == "user" and message.text_content
            ),
            None,
        )

        if not latest_user_message:
            raise ValueError("No caller message found in LiveKit chat context.")

        response = await self._llm._engine.respond(
            self._llm._state,
            latest_user_message,
            language=self._llm._language_context.get("language", "en"),
        )

        if self._llm._conversation_store is not None:
            await self._llm._conversation_store.save(
                self._llm._state
            )

        self._event_ch.send_nowait(
            llm.ChatChunk(
                id=str(uuid.uuid4()),
                delta=llm.ChoiceDelta(
                    role="assistant",
                    content=response,
                ),
            )
        )
