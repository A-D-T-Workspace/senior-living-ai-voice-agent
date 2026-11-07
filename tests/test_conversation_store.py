import pytest

from src.conversation.models import ConversationState
from src.storage.conversation_store import ConversationStore

@pytest.mark.asyncio
async def test_conversation_can_be_saved_and_retrieved(tmp_path):
    store = ConversationStore(
        f"sqlite:///{tmp_path / 'test.db'}"
    )
    await store.initialize()

    state = ConversationState(session_id="session-001")
    state.caller.first_name = "Eric"

    await store.save(state)

    retrieved = await store.get("session-001")

    assert retrieved is not None
    assert retrieved.session_id == "session-001"
    assert retrieved.caller.first_name == "Eric"

@pytest.mark.asyncio
async def test_conversation_persists_across_store_instances(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"

    first_store = ConversationStore(database_url)
    await first_store.initialize()

    state = ConversationState(session_id="session-002")
    await first_store.save(state)

    second_store = ConversationStore(database_url)
    await second_store.initialize()

    retrieved = await second_store.get("session-002")

    assert retrieved is not None
    assert retrieved.session_id == "session-002"

@pytest.mark.asyncio
async def test_missing_conversation_returns_none(tmp_path):
    store = ConversationStore(
        f"sqlite:///{tmp_path / 'test.db'}"
    )
    await store.initialize()

    assert await store.get("nonexistent") is None

@pytest.mark.asyncio
async def test_conversation_can_be_deleted(tmp_path):
    store = ConversationStore(
        f"sqlite:///{tmp_path / 'test.db'}"
    )
    await store.initialize()

    state = ConversationState(session_id="session-003")
    await store.save(state)

    await store.delete("session-003")

    assert await store.get("session-003") is None