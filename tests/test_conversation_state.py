from src.conversation.state import build_llm_messages

from src.conversation.state import (
    create_conversation,
    add_message,
    update_caller,
    save_discovery_answer,
    update_conversation_stage,
)

def test_create_conversation():
    state = create_conversation("session-001")

    assert state.session_id == "session-001"
    assert state.status == "active"
    assert state.current_stage == "greeting"
    assert state.messages == []

def test_add_message():
    state = create_conversation("session-002")

    add_message(state, "user", "I'm looking for care for my mother.")

    assert len(state.messages) == 1
    assert state.messages[0].role == "user"
    assert state.messages[0].content == "I'm looking for care for my mother."

def test_update_caller():
    state = create_conversation("session-003")

    update_caller(
        state,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
    )

    assert state.caller.first_name == "John"
    assert state.caller.last_name == "Smith"
    assert state.caller.email == "john@example.com"

def test_update_caller_preserves_existing_details():
    state = create_conversation("session-004")

    update_caller(state, first_name="John", last_name="Smith")
    update_caller(state, first_name="David")

    assert state.caller.first_name == "David"
    assert state.caller.last_name == "Smith"

def test_save_discovery_answer():
    state = create_conversation("session-005")

    save_discovery_answer(
        state,
        "Who are you looking for?",
        "My mother",
    )

    assert state.discovery_answers["Who are you looking for?"] == "My mother"

def test_update_conversation_stage():
    state = create_conversation("session-006")

    update_conversation_stage(state, "discovery")

    assert state.current_stage == "discovery"

def test_build_llm_messages_preserves_conversation_history():
    state = create_conversation("test-session")

    add_message(state, "user", "I'm looking for my mother.")
    add_message(state, "assistant", "Of course. How old is your mother?")
    add_message(state, "user", "She is 82 years old.")

    messages = build_llm_messages(state)

    assert messages[0]["role"] == "system"
    assert len(messages) == 4

    assert messages[1]["content"] == "I'm looking for my mother."
    assert messages[2]["content"] == "Of course. How old is your mother?"
    assert messages[3]["content"] == "She is 82 years old."

def test_build_llm_messages_includes_knowledge_evidence():
    state = create_conversation("test-grounding")

    evidence = [
        {
            "source": "facilities",
            "content": ["Dining area", "Landscaped gardens"],
        }
    ]

    messages = build_llm_messages(
        state,
        knowledge_evidence=evidence,
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert "Landscaped gardens" in messages[1]["content"]


def test_build_llm_messages_without_evidence():
    state = create_conversation("test-no-evidence")

    messages = build_llm_messages(state)

    assert len(messages) == 1
    assert messages[0]["role"] == "system"


def test_knowledge_evidence_does_not_modify_conversation_history():
    state = create_conversation("test-history")

    evidence = [
        {
            "source": "pricing",
            "content": {"status": "Not yet defined"},
        }
    ]

    build_llm_messages(
        state,
        knowledge_evidence=evidence,
    )

    assert state.messages == []

def test_build_llm_messages_includes_evidence_status_rules():
    state = create_conversation("test-evidence-status")

    evidence = [
        {
            "category": "care_and_safety",
            "claim": "dementia_care",
            "status": "not_offered",
            "value": False,
        },
        {
            "category": "care_and_safety",
            "claim": "specialist_disability_support",
            "status": "unconfirmed",
            "value": None,
        },
    ]

    messages = build_llm_messages(
        state,
        knowledge_evidence=evidence,
    )

    evidence_message = messages[1]["content"]

    assert "confirmed" in evidence_message
    assert "not_offered" in evidence_message
    assert "unconfirmed" in evidence_message
    assert "Never change, exaggerate, or weaken an evidence status." in evidence_message
    assert "Never reveal the fictional demonstration address." in evidence_message
