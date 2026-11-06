import pytest

from src.conversation.state import create_conversation
from src.conversation.discovery import (
    get_unanswered_questions,
    get_next_discovery_question,
    record_discovery_response,
)
from src.agent.instructions import DISCOVERY_QUESTIONS

def test_all_questions_are_initially_unanswered():
    state = create_conversation("discovery-001")

    assert get_unanswered_questions(state) == DISCOVERY_QUESTIONS

def test_get_next_discovery_question():
    state = create_conversation("discovery-002")

    assert get_next_discovery_question(state) == DISCOVERY_QUESTIONS[0]

def test_answered_question_is_removed():
    state = create_conversation("discovery-003")

    question = DISCOVERY_QUESTIONS[0]
    record_discovery_response(state, question, "I'm looking for my mother.")

    assert question not in get_unanswered_questions(state)

def test_next_question_changes_after_answer():
    state = create_conversation("discovery-004")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm looking for my father.",
    )

    assert get_next_discovery_question(state) == DISCOVERY_QUESTIONS[1]

def test_unknown_question_is_rejected():
    state = create_conversation("discovery-005")

    with pytest.raises(ValueError):
        record_discovery_response(
            state,
            "What is your favourite colour?",
            "Blue",
        )

def test_empty_answer_is_rejected():
    state = create_conversation("discovery-006")

    with pytest.raises(ValueError):
        record_discovery_response(
            state,
            DISCOVERY_QUESTIONS[0],
            "   ",
        )

def test_all_questions_answered():
    state = create_conversation("discovery-007")

    for question in DISCOVERY_QUESTIONS:
        record_discovery_response(state, question, "Test answer")

    assert get_unanswered_questions(state) == []
    assert get_next_discovery_question(state) is None


def test_classifies_family_enquiry():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-008")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm looking for accommodation for my mother.",
    )

    assert "family_enquiry" in classify_caller_intents(state)


def test_classifies_urgent_transition():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-009")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[3],
        "We need accommodation as soon as possible.",
    )

    assert "urgent_transition" in classify_caller_intents(state)


def test_classifies_multiple_intents():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-010")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm looking for my father.",
    )
    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[3],
        "We need accommodation urgently.",
    )

    intents = classify_caller_intents(state)

    assert "family_enquiry" in intents
    assert "urgent_transition" in intents

def test_urgent_caller_gets_timing_question_next():
    from src.conversation.discovery import get_next_discovery_question

    state = create_conversation("discovery-011")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm looking for my mother. We need accommodation urgently.",
    )

    assert get_next_discovery_question(state) == DISCOVERY_QUESTIONS[3]

def test_visit_ready_caller_gets_visit_question_next():
    from src.conversation.discovery import get_next_discovery_question

    state = create_conversation("discovery-012")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm looking for my father and would like to arrange a visit.",
    )

    assert get_next_discovery_question(state) == DISCOVERY_QUESTIONS[7]

def test_discovery_completes_when_core_questions_are_answered():
    from src.conversation.discovery import is_discovery_complete

    state = create_conversation("discovery-013")

    for question in DISCOVERY_QUESTIONS[:5]:
        record_discovery_response(state, question, "Relevant test answer")

    assert is_discovery_complete(state)

def test_optional_questions_do_not_block_completion():
    from src.conversation.discovery import is_discovery_complete

    state = create_conversation("discovery-014")

    for question in DISCOVERY_QUESTIONS[:5]:
        record_discovery_response(state, question, "Relevant test answer")

    assert is_discovery_complete(state)
    assert DISCOVERY_QUESTIONS[5] in get_unanswered_questions(state)

def test_does_not_classify_negated_visit_intent():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-015")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I'm not ready to visit the community.",
    )

    assert "visit_readiness" not in classify_caller_intents(state)

def test_does_not_classify_uncertain_visit_intent():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-016")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "Maybe I will visit someday.",
    )

    assert "visit_readiness" not in classify_caller_intents(state)

def test_classifies_clear_visit_intent():
    from src.conversation.discovery import classify_caller_intents

    state = create_conversation("discovery-017")

    record_discovery_response(
        state,
        DISCOVERY_QUESTIONS[0],
        "I would like to arrange a visit next week.",
    )

    assert "visit_readiness" in classify_caller_intents(state)

def test_classifies_natural_visit_language():
    from src.conversation.discovery import classify_caller_intents

    phrases = [
        "I'd love to come and see the place.",
        "Can we schedule a tour?",
        "I'd be happy to visit next week.",
        "I want to see the facilities.",
    ]

    for index, phrase in enumerate(phrases, start=18):
        state = create_conversation(f"discovery-{index}")

        record_discovery_response(
            state,
            DISCOVERY_QUESTIONS[0],
            phrase,
        )

        assert "visit_readiness" in classify_caller_intents(state), phrase