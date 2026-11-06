import pytest
from pydantic import ValidationError

from src.conversation.extraction import (
    DiscoveryExtraction,
    ExtractedDiscoveryAnswer,
    validate_discovery_question,
)
from src.agent.instructions import DISCOVERY_QUESTIONS

def test_accepts_valid_discovery_answer():
    answer = ExtractedDiscoveryAnswer(
        question=DISCOVERY_QUESTIONS[0],
        answer="I'm looking for my mother.",
        evidence="my mother",
        certainty="explicit",
        is_correction=False,
    )

    assert answer.certainty == "explicit"

def test_rejects_empty_answer():
    with pytest.raises(ValidationError):
        ExtractedDiscoveryAnswer(
            question=DISCOVERY_QUESTIONS[0],
            answer="",
            evidence="my mother",
            certainty="explicit",
        )

def test_rejects_empty_evidence():
    with pytest.raises(ValidationError):
        ExtractedDiscoveryAnswer(
            question=DISCOVERY_QUESTIONS[0],
            answer="I'm looking for my mother.",
            evidence="",
            certainty="explicit",
        )

def test_rejects_invalid_certainty():
    with pytest.raises(ValidationError):
        ExtractedDiscoveryAnswer(
            question=DISCOVERY_QUESTIONS[0],
            answer="I'm looking for my mother.",
            evidence="my mother",
            certainty="high",
        )

def test_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        ExtractedDiscoveryAnswer(
            question=DISCOVERY_QUESTIONS[0],
            answer="I'm looking for my mother.",
            evidence="my mother",
            certainty="explicit",
            unexpected_field="invalid",
        )

def test_accepts_multiple_discovery_answers():
    extraction = DiscoveryExtraction(
        answers=[
            {
                "question": DISCOVERY_QUESTIONS[0],
                "answer": "I'm looking for my mother.",
                "evidence": "my mother",
                "certainty": "explicit",
            },
            {
                "question": DISCOVERY_QUESTIONS[1],
                "answer": "A private suite.",
                "evidence": "private suite",
                "certainty": "explicit",
            },
        ]
    )

    assert len(extraction.answers) == 2

def test_accepts_empty_extraction():
    extraction = DiscoveryExtraction()

    assert extraction.answers == []

def test_recognises_valid_discovery_questions():
    for question in DISCOVERY_QUESTIONS:
        assert validate_discovery_question(question)

def test_rejects_unknown_discovery_question():
    assert not validate_discovery_question(
        "What is your monthly budget?"
    )