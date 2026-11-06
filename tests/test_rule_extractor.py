from src.agent.instructions import (
    AGE_QUESTION,
    CURRENT_LIVING_SITUATION_QUESTION,
    LIVING_ARRANGEMENT_QUESTION,
    MOTIVATION_QUESTION,
)
from src.conversation.rule_extractor import extract_rules

def test_extracts_age():
    result = extract_rules("My mother is 82 years old.")

    assert len(result.answers) == 1
    assert result.answers[0].question == AGE_QUESTION
    assert result.answers[0].answer == "82"

def test_extracts_current_living_situation():
    result = extract_rules("She currently lives with me.")

    assert len(result.answers) == 1
    assert result.answers[0].question == CURRENT_LIVING_SITUATION_QUESTION

def test_extracts_accommodation_preference():
    result = extract_rules("We are looking for a private suite.")

    assert len(result.answers) == 1
    assert result.answers[0].question == LIVING_ARRANGEMENT_QUESTION
    assert result.answers[0].answer == "private suite"


def test_extracts_multiple_answers():
    message = (
        "My mother is 82 years old. "
        "She currently lives with me, but we are looking "
        "for a private suite because she would prefer her own space."
    )

    result = extract_rules(message)

    questions = {answer.question for answer in result.answers}

    assert AGE_QUESTION in questions
    assert CURRENT_LIVING_SITUATION_QUESTION in questions
    assert LIVING_ARRANGEMENT_QUESTION in questions
    assert MOTIVATION_QUESTION in questions
    assert len(result.answers) == 4

def test_does_not_extract_unsupported_information():
    result = extract_rules("We are exploring our options.")

    assert result.answers == []

def test_does_not_extract_age_without_years_old():
    result = extract_rules("My mother is 82.")

    assert AGE_QUESTION not in {
        answer.question for answer in result.answers
    }

def test_does_not_confuse_shared_living_with_shared_suite():
    result = extract_rules("My mother lives with me.")

    assert LIVING_ARRANGEMENT_QUESTION not in {
        answer.question for answer in result.answers
    }

def test_extracts_shared_suite():
    result = extract_rules("We are considering a shared suite.")

    assert any(
        answer.question == LIVING_ARRANGEMENT_QUESTION
        and answer.answer == "shared suite"
        for answer in result.answers
    )