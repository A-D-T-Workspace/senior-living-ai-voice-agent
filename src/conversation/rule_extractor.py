import re

from src.agent.instructions import (
    AGE_QUESTION,
    CURRENT_LIVING_SITUATION_QUESTION,
    LIVING_ARRANGEMENT_QUESTION,
    MOTIVATION_QUESTION,
)
from src.conversation.extraction import (
    DiscoveryExtraction,
    ExtractedDiscoveryAnswer,
)

def extract_rules(caller_message: str) -> DiscoveryExtraction:
    """Extract discovery answers using deterministic text patterns."""

    answers = []

    age_match = re.search(
        r"\b(?:is|aged|age of)\s+(\d{1,3})\s+years?\s+old\b"
        r"|\b(\d{1,3})\s+years?\s+old\b",
        caller_message,
        re.IGNORECASE,
    )

    if age_match:
        age = next(
            group for group in age_match.groups()
            if group is not None
        )

        answers.append(
            ExtractedDiscoveryAnswer(
                question=AGE_QUESTION,
                answer=age,
                evidence=age_match.group(0),
                certainty="explicit",
            )
        )

    living_patterns = [
        r"\b(?:she|he|they|my mother|my father|my parent|my parents)"
        r"\s+(?:currently\s+)?lives?\s+with\s+[^,.]+",
        r"\b(?:she|he|they|my mother|my father|my parent|my parents)"
        r"\s+(?:currently\s+)?lives?\s+alone\b",
        r"\b(?:she|he|they|my mother|my father|my parent|my parents)"
        r"\s+(?:currently\s+)?lives?\s+in\s+[^,.]+",
    ]

    for pattern in living_patterns:
        match = re.search(
            pattern,
            caller_message,
            re.IGNORECASE,
        )

        if match:
            answers.append(
                ExtractedDiscoveryAnswer(
                    question=CURRENT_LIVING_SITUATION_QUESTION,
                    answer=match.group(0),
                    evidence=match.group(0),
                    certainty="explicit",
                )
            )
            break
  
    accommodation_match = re.search(
        r"\b(?:private|shared)\s+(?:suite|room|accommodation)\b",
        caller_message,
        re.IGNORECASE,
    )

    if accommodation_match:
        answers.append(
            ExtractedDiscoveryAnswer(
                question=LIVING_ARRANGEMENT_QUESTION,
                answer=accommodation_match.group(0),
                evidence=accommodation_match.group(0),
                certainty="explicit",
            )
        )

    motivation_match = re.search(
        r"\bbecause\s+(?P<reason>[^,.!?]+)",
        caller_message,
        re.IGNORECASE,
    )

    if motivation_match:
        answers.append(
            ExtractedDiscoveryAnswer(
                question=MOTIVATION_QUESTION,
                answer=motivation_match.group("reason").strip(),
                evidence=motivation_match.group(0),
                certainty="explicit",
            )
        )

    return DiscoveryExtraction(answers=answers)