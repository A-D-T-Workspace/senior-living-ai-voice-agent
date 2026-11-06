from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.agent.instructions import DISCOVERY_QUESTIONS

class ExtractedDiscoveryAnswer(BaseModel):
    """A discovery answer extracted from a caller message."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str = Field(min_length=1)
    evidence: str = Field(min_length=1)

    certainty: Literal["explicit", "uncertain"]

    is_correction: bool = False

class DiscoveryExtraction(BaseModel):
    """Structured discovery information extracted from a caller message."""

    model_config = ConfigDict(extra="forbid")

    answers: list[ExtractedDiscoveryAnswer] = Field(
        default_factory=list
    )

def validate_discovery_question(question: str) -> bool:
    """Check whether an extracted question belongs to our discovery framework."""

    return question in DISCOVERY_QUESTIONS