import re

from src.agent.instructions import (
    DISCOVERY_QUESTIONS,
    MOVE_TIMING_QUESTION,
    VISIT_QUESTION,
    LOOKING_FOR_QUESTION,
    LIVING_ARRANGEMENT_QUESTION,
    MOTIVATION_QUESTION,
    PREFERRED_LOCATION_QUESTION,
    AGE_QUESTION,
    CURRENT_LIVING_SITUATION_QUESTION,
)
from src.conversation.models import ConversationState
from src.conversation.state import save_discovery_answer

CORE_DISCOVERY_QUESTIONS = [
    LOOKING_FOR_QUESTION,
    LIVING_ARRANGEMENT_QUESTION,
    MOTIVATION_QUESTION,
    MOVE_TIMING_QUESTION,
    PREFERRED_LOCATION_QUESTION,
]

ADDITIONAL_DISCOVERY_QUESTIONS = [
    AGE_QUESTION,
    CURRENT_LIVING_SITUATION_QUESTION,
]

OPTIONAL_DISCOVERY_QUESTIONS = [
    question
    for question in DISCOVERY_QUESTIONS
    if question not in CORE_DISCOVERY_QUESTIONS
]

def _get_all_answers(state: ConversationState) -> str:
    """Combine discovery answers into searchable text."""
    return " ".join(state.discovery_answers.values()).lower()

def classify_caller_intents(
    state: ConversationState,
) -> list[str]:
    """
    Identify caller intents using deterministic keyword rules.

    Multiple intents may apply to one caller.
    """
    intents = []
    answers = _get_all_answers(state)

    if re.search(
        r"\b(myself|for me|for myself)\b",
        answers,
    ):
        intents.append("self_enquiry")

    if re.search(
        r"\b(mother|mom|mum|father|dad|parent|parents|"
        r"grandmother|grandfather|grandparent|relative|"
        r"family member|someone else)\b",
        answers,
    ):
        intents.append("family_enquiry")

    if re.search(
        r"\b(private suite|shared suite|private room|"
        r"shared room|living arrangement|accommodation)\b",
        answers,
    ):
        intents.append("accommodation_exploration")

    if re.search(
        r"\b(urgent|urgently|as soon as possible|immediately|"
        r"right away|within a week|within two weeks)\b",
        answers,
    ):
        intents.append("urgent_transition")

    if re.search(
        r"\b(next year|next few years|long.term|"
        r"future planning|not in a hurry|eventually)\b",
        answers,
    ):
        intents.append("long_term_planning")

    if re.search(
        r"\b(other communities|other facilities|"
        r"comparing|comparison|alternatives|"
        r"looking at other options)\b",
        answers,
    ):
        intents.append("community_comparison")

    clear_visit_intent = re.search(
        r"\b("
        r"would like to visit|"
        r"want to visit|"
        r"love to visit|"
        r"happy to visit|"
        r"love to come and see|"
        r"come and see the place|"
        r"see the facilities|"
        r"schedule a tour|"
        r"book a tour|"
        r"arrange a visit|"
        r"ready to visit|"
        r"would like a tour|"
        r"want to arrange a visit|"
        r"would like to arrange a visit|"
        r"visit next week"
        r")\b",
        answers,
    )

    uncertain_visit_intent = re.search(
        r"\b(not ready|not interested|"
        r"maybe|perhaps|someday|"
        r"not sure|might visit|"
        r"thinking about visiting)\b",
        answers,
    )

    if clear_visit_intent and not uncertain_visit_intent:
        intents.append("visit_readiness")

    return intents

def get_unanswered_questions(
    state: ConversationState,
) -> list[str]:
    """Return discovery questions that have not been answered."""
    return [
        question
        for question in DISCOVERY_QUESTIONS
        if question not in state.discovery_answers
    ]

def get_next_discovery_question(
    state: ConversationState,
) -> str | None:
    """
    Select the next unanswered question using caller context.

    The original question sequence is preserved unless caller
    information indicates that another question should take priority.
    """
    unanswered = get_unanswered_questions(state)

    if not unanswered:
        return None

    intents = classify_caller_intents(state)

    if "urgent_transition" in intents and MOVE_TIMING_QUESTION in unanswered:
        return MOVE_TIMING_QUESTION

    if "visit_readiness" in intents and VISIT_QUESTION in unanswered:
        return VISIT_QUESTION

    return unanswered[0]

def record_discovery_response(
    state: ConversationState,
    question: str,
    answer: str,
) -> ConversationState:
    """Validate and save a discovery response."""
    if question not in DISCOVERY_QUESTIONS:
        raise ValueError("Unknown discovery question.")

    if not answer.strip():
        raise ValueError("Discovery answer cannot be empty.")

    return save_discovery_answer(
        state,
        question,
        answer.strip(),
    )

def is_discovery_complete(
    state: ConversationState,
) -> bool:
    """
    Determine whether the five core discovery questions are answered.

    Optional questions do not prevent discovery completion.
    """
    return all(
        question in state.discovery_answers
        and bool(state.discovery_answers[question].strip())
        for question in CORE_DISCOVERY_QUESTIONS
    )
