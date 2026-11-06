import re
import logging

from src.agent.llm import OllamaClient
from src.agent.response_policy import GroundedResponsePolicy
from src.conversation.models import ConversationState
from src.conversation.state import (
    add_message,
    build_llm_messages,
)
from src.knowledge.retriever import CommunityKnowledgeRetriever
from src.conversation.extractor import DiscoveryExtractor
from src.agent.instructions import DISCOVERY_QUESTIONS
from src.conversation.discovery import record_discovery_response
from src.conversation.rule_extractor import extract_rules

logger = logging.getLogger(__name__)

class ConversationEngine:
    """Coordinates conversation state, knowledge retrieval, and LLM responses."""

    def __init__(
        self,
        llm_client=None,
        knowledge_retriever=None,
        booking_available=False,
        response_policy=None,
        discovery_extractor=None,
        scheduling_service=None,
    ):
        self.llm = llm_client or OllamaClient()
        self.retriever = (
            knowledge_retriever or CommunityKnowledgeRetriever()
        )
        self.booking_available = booking_available
        self.response_policy = (
            response_policy or GroundedResponsePolicy()
        )
        self.discovery_extractor = (
            discovery_extractor
            or DiscoveryExtractor(llm_client=self.llm)
        )

        self.scheduling_service = scheduling_service

        self.booking_available = (
            scheduling_service is not None and booking_available
        )

    def _booking_capability_message(self):
        if self.booking_available:
            return (
                "Booking integration is configured. "
                "Only report an availability check or booking as successful "
                "after receiving a successful result from the actual "
                "booking integration."
            )

        return (
            "BOOKING CAPABILITY STATUS: UNAVAILABLE. "
            "No booking or availability integration is currently available. "
            "Do not claim to check availability, access a booking system, "
            "reserve a time, create an appointment, or complete a booking. "
            "Do not imply that any external booking action has occurred. "
            "Explain naturally that appointment availability cannot "
            "currently be verified."
        )

    def _contains_unsupported_booking_claim(self, response: str) -> bool:
        if self.booking_available:
            return False

        patterns = [
            r"\blet me check\b",
            r"\bchecking (?:our |the )?(?:availability|booking) system\b",
            r"\bI(?:'ll| will) check (?:our |the )?(?:availability|booking)\b",
            r"\bI(?:'ve| have) checked (?:our |the )?(?:availability|booking)\b",
            r"\bI(?:'ve| have) booked\b",
            r"\byour appointment is booked\b",
            r"\byou(?:'re| are) booked\b",
            r"\bappointment has been confirmed\b",
            r"\bI(?:'ll| will) book (?:that|you|an appointment)\b",
            r"\bI can book (?:that|you|an appointment)\b",
            r"\bavailable time slots\b",
        ]

        return any(
            re.search(pattern, response, re.IGNORECASE)
            for pattern in patterns
        )

    async def _extract_discovery_answers(
        self,
        state: ConversationState,
        caller_message: str,
    ) -> None:
        """Combine rule-based and LLM extraction safely."""

        extracted_answers = {}

        try:
            rule_extraction = extract_rules(caller_message)

            for item in rule_extraction.answers:
                if item.certainty != "explicit":
                    continue

                if item.question not in DISCOVERY_QUESTIONS:
                    continue

                if item.evidence not in caller_message:
                    continue

                if item.question not in extracted_answers or item.is_correction:
                    extracted_answers[item.question] = item

        except Exception:
            logger.exception("Rule-based discovery extraction failed.")

        try:
            llm_extraction = await self.discovery_extractor.extract(
                caller_message
            )

            for item in llm_extraction.answers:
                if item.certainty != "explicit":
                    continue

                if item.question not in DISCOVERY_QUESTIONS:
                    continue

                if item.evidence not in caller_message:
                    continue

                extracted_answers[item.question] = item

        except Exception:
            logger.exception("LLM discovery extraction failed.")

        for item in extracted_answers.values():
            existing_answer = state.discovery_answers.get(
                item.question
            )

            if existing_answer and not item.is_correction:
                continue

            if not existing_answer and item.is_correction:
                continue

            record_discovery_response(
                state,
                item.question,
                item.answer,
            )

    async def respond(
        self,
        state: ConversationState,
        caller_message: str,
    ) -> str:
        """Retrieve verified knowledge and generate a grounded response."""

        if not caller_message.strip():
            raise ValueError("Caller message cannot be empty.")

        if state.status != "active":
            raise ValueError("Conversation is not active.")

        caller_message = caller_message.strip()

        add_message(state, "user", caller_message)

        retrieval_result = self.retriever.retrieve(caller_message)
        evidence = retrieval_result["evidence"]

        policy_response = self.response_policy.generate(
            caller_message,
            evidence,
        )

        if policy_response is not None:
            await self._extract_discovery_answers(state, caller_message)
            add_message(state, "assistant", policy_response)
            return policy_response

        messages = build_llm_messages(
            state,
            knowledge_evidence=evidence,
        )

        messages.insert(
            1,
            {
                "role": "system",
                "content": self._booking_capability_message(),
            },
        )

        messages.insert(
            2,
            {
                "role": "system",
                "content": (
                    "RESPONSE GROUNDING AND CONCISENESS: "
                    "For factual questions about WillowBrook, use only the "
                    "provided evidence. If the evidence does not confirm an "
                    "answer, say so briefly in one or two sentences. "
                    "Do not invent facts, services, prices, capabilities, "
                    "or real-time information. When appropriate, offer to "
                    "arrange a conversation with the community team. "
                    "For ordinary conversational questions, respond naturally. "
                    "Avoid unnecessary explanations, repeated disclaimers, "
                    "and unrelated suggestions."
                ),
            },
        )

        response = await self.llm.chat(messages)

        await self._extract_discovery_answers(
            state,
            caller_message,
        )

        if self._contains_unsupported_booking_claim(response):
            response = (
                "I can explain our appointment process, but I cannot "
                "currently verify available appointment times or complete "
                "a booking. I don't want to give you unconfirmed information."
            )

        add_message(state, "assistant", response)

        return response