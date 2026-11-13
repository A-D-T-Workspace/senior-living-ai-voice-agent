import pytest

from src.agent.engine import ConversationEngine
from src.conversation.state import create_conversation
from src.conversation.extraction import (
    DiscoveryExtraction,
    ExtractedDiscoveryAnswer,
)
from src.agent.instructions import DISCOVERY_QUESTIONS

class MockLLMClient:
    """Simulates an LLM response without calling Ollama."""

    async def chat(self, *messages):
        return (
            "I'd be happy to help. "
            "What type of living arrangement are you considering?"
        )

class RecordingLLMClient:
    def __init__(self):
        self.received_messages = []

    async def chat(self, *messages):
        self.received_messages.append(messages[0])
        return "I would be happy to help."

class FakeDiscoveryExtractor:
    """Isolates discovery extraction from the main conversation LLM."""

    def __init__(self, answers=None, error=None):
        self.answers = answers or []
        self.error = error
        self.calls = []

    async def extract(self, caller_message):
        self.calls.append(caller_message)

        if self.error:
            raise self.error

        return DiscoveryExtraction(answers=self.answers)

class FakeKnowledgeRetriever:
    """Knowledge retriever test double."""

    def __init__(self, evidence):
        self.evidence = evidence
        self.received_questions = []

    def retrieve(self, question):
        self.received_questions.append(question)

        return {
            "question": question,
            "found": bool(self.evidence),
            "evidence": self.evidence,
            "message": "Test retrieval completed.",
        }

def make_engine(
    llm_client=None,
    knowledge_retriever=None,
    booking_available=False,
    response_policy=None,
    discovery_extractor=None,
):
    """Creates an engine with an isolated discovery extractor."""

    return ConversationEngine(
        llm_client=llm_client or MockLLMClient(),
        knowledge_retriever=knowledge_retriever,
        booking_available=booking_available,
        response_policy=response_policy,
        discovery_extractor=(
            discovery_extractor or FakeDiscoveryExtractor()
        ),
    )

def make_answer(
    question,
    answer,
    evidence,
    certainty="explicit",
    is_correction=False,
):
    return ExtractedDiscoveryAnswer(
        question=question,
        answer=answer,
        evidence=evidence,
        certainty=certainty,
        is_correction=is_correction,
    )

@pytest.mark.asyncio
async def test_engine_processes_conversation():
    engine = make_engine()
    state = create_conversation("engine-test")

    response = await engine.respond(
        state,
        "I'm looking for a living arrangement for my mother.",
    )

    assert response == (
        "I'd be happy to help. "
        "What type of living arrangement are you considering?"
    )

    assert len(state.messages) == 2
    assert state.messages[0].role == "user"
    assert state.messages[1].role == "assistant"

@pytest.mark.asyncio
async def test_engine_preserves_multiple_turns():
    engine = make_engine()
    state = create_conversation("multi-turn-test")

    await engine.respond(state, "I'm looking for my mother.")
    await engine.respond(state, "She is 82 years old.")

    assert len(state.messages) == 4
    assert state.messages[0].content == "I'm looking for my mother."
    assert state.messages[2].content == "She is 82 years old."

@pytest.mark.asyncio
async def test_engine_rejects_empty_messages():
    engine = make_engine()
    state = create_conversation("empty-test")

    with pytest.raises(
        ValueError,
        match="Caller message cannot be empty",
    ):
        await engine.respond(state, "   ")

@pytest.mark.asyncio
async def test_engine_rejects_inactive_conversations():
    engine = make_engine()
    state = create_conversation("inactive-test")
    state.status = "completed"

    with pytest.raises(
        ValueError,
        match="Conversation is not active",
    ):
        await engine.respond(state, "Hello")

@pytest.mark.asyncio
async def test_engine_retrieves_knowledge_for_caller_message():
    llm = RecordingLLMClient()
    retriever = FakeKnowledgeRetriever([])

    engine = make_engine(
        llm_client=llm,
        knowledge_retriever=retriever,
    )

    state = create_conversation("test-retrieval")

    await engine.respond(state, "Do you have private suites?")

    assert retriever.received_questions == [
        "Do you have private suites?"
    ]

@pytest.mark.asyncio
async def test_engine_passes_knowledge_evidence_to_llm():
    evidence = [
        {
            "source": "facilities",
            "content": [
                "Dining area",
                "Landscaped gardens",
            ],
        }
    ]

    llm = RecordingLLMClient()
    retriever = FakeKnowledgeRetriever(evidence)

    engine = make_engine(
        llm_client=llm,
        knowledge_retriever=retriever,
    )

    state = create_conversation("test-evidence")

    await engine.respond(state, "What facilities are available?")

    received_messages = llm.received_messages[0]

    assert any(
        "Landscaped gardens" in message["content"]
        for message in received_messages
    )

@pytest.mark.asyncio
async def test_engine_handles_missing_knowledge_evidence():
    llm = RecordingLLMClient()
    retriever = FakeKnowledgeRetriever([])

    engine = make_engine(
        llm_client=llm,
        knowledge_retriever=retriever,
    )

    state = create_conversation("test-no-evidence")

    await engine.respond(state, "What is the refund policy?")

    received_messages = llm.received_messages[0]

    assert len(received_messages) == 4
    assert received_messages[0]["role"] == "system"
    assert received_messages[1]["role"] == "system"
    assert received_messages[2]["role"] == "system"
    assert received_messages[3]["role"] == "user"

    assert (
        "RESPONSE GROUNDING AND CONCISENESS"
        in received_messages[2]["content"]
    )

    assert (
        "BOOKING CAPABILITY STATUS: UNAVAILABLE"
        in received_messages[1]["content"]
    )

@pytest.mark.asyncio
async def test_engine_blocks_false_availability_claims():
    class FalseBookingLLM:
        async def chat(self, *messages):
            return "Let me check our availability system for you."

    engine = make_engine(llm_client=FalseBookingLLM())
    state = create_conversation("false-availability-test")

    response = await engine.respond(
        state,
        "Can I book a tour?",
    )

    assert "Let me check" not in response
    assert "cannot currently verify" in response

@pytest.mark.asyncio
async def test_engine_blocks_false_booking_confirmation():
    class FalseBookingLLM:
        async def chat(self, *messages):
            return "Your appointment is booked."

    engine = make_engine(llm_client=FalseBookingLLM())
    state = create_conversation("false-booking-test")

    response = await engine.respond(
        state,
        "Please book a tour.",
    )

    assert response != "Your appointment is booked."
    assert "cannot currently verify" in response

@pytest.mark.asyncio
async def test_engine_informs_llm_booking_is_unavailable():
    llm = RecordingLLMClient()

    engine = make_engine(llm_client=llm)
    state = create_conversation("booking-capability-test")

    await engine.respond(
        state,
        "I would like to learn more about the community.",
    )

    messages = llm.received_messages[0]

    assert any(
        "BOOKING CAPABILITY STATUS: UNAVAILABLE" in message["content"]
        for message in messages
    )

@pytest.mark.asyncio
async def test_engine_allows_normal_appointment_information():
    class AppointmentInformationLLM:
        async def chat(self, *messages):
            return (
                "Community tours are available by appointment. "
                "Booking is required."
            )

    engine = make_engine(llm_client=AppointmentInformationLLM())
    state = create_conversation("appointment-information-test")

    response = await engine.respond(
        state,
        "Do you offer community tours?",
    )

    assert "community tours" in response.lower()
    assert "introductory consultations" in response.lower()
    assert "appointments require booking" in response.lower()
    assert "cannot currently verify" in response.lower()

@pytest.mark.asyncio
async def test_engine_saves_explicit_discovery_answer():
    question = DISCOVERY_QUESTIONS[0]
    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=question,
                answer="My mother",
                evidence="looking for my mother",
            )
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("explicit-discovery-test")

    await engine.respond(
        state,
        "I am looking for my mother.",
    )

    assert state.discovery_answers[question] == "My mother"

@pytest.mark.asyncio
async def test_engine_ignores_uncertain_discovery_answer():
    question = DISCOVERY_QUESTIONS[0]
    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=question,
                answer="My mother",
                evidence="looking for my mother",
                certainty="uncertain",
            )
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("uncertain-discovery-test")

    await engine.respond(
        state,
        "I am looking for my mother.",
    )

    assert question not in state.discovery_answers

@pytest.mark.asyncio
async def test_engine_updates_existing_answer_when_corrected():
    question = DISCOVERY_QUESTIONS[0]

    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=question,
                answer="My father",
                evidence="Actually, I meant my father",
                is_correction=True,
            )
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("correction-update-test")

    state.discovery_answers[question] = "My mother"

    await engine.respond(
        state,
        "Actually, I meant my father.",
    )

    assert state.discovery_answers[question] == "My father"

@pytest.mark.asyncio
async def test_engine_ignores_discovery_corrections():
    question = DISCOVERY_QUESTIONS[0]
    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=question,
                answer="My father",
                evidence="Actually, my father",
                is_correction=True,
            )
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("correction-test")

    await engine.respond(
        state,
        "Actually, my father.",
    )

    assert question not in state.discovery_answers

@pytest.mark.asyncio
async def test_engine_preserves_existing_discovery_answer():
    question = DISCOVERY_QUESTIONS[0]
    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=question,
                answer="My father",
                evidence="looking for my father",
            )
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("existing-answer-test")

    state.discovery_answers[question] = "My mother"

    await engine.respond(
        state,
        "I am looking for my father.",
    )

    assert state.discovery_answers[question] == "My mother"

@pytest.mark.asyncio
async def test_engine_saves_multiple_discovery_answers():
    first_question = DISCOVERY_QUESTIONS[0]
    second_question = DISCOVERY_QUESTIONS[1]

    extractor = FakeDiscoveryExtractor(
        answers=[
            make_answer(
                question=first_question,
                answer="My mother",
                evidence="looking for my mother",
            ),
            make_answer(
                question=second_question,
                answer="Private suite",
                evidence="a private suite",
            ),
        ]
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("multiple-answers-test")

    await engine.respond(
        state,
        "I am looking for my mother and considering a private suite.",
    )

    assert state.discovery_answers[first_question] == "My mother"
    assert state.discovery_answers[second_question] == "Private suite"

@pytest.mark.asyncio
async def test_engine_continues_when_discovery_extraction_fails():
    extractor = FakeDiscoveryExtractor(
        error=ValueError("Extraction failed")
    )

    engine = make_engine(discovery_extractor=extractor)
    state = create_conversation("extraction-failure-test")

    response = await engine.respond(
        state,
        "I am looking for my mother.",
    )

    assert response == (
        "I'd be happy to help. "
        "What type of living arrangement are you considering?"
    )

    assert len(state.messages) == 2
    assert state.messages[1].role == "assistant"

@pytest.mark.asyncio
async def test_engine_calls_extractor_after_main_llm():
    class OrderedLLMClient:
        def __init__(self):
            self.call_count = 0

        async def chat(self, *messages):
            self.call_count += 1
            return "I would be happy to help."

    class OrderedExtractor:
        def __init__(self, llm):
            self.llm = llm
            self.called_after_main_llm = False

        async def extract(self, caller_message):
            self.called_after_main_llm = self.llm.call_count == 1
            return DiscoveryExtraction(answers=[])

    llm = OrderedLLMClient()
    extractor = OrderedExtractor(llm)

    engine = make_engine(
        llm_client=llm,
        discovery_extractor=extractor,
    )

    state = create_conversation("extraction-order-test")

    await engine.respond(state, "Hello.")

    assert extractor.called_after_main_llm is True

@pytest.mark.asyncio
async def test_engine_handles_main_llm_failure():
    class FailingLLMClient:
        async def chat(self, *messages):
            raise RuntimeError("Ollama is unavailable.")

    engine = make_engine(
        llm_client=FailingLLMClient(),
    )

    state = create_conversation("main-llm-failure-test")

    response = await engine.respond(
        state,
        "Hello, I would like to learn about your community.",
    )

    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert len(state.messages) == 2
    assert state.messages[1].role == "assistant"

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language", "language_name"),
    [
        ("en", "English"),
        ("yo", "Yoruba"),
        ("ig", "Igbo"),
        ("ha", "Hausa"),
    ],
)
async def test_engine_instructs_llm_to_respond_in_detected_language(
    language,
    language_name,
):
    llm = RecordingLLMClient()

    engine = make_engine(llm_client=llm)
    state = create_conversation("multilingual-test")

    await engine.respond(
        state,
        "I am looking for a senior living community.",
        language=language,
    )

    messages = llm.received_messages[0]

    assert any(
        language_name in message["content"]
        and "respond" in message["content"].lower()
        for message in messages
        if message["role"] == "system"
    )