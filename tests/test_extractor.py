import pytest

from src.conversation.extractor import DiscoveryExtractor
from src.agent.instructions import DISCOVERY_QUESTIONS

class MockLLMClient:
    """Mock Ollama client for extractor tests."""

    def __init__(self, response):
        self.response = response
        self.called = False
        self.response_format = None

    async def chat(self, messages, response_format=None):
        self.called = True
        self.response_format = response_format
        return self.response

@pytest.mark.asyncio
async def test_extracts_valid_discovery_answer():
    response = """
    {
        "answers": [
            {
                "question": "Are you looking for yourself or someone else?",
                "answer": "Someone else",
                "evidence": "I am looking for my mother",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "I am looking for my mother"
    )

    assert len(result.answers) == 1
    assert result.answers[0].certainty == "explicit"
    assert result.answers[0].evidence == "I am looking for my mother"
    assert client.called is True
    assert client.response_format == "json"

@pytest.mark.asyncio
async def test_extracts_multiple_answers():
    response = """
    {
        "answers": [
            {
                "question": "Are you looking for yourself or someone else?",
                "answer": "Someone else",
                "evidence": "I am looking for my mother",
                "certainty": "explicit",
                "is_correction": false
            },
            {
                "question": "Which location would you prefer?",
                "answer": "Lagos",
                "evidence": "We want somewhere in Lagos",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "I am looking for my mother. We want somewhere in Lagos."
    )

    assert len(result.answers) == 2

@pytest.mark.asyncio
async def test_accepts_empty_extraction():
    client = MockLLMClient('{"answers": []}')
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "What facilities does the community have?"
    )

    assert result.answers == []

@pytest.mark.asyncio
async def test_rejects_empty_caller_message():
    client = MockLLMClient('{"answers": []}')
    extractor = DiscoveryExtractor(llm_client=client)

    with pytest.raises(ValueError, match="cannot be empty"):
        await extractor.extract("   ")

    assert client.called is False

@pytest.mark.asyncio
async def test_rejects_invalid_json():
    client = MockLLMClient("This is not valid JSON.")
    extractor = DiscoveryExtractor(llm_client=client)

    with pytest.raises(ValueError, match="invalid discovery extraction"):
        await extractor.extract("I am looking for my mother.")

@pytest.mark.asyncio
async def test_discards_unsupported_discovery_question():
    response = """
    {
        "answers": [
            {
                "question": "What is your favourite colour?",
                "answer": "Blue",
                "evidence": "I like blue",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract("I like blue")

    assert result.answers == []

@pytest.mark.asyncio
async def test_discards_evidence_not_present_in_message():
    response = """
    {
        "answers": [
            {
                "question": "Are you looking for yourself or someone else?",
                "answer": "Someone else",
                "evidence": "I am looking for my father",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract("I am looking for my mother")

    assert result.answers == []

@pytest.mark.asyncio
async def test_rejects_missing_required_fields():
    response = """
    {
        "answers": [
            {
                "question": "Are you looking for yourself or someone else?",
                "answer": "Someone else"
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    with pytest.raises(ValueError, match="invalid discovery extraction"):
        await extractor.extract("I am looking for my mother.")

@pytest.mark.asyncio
async def test_rejects_invalid_certainty():
    response = """
    {
        "answers": [
            {
                "question": "Are you looking for yourself or someone else?",
                "answer": "Someone else",
                "evidence": "I am looking for my mother",
                "certainty": "guaranteed",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    with pytest.raises(ValueError, match="invalid discovery extraction"):
        await extractor.extract("I am looking for my mother.")

@pytest.mark.asyncio
async def test_requests_json_response_format():
    client = MockLLMClient('{"answers": []}')
    extractor = DiscoveryExtractor(llm_client=client)

    await extractor.extract(
        "What facilities does the community have?"
    )

    assert client.called is True
    assert client.response_format == "json"

@pytest.mark.asyncio
async def test_extracts_person_age():
    response = """
    {
        "answers": [
            {
                "question": "How old is the person considering senior living?",
                "answer": "82 years old",
                "evidence": "My mother is 82 years old",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "My mother is 82 years old."
    )

    assert len(result.answers) == 1
    assert result.answers[0].question == (
        "How old is the person considering senior living?"
    )
    assert result.answers[0].answer == "82 years old"


@pytest.mark.asyncio
async def test_extracts_current_living_situation():
    response = """
    {
        "answers": [
            {
                "question": "What is their current living arrangement?",
                "answer": "Living with family",
                "evidence": "She currently lives with me",
                "certainty": "explicit",
                "is_correction": false
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "She currently lives with me."
    )

    assert len(result.answers) == 1
    assert result.answers[0].question == (
        "What is their current living arrangement?"
    )
    assert result.answers[0].answer == "Living with family"

@pytest.mark.asyncio
async def test_extracts_corrected_discovery_answer():
    response = """
    {
        "answers": [
            {
                "question": "How old is the person considering senior living?",
                "answer": "83 years old",
                "evidence": "I meant 83, not 82",
                "certainty": "explicit",
                "is_correction": true
            }
        ]
    }
    """

    client = MockLLMClient(response)
    extractor = DiscoveryExtractor(llm_client=client)

    result = await extractor.extract(
        "I meant 83, not 82."
    )

    assert len(result.answers) == 1
    assert result.answers[0].answer == "83 years old"
    assert result.answers[0].is_correction is True