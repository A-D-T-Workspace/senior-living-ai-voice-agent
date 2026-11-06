import pytest

from src.knowledge.retriever import CommunityKnowledgeRetriever

@pytest.fixture
def retriever():
    return CommunityKnowledgeRetriever()

def test_retrieves_community_information(retriever):
    result = retriever.retrieve("Where is the community located?")

    assert result["found"] is True
    assert any(
        item["category"] == "community"
        for item in result["evidence"]
    )

def test_retrieves_accommodation_information(retriever):
    result = retriever.retrieve("What accommodation options are available?")

    assert result["found"] is True
    assert any(
        item["category"] == "accommodation"
        for item in result["evidence"]
    )

def test_retrieves_facilities(retriever):
    result = retriever.retrieve("Does the community have a garden?")

    assert result["found"] is True
    assert any(
        item["category"] == "facilities"
        for item in result["evidence"]
    )

def test_retrieves_services(retriever):
    result = retriever.retrieve("What services do you provide?")

    assert result["found"] is True
    assert any(
        item["category"] == "services"
        for item in result["evidence"]
    )

def test_retrieves_care_and_safety_information(retriever):
    result = retriever.retrieve("Do you provide nursing care?")

    assert result["found"] is True
    assert any(
        item["category"] == "care_and_safety"
        for item in result["evidence"]
    )

def test_retrieves_pricing_information(retriever):
    result = retriever.retrieve("How much does accommodation cost?")

    assert result["found"] is True
    assert any(
        item["category"] == "pricing"
        for item in result["evidence"]
    )

def test_retrieves_appointment_information(retriever):
    result = retriever.retrieve("Can I book a community tour?")

    assert result["found"] is True
    assert any(
        item["category"] == "appointments"
        for item in result["evidence"]
    )

def test_returns_no_evidence_for_unrelated_question(retriever):
    result = retriever.retrieve("What is the weather like today?")

    assert result["found"] is False
    assert result["evidence"] == []

def test_rejects_empty_question(retriever):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        retriever.retrieve("   ")

@pytest.mark.parametrize(
    ("question", "expected_source"),
    [
        ("Can my father receive specialist support?", "care_and_safety"),
        ("Do you have single rooms?", "accommodation"),
        ("Is there somewhere to relax outdoors?", "facilities"),
        ("Do you provide meals?", "services"),
        ("What is the monthly fee?", "pricing"),
        ("Can I come and see the place?", "appointments"),
    ],
)
def test_retrieves_information_from_natural_phrasing(
    retriever,
    question,
    expected_source,
):
    result = retriever.retrieve(question)

    assert result["found"] is True
    assert any(
        item["category"] == expected_source
        for item in result["evidence"]
    )

def test_does_not_retrieve_unrelated_categories(retriever):
    result = retriever.retrieve("What is the weather like today?")

    assert result["found"] is False
    assert result["evidence"] == []

def test_retrieves_only_matching_category(retriever):
    result = retriever.retrieve("Do you have private rooms?")

    sources = [item["category"] for item in result["evidence"]]

    assert sources == ["accommodation"]
