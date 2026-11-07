import pytest

from src.agent.response_policy import GroundedResponsePolicy

@pytest.fixture
def policy():
    return GroundedResponsePolicy()

@pytest.fixture
def community_evidence():
    return [
        {
            "category": "community",
            "claim": "location",
            "status": "confirmed",
            "value": {"city": "Lagos", "country": "Nigeria"},
        },
        {
            "category": "accommodation",
            "claim": "Private Suite",
            "status": "confirmed",
            "value": "Private accommodation for one resident.",
        },
        {
            "category": "accommodation",
            "claim": "Shared Suite",
            "status": "confirmed",
            "value": (
                "Shared accommodation for residents who prefer "
                "a communal living arrangement."
            ),
        },
        {
            "category": "facilities",
            "claim": "Landscaped gardens",
            "status": "confirmed",
            "value": "Landscaped gardens",
        },
        {
            "category": "facilities",
            "claim": "Shared social lounge",
            "status": "confirmed",
            "value": "Shared social lounge",
        },
        {
            "category": "care_and_safety",
            "claim": "nursing_care",
            "status": "not_offered",
            "value": False,
        },
        {
            "category": "care_and_safety",
            "claim": "dementia_care",
            "status": "not_offered",
            "value": False,
        },
        {
            "category": "care_and_safety",
            "claim": "specialist_disability_support",
            "status": "unconfirmed",
            "value": None,
        },
        {
            "category": "pricing",
            "claim": "pricing",
            "status": "unconfirmed",
            "value": "Not yet defined",
            "currency": "NGN",
        },
        {
            "category": "appointments",
            "claim": "Community tours",
            "status": "confirmed",
            "value": "Community tours",
        },
        {
            "category": "appointments",
            "claim": "Introductory consultations",
            "status": "confirmed",
            "value": "Introductory consultations",
        },
        {
            "category": "appointments",
            "claim": "booking_required",
            "status": "confirmed",
            "value": True,
        },
    ]

def test_private_suite_uses_only_confirmed_description(
    policy, community_evidence
):
    response = policy.generate(
        "What does the private suite include?",
        community_evidence,
    )

    assert "Private accommodation for one resident" in response
    assert "bathroom" not in response.lower()
    assert "kitchenette" not in response.lower()

def test_disability_support_remains_unconfirmed(
    policy, community_evidence
):
    response = policy.generate(
        "Do you provide disability support?",
        community_evidence,
    )

    assert "don't have confirmed information" in response.lower()
    assert "do not offer" not in response.lower()

def test_nursing_care_is_reported_as_not_offered(
    policy, community_evidence
):
    response = policy.generate(
        "Do you provide nursing care?",
        community_evidence,
    )

    assert "do not offer nursing care" in response.lower()

def test_dementia_care_is_reported_as_not_offered(
    policy, community_evidence
):
    response = policy.generate(
        "Do you provide dementia care?",
        community_evidence,
    )

    assert "do not offer dementia care" in response.lower()

def test_pricing_is_not_invented(policy, community_evidence):
    response = policy.generate(
        "How much does accommodation cost?",
        community_evidence,
    )

    assert "not yet been established" in response.lower()
    assert "₦" not in response
    assert "NGN" not in response

def test_location_uses_confirmed_evidence_and_discloses_demo_status():
    policy = GroundedResponsePolicy()

    evidence = [
        {
            "category": "community",
            "claim": "location",
            "status": "confirmed",
            "value": {
                "city": "Lagos",
                "country": "Nigeria",
            },
        }
    ]

    response = policy.generate(
        "Where is WillowBrook Senior Living located?",
        evidence,
    )

    assert "Lagos" in response
    assert "Nigeria" in response
    assert "fictional" in response.lower()
    assert "not a real operating facility" in response.lower()

def test_facilities_use_confirmed_evidence(
    policy, community_evidence
):
    response = policy.generate(
        "What facilities do you have?",
        community_evidence,
    )

    assert "Landscaped gardens" in response
    assert "Shared social lounge" in response

def test_appointment_response_does_not_claim_booking(
    policy, community_evidence
):
    response = policy.generate(
        "Can I book a community tour?",
        community_evidence,
    )

    assert "community tours" in response.lower()
    assert "cannot currently verify" in response.lower()
    assert "your appointment is booked" not in response.lower()

def test_conversational_question_returns_none(
    policy, community_evidence
):
    response = policy.generate(
        "My mother is considering moving. Can you tell me more?",
        community_evidence,
    )

    assert response is None

def test_empty_question_returns_none(policy, community_evidence):
    response = policy.generate("", community_evidence)

    assert response is None

def test_weather_question_returns_verified_forecast_limitation(policy):
    response = policy.generate(
        "What will the weather be like in Lagos tomorrow?",
        [],
    )

    assert "don't have access to verified weather forecasts" in response.lower()
    assert "reliable weather service" in response.lower()

def test_superiority_question_discloses_fictional_status(policy):
    response = policy.generate(
        "Are you the best senior living community in Lagos?",
        [],
    )

    assert "don't have verified comparative rankings" in response.lower()
    assert "fictional demonstration community" in response.lower()
    assert "not a real operating facility" in response.lower()

def test_conversation_history_question_returns_none(
    policy, community_evidence
):
    response = policy.generate(
        "Can you remind me what name I gave you and who I am looking for accommodation for?",
        community_evidence,
    )

    assert response is None

def test_conversation_history_question_bypasses_accommodation_policy(
    policy, community_evidence
):
    response = policy.generate(
        "What did I tell you earlier about my accommodation needs?",
        community_evidence,
    )

    assert response is None