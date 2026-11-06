from src.agent.instructions import SYSTEM_INSTRUCTIONS

def test_instructions_prevent_unsupported_accommodation_claims():
    assert "Never invent" in SYSTEM_INSTRUCTIONS
    assert "unsupported" in SYSTEM_INSTRUCTIONS.lower()

def test_instructions_prevent_unsupported_promotional_claims():
    assert "promotional language" in SYSTEM_INSTRUCTIONS.lower()

def test_instructions_distinguish_evidence_statuses():
    assert "CONFIRMED" in SYSTEM_INSTRUCTIONS
    assert "NOT OFFERED" in SYSTEM_INSTRUCTIONS
    assert "UNCONFIRMED" in SYSTEM_INSTRUCTIONS

def test_instructions_protect_internal_evidence():
    assert "raw evidence records" in SYSTEM_INSTRUCTIONS.lower()
    assert "internal field names" in SYSTEM_INSTRUCTIONS.lower()

def test_instructions_prevent_false_booking_claims():
    instructions = SYSTEM_INSTRUCTIONS.lower()

    assert "never claim an appointment is booked" in instructions
    assert "verified confirmation" in instructions
    assert "never invent available dates or times" in instructions
    assert "never imply that calendly has been checked" in instructions

def test_instructions_prevent_unverified_follow_up_promises():
    instructions = SYSTEM_INSTRUCTIONS.lower()

    assert "never promise a community-team callback" in instructions
    assert "actual follow-up mechanism" in instructions