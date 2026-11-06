import json
from pathlib import Path

class CommunityKnowledgeRetriever:
    """Retrieves structured, authoritative evidence from the community profile."""

    def __init__(self, profile_path=None):
        if profile_path is None:
            profile_path = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "processed"
                / "community_profile.json"
            )

        with open(profile_path, "r", encoding="utf-8") as file:
            self.profile = json.load(file)

    def _build_evidence(self):
        profile = self.profile

        community = profile["community"]
        care = profile["care_and_safety"]
        pricing = profile["pricing"]
        appointments = profile["appointments"]

        evidence = [
            {
                "category": "community",
                "claim": "community_name",
                "status": "confirmed",
                "value": community["name"],
            },
            {
                "category": "community",
                "claim": "location",
                "status": "confirmed",
                "value": {
                    "city": community["location"]["city"],
                    "country": community["location"]["country"],
                },
            },
            {
                "category": "community",
                "claim": "business_type",
                "status": "confirmed",
                "value": community["business_type"],
            },
            {
                "category": "community",
                "claim": "description",
                "status": "confirmed",
                "value": community["description"],
            },
        ]

        for option in profile["accommodation"]["options"]:
            evidence.append({
                "category": "accommodation",
                "claim": option["name"],
                "status": "confirmed",
                "value": option["description"],
            })

        for facility in profile["facilities"]:
            evidence.append({
                "category": "facilities",
                "claim": facility,
                "status": "confirmed",
                "value": facility,
            })

        for service in profile["services"]:
            evidence.append({
                "category": "services",
                "claim": service,
                "status": "confirmed",
                "value": service,
            })

        for care_item in [
            "medical_care",
            "nursing_care",
            "emergency_medical_services",
            "dementia_care",
        ]:
            value = care.get(care_item)

            evidence.append({
                "category": "care_and_safety",
                "claim": care_item,
                "status": (
                    "not_offered" if value is False
                    else "confirmed" if value is True
                    else "unconfirmed"
                ),
                "value": value,
            })

        evidence.append({
            "category": "care_and_safety",
            "claim": "specialist_disability_support",
            "status": "unconfirmed",
            "value": None,
        })

        evidence.append({
            "category": "pricing",
            "claim": "pricing",
            "status": "unconfirmed",
            "value": pricing["status"],
            "currency": pricing["currency"],
        })

        for appointment in appointments["offered"]:
            evidence.append({
                "category": "appointments",
                "claim": appointment,
                "status": "confirmed",
                "value": appointment,
            })

        evidence.append({
            "category": "appointments",
            "claim": "booking_required",
            "status": "confirmed",
            "value": appointments["booking_required"],
        })

        return evidence

    def retrieve(self, question: str):
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        query = question.lower()
        all_evidence = self._build_evidence()

        keyword_groups = {
            "community": [
                "location", "located", "where", "lagos",
                "nigeria", "independent living",
            ],
            "accommodation": [
                "suite", "room", "accommodation", "private",
                "shared", "living arrangement",
            ],
            "facilities": [
                "facility", "facilities", "garden", "lounge",
                "dining area", "recreational space",
                "outdoor", "outside", "relax", "relaxation",
            ],
            "services": [
                "service", "services", "meal", "food",
                "housekeeping", "activities", "events",
            ],
            "care_and_safety": [
                "medical", "nursing", "dementia", "memory care",
                "emergency", "disability", "specialist care",
                "healthcare", "care",
                "specialist support", "disability support",
            ],
            "pricing": [
                "price", "pricing", "cost", "fee", "fees",
                "how much", "payment",
            ],
            "appointments": [
                "appointment", "tour", "visit", "consultation",
                "booking", "availability", "schedule",
                "come and see", "see the place", "look around",
            ],
        }

        matched_categories = {
            category
            for category, terms in keyword_groups.items()
            if any(term in query for term in terms)
        }

        selected_evidence = []

        for item in all_evidence:
            if item["category"] not in matched_categories:
                continue

            if item["category"] == "accommodation":
                claim = item["claim"].lower()

                if "private" in query and "private" not in claim:
                    continue

                if "shared" in query and "shared" not in claim:
                    continue

            if item["category"] == "services":
                emergency_query = "emergency medical services" in query

                other_service_terms = [
                    "meal",
                    "food",
                    "housekeeping",
                    "activities",
                    "events",
                ]

                if emergency_query and not any(
                    term in query for term in other_service_terms
                ):
                    continue

            if item["category"] == "care_and_safety":
                claim_terms = {
                    "medical_care": ["medical care", "healthcare"],
                    "nursing_care": ["nursing"],
                    "emergency_medical_services": ["emergency"],
                    "dementia_care": ["dementia", "memory care"],
                    "specialist_disability_support": [
                        "disability",
                        "specialist care",
                        "specialist support",
                        "disability support",
                    ],
                }

                terms = claim_terms.get(item["claim"], [])

                if not any(term in query for term in terms):
                    continue

            selected_evidence.append(item)

        return {
            "question": question,
            "found": bool(selected_evidence),
            "evidence": selected_evidence,
            "message": (
                "Relevant evidence retrieved."
                if selected_evidence
                else "No relevant community evidence found."
            ),
        }
