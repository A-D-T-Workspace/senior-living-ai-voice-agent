import re

class GroundedResponsePolicy:
    """
    Builds factual responses directly from retrieved community evidence.

    Returns None when a question is conversational and should be
    handled by the language model.
    """

    def _asks_about_weather(self, query: str) -> bool:
        return bool(
            re.search(
                r"\b(weather|forecast|rain|temperature)\b",
                query,
            )
        )

    def _asks_about_superiority(self, query: str) -> bool:
        terms = ["best", "better than", "top-rated", "number one", "highest rated"]
        return any(term in query for term in terms)

    def generate(self, question: str, evidence: list[dict]) -> str | None:
        query = question.lower().strip()

        if not query:
            return None
        
        if self._asks_about_conversation_history(query):
            return None

        if self._asks_about_weather(query):
            return (
                "I don't have access to verified weather forecasts. "
                "Please check a reliable weather service for the latest forecast."
            )

        if self._asks_about_superiority(query):
            return (
                "I don't have verified comparative rankings for senior living "
                "communities in Lagos. WillowBrook Senior Living is a fictional "
                "demonstration community, not a real operating facility."
            )

        if self._asks_about_pricing(query):
            if not self._find(evidence, "pricing"):
                return None
            return self._pricing_response(evidence)

        if self._asks_about_care(query):
            if not self._find(evidence, "care_and_safety"):
                return None
            return self._care_response(query, evidence)

        if self._asks_about_accommodation(query):
            if not self._find(evidence, "accommodation"):
                return None
            return self._accommodation_response(query, evidence)

        if self._asks_about_facilities(query):
            if not self._find(evidence, "facilities"):
                return None
            return self._list_response(
                evidence,
                category="facilities",
                introduction="Our community facilities include",
            )

        if self._asks_about_services(query):
            if not self._find(evidence, "services"):
                return None
            return self._list_response(
                evidence,
                category="services",
                introduction="Our listed services include",
            )

        if self._asks_about_location(query):
            if not any(
                item.get("category") == "community"
                and item.get("claim") == "location"
                for item in evidence
            ):
                return None
            return self._location_response(evidence)

        if self._asks_about_appointments(query):
            if not self._find(evidence, "appointments"):
                return None
            return self._appointment_response(evidence)

        return None

    @staticmethod
    def _asks_about_pricing(query: str) -> bool:
        terms = ["price", "pricing", "cost", "fee", "fees", "how much"]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_care(query: str) -> bool:
        terms = [
            "medical care",
            "healthcare",
            "nursing",
            "dementia",
            "memory care",
            "emergency medical",
            "disability support",
            "specialist care",
            "specialist support",
        ]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_accommodation(query: str) -> bool:
        terms = [
            "suite",
            "room",
            "accommodation",
            "private",
            "shared",
        ]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_facilities(query: str) -> bool:
        terms = [
            "facility",
            "facilities",
            "garden",
            "lounge",
            "dining area",
            "recreational space",
        ]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_services(query: str) -> bool:
        terms = [
            "service",
            "services",
            "housekeeping",
            "meal",
            "food",
            "activities",
            "events",
        ]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_location(query: str) -> bool:
        terms = ["where", "location", "located", "which city"]
        return any(term in query for term in terms)

    @staticmethod
    def _asks_about_appointments(query: str) -> bool:
        terms = [
            "appointment",
            "tour",
            "visit",
            "consultation",
            "booking",
        ]
        return any(term in query for term in terms)

    @staticmethod
    def _find(evidence: list[dict], category: str) -> list[dict]:
        return [
            item for item in evidence
            if item.get("category") == category
        ]
    
    @staticmethod
    def _asks_about_conversation_history(query: str) -> bool:
        patterns = [
            r"\bremind me\b",
            r"\bwhat did i (?:say|tell you|mention)\b",
            r"\bwhat name did i\b",
            r"\bwho am i looking for\b",
            r"\bwhy am i looking\b",
            r"\bwhat was i looking for\b",
            r"\bwhat did i ask\b",
            r"\bearlier in (?:our )?conversation\b",
        ]

        return any(
            re.search(pattern, query, re.IGNORECASE)
            for pattern in patterns
        )

    def _pricing_response(self, evidence: list[dict]) -> str:
        records = self._find(evidence, "pricing")

        if not records:
            return (
                "I don't have confirmed pricing information yet. "
                "I can help arrange a conversation with the community team."
            )

        record = records[0]

        if record.get("status") != "confirmed":
            return (
                "Our pricing has not yet been established, "
                "so I cannot provide a confirmed price."
            )

        return f"Our confirmed pricing information is: {record.get('value')}."

    def _care_response(
        self,
        query: str,
        evidence: list[dict],
    ) -> str:
        care_terms = {
            "medical_care": ["medical care", "healthcare"],
            "nursing_care": ["nursing"],
            "dementia_care": ["dementia", "memory care"],
            "emergency_medical_services": ["emergency medical"],
            "specialist_disability_support": [
                "disability support",
                "specialist care",
                "specialist support",
            ],
        }

        matching_claims = [
            claim
            for claim, terms in care_terms.items()
            if any(term in query for term in terms)
        ]

        records = [
            item for item in evidence
            if item.get("category") == "care_and_safety"
            and item.get("claim") in matching_claims
        ]

        if not records:
            return (
                "I don't have confirmed information about that type "
                "of support. I can help arrange a conversation with "
                "the community team."
            )

        responses = []

        for record in records:
            claim = record["claim"].replace("_", " ")

            if record.get("status") == "not_offered":
                responses.append(
                    f"We do not offer {claim}."
                )

            elif record.get("status") == "confirmed":
                responses.append(
                    f"We offer {claim}."
                )

            else:
                responses.append(
                    f"I don't have confirmed information about "
                    f"{claim} yet."
                )

        return " ".join(responses)

    
    def _accommodation_response(
        self,
        query: str,
        evidence: list[dict],
    ) -> str:
        records = self._find(evidence, "accommodation")

        confirmed_records = [
            item
            for item in records
            if item.get("status") == "confirmed"
        ]

        query_lower = query.lower()

        if "private" in query_lower:
            confirmed_records = [
                item for item in confirmed_records
                if "private" in item.get("claim", "").lower()
            ]

        elif "shared" in query_lower:
            confirmed_records = [
                item for item in confirmed_records
                if "shared" in item.get("claim", "").lower()
            ]

        if not confirmed_records:
            return (
                "I don't have confirmed accommodation details "
                "for that question yet."
            )

        descriptions = [
            f"{item['claim']}: {item['value']}".rstrip(".")
            for item in confirmed_records
        ]

        if len(descriptions) == 1:
            return f"We offer {descriptions[0]}."

        return (
            "Our listed accommodation options are "
            + "; ".join(descriptions)
            + "."
        )

    def _list_response(
        self,
        evidence: list[dict],
        category: str,
        introduction: str,
    ) -> str:
        records = self._find(evidence, category)

        confirmed_items = [
            item["value"]
            for item in records
            if item.get("status") == "confirmed"
        ]

        if not confirmed_items:
            return (
                "I don't have confirmed information about that yet. "
                "I can help arrange a conversation with the community team."
            )

        return introduction + ": " + ", ".join(confirmed_items) + "."

    def _location_response(self, evidence: list[dict]) -> str:
        records = self._find(evidence, "community")

        location_record = next(
            (
                item for item in records
                if item.get("claim") == "location"
                and item.get("status") == "confirmed"
            ),
            None,
        )

        if not location_record:
            return "I don't have confirmed location information yet."

        location = location_record["value"]

        return (
            f"The configured demonstration location for WillowBrook "
            f"Senior Living is {location['city']}, {location['country']}. "
            f"Please note that WillowBrook is a fictional community "
            f"created for this demonstration, not a real operating facility."
        )

    def _appointment_response(self, evidence: list[dict]) -> str:
        records = self._find(evidence, "appointments")

        offered = [
            item["value"]
            for item in records
            if item.get("status") == "confirmed"
            and item.get("claim") != "booking_required"
        ]

        if not offered:
            return (
                "I don't have confirmed appointment information yet. "
                "I can help arrange a conversation with the community team."
            )

        appointment_text = ", ".join(offered)

        return (
            f"We offer {appointment_text.lower()}. "
            "Appointments require booking, but I cannot currently "
            "verify available times or complete a booking."
        )
