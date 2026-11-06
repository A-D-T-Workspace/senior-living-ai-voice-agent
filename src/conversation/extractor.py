import json

from pydantic import ValidationError

from src.agent.llm import OllamaClient
from src.agent.instructions import DISCOVERY_QUESTIONS
from src.conversation.extraction import DiscoveryExtraction

class DiscoveryExtractor:
    """Extract structured discovery answers using an LLM."""

    def __init__(self, llm_client=None):
        self.llm = llm_client or OllamaClient()

    async def extract(
        self,
        caller_message: str,
    ) -> DiscoveryExtraction:
        """Extract and validate discovery answers from caller input."""

        if not caller_message.strip():
            raise ValueError("Caller message cannot be empty.")

        system_prompt = (
            "You are a structured information extraction system.\n"
            "Extract only information explicitly provided by the caller.\n"
            "Do not invent, assume, or infer unsupported answers.\n\n"
            "Return valid JSON with this exact structure:\n"
            '{"answers": [{"question": "...", "answer": "...", '
            '"evidence": "...", "certainty": "explicit", '
            '"is_correction": false}]}\n\n'
            "Rules:\n"
            "1. Use only the supplied discovery questions.\n"
            "2. Extract EVERY distinct answer explicitly supported by the caller.\n"
            "3. Never stop after extracting just one answer when more are available.\n"
            "4. One caller message may contain answers to several questions.\n"
            "5. Map each fact to its most appropriate discovery question.\n"
            "6. Evidence must be an exact excerpt from the caller message.\n"
            "7. Use explicit when the caller clearly states an answer.\n"
            "8. Use uncertain when the caller expresses uncertainty.\n"
            "9. Never extract answers from questions asked by the caller.\n"
            "10. Set is_correction to true only when the caller clearly "
            "corrects previously supplied information.\n"
            "11. Return an empty answers list when no discovery answer "
            "is supported.\n\n"
            "FACT-TO-QUESTION MAPPING:\n"
            "- A person's age belongs to the age question.\n"
            "- Where the person currently lives belongs to the current "
            "living situation question.\n"
            "- For example, 'lives with me' means 'Lives with the caller'.\n"
            "- Never interpret living with a family member as a shared suite.\n"
            "- A private suite or shared suite being considered belongs "
            "to the living arrangement question.\n"
            "- Reasons for considering senior living belong to the motivation "
            "question.\n"
            "- For example, preferring personal space is a motivation.\n"
            "- Do not confuse current living situation with future accommodation.\n"
            "- Do not combine different facts into one answer.\n"
            "- Every evidence value must be copied character-for-character "
            "from the caller message.\n"
            "- Never invent, reconstruct, or paraphrase evidence.\n"
            + "\n".join(
                f"- {question}"
                for question in DISCOVERY_QUESTIONS
            )
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": caller_message,
            },
        ]

        response = await self.llm.chat(
            messages,
            response_format="json",
        )

        try:
            data = json.loads(response)
            extraction = DiscoveryExtraction.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(
                "LLM returned an invalid discovery extraction."
            ) from exc

        validated_answers = []

        for answer in extraction.answers:
            if answer.question not in DISCOVERY_QUESTIONS:
                continue

            if answer.evidence not in caller_message:
                continue

            validated_answers.append(answer)

        return DiscoveryExtraction(answers=validated_answers)