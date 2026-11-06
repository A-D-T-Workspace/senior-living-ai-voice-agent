import asyncio
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.engine import ConversationEngine
from src.conversation.state import create_conversation

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "grounding_cases.json"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs"

RESULTS_PATH = (
    OUTPUT_DIR / "grounding_evaluation_results.json"
)

def load_evaluation_dataset():
    """Load and validate the grounding evaluation dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    cases = dataset.get("evaluation_cases")

    if not isinstance(cases, list) or not cases:
        raise ValueError(
            "Dataset must contain a non-empty evaluation_cases list."
        )

    required_fields = {
        "id",
        "category",
        "question",
        "expected_facts",
        "required_behavior",
        "forbidden_claims",
    }

    for index, case in enumerate(cases):
        missing = required_fields - case.keys()

        if missing:
            raise ValueError(
                f"Evaluation case {index} is missing fields: "
                f"{sorted(missing)}"
            )

    return dataset

def detect_forbidden_claims(
    response: str,
    forbidden_claims: list[str],
) -> list[str]:
    """
    Flag literal forbidden phrases for human review.

    This is a heuristic check, not a semantic hallucination detector.
    """

    response_lower = response.lower()

    return [
        claim
        for claim in forbidden_claims
        if claim.lower() in response_lower
    ]


async def evaluate_case(engine, case):
    """Run one evaluation case through the conversation engine."""

    state = create_conversation(
        session_id=f"evaluation-{case['id']}"
    )

    response = await engine.respond(
        state=state,
        caller_message=case["question"],
    )

    flagged_claims = detect_forbidden_claims(
        response,
        case["forbidden_claims"],
    )

    return {
        "case_id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "expected_facts": case["expected_facts"],
        "required_behavior": case["required_behavior"],
        "response": response,
        "flagged_forbidden_claims": flagged_claims,
        "requires_human_review": True,
    }

async def main():
    """Run the complete grounding evaluation."""

    dataset = load_evaluation_dataset()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = ConversationEngine()

    cases = dataset["evaluation_cases"]
    results = []

    print("\n" + "=" * 60)
    print("WILLOWBROOK GROUNDING EVALUATION")
    print("=" * 60)

    print(f"Dataset: {dataset['dataset_name']}")
    print(f"Evaluation cases: {len(cases)}")
    print("\nStarting model evaluation...\n")

    for index, case in enumerate(cases, start=1):
        print(
            f"[{index}/{len(cases)}] "
            f"Evaluating {case['id']}: {case['question']}"
        )

        try:
            result = await evaluate_case(engine, case)
            results.append(result)

            if result["flagged_forbidden_claims"]:
                print("  WARNING: Potential forbidden claims detected.")

                for claim in result["flagged_forbidden_claims"]:
                    print(f"  - {claim}")
            else:
                print("  Completed. No literal forbidden phrase detected.")

        except Exception as error:
            error_type = type(error).__name__
            error_message = str(error)
            error_traceback = traceback.format_exc()

            print(f"  ERROR TYPE: {error_type}")
            print(f"  ERROR MESSAGE: {repr(error_message)}")
            print("  TRACEBACK:")
            print(error_traceback)

            results.append({
                "case_id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "error_type": error_type,
                "error": error_message,
                "traceback": error_traceback,
                "requires_human_review": True,
            })  

        print()

    successful_runs = [
        result for result in results
        if "response" in result
    ]

    flagged_runs = [
        result for result in successful_runs
        if result["flagged_forbidden_claims"]
    ]

    evaluation_report = {
        "dataset_name": dataset["dataset_name"],
        "dataset_version": dataset["version"],
        "model": engine.llm.model,
        "evaluation_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": {
            "total_cases": len(cases),
            "successful_runs": len(successful_runs),
            "failed_runs": len(cases) - len(successful_runs),
            "cases_with_literal_forbidden_phrase_flags": len(
                flagged_runs
            ),
            "human_review_required": True,
        },
        "results": results,
    }

    with RESULTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            evaluation_report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(f"Total cases: {len(cases)}")
    print(f"Successful runs: {len(successful_runs)}")
    print(f"Failed runs: {len(cases) - len(successful_runs)}")
    print(f"Cases flagged: {len(flagged_runs)}")

    print(f"\nResults saved to:\n{RESULTS_PATH}")

    print(
        "\nNOTE: Literal phrase detection is only a screening "
        "mechanism. All responses require factual review."
    )

if __name__ == "__main__":
    asyncio.run(main())
