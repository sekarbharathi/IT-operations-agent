import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))


from app.services.langgraph_agent import (
    agent,
    SYSTEM_PROMPT,
)

from evaluation.evaluators.deterministic import (
    evaluate_case,
)


DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "opsai_cases.json"
)

REPORT_DIR = BASE_DIR / "reports"


def load_dataset():
    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def run_case(test_case):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": test_case["input"],
        },
    ]

    result = agent.invoke(
        {
            "messages": messages,
            "user_id": test_case["user_id"],
        }
    )

    evaluation = evaluate_case(
        result["messages"],
        test_case["expected"],
    )

    final_answer = next(
        (
            message.get("content", "")
            for message in reversed(result["messages"])
            if message.get("role") == "assistant"
            and message.get("content")
        ),
        "",
    )

    return {
        "id": test_case["id"],
        "category": test_case["category"],
        "description": test_case["description"],
        "input": test_case["input"],
        "user_id": test_case["user_id"],
        "passed": evaluation["passed"],
        "evaluation": evaluation,
        "answer": final_answer,
    }


def main():
    test_cases = load_dataset()

    results = []

    print("\nStarting OpsAI evaluation...\n")

    for test_case in test_cases:
        print(
            f"Running {test_case['id']}: "
            f"{test_case['description']}"
        )

        try:
            result = run_case(test_case)

        except Exception as exc:
            result = {
                "id": test_case["id"],
                "category": test_case["category"],
                "passed": False,
                "error": str(exc),
            }

        results.append(result)

        print(
            f"  {'PASS' if result['passed'] else 'FAIL'}"
        )
        print()

    total = len(results)
    passed = sum(
        result["passed"]
        for result in results
    )

    failed = total - passed

    pass_rate = (
        passed / total * 100
        if total
        else 0
    )

    report = {
        "evaluation": "OpsAI deterministic evaluation",
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate_percent": round(
            pass_rate,
            2,
        ),
        "results": results,
    }

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        REPORT_DIR
        / "evaluation_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print("=" * 45)
    print("OPS AI EVALUATION")
    print("=" * 45)
    print(f"Total tests: {total}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Pass rate:   {pass_rate:.2f}%")
    print()
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()