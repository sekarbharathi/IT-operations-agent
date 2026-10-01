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


DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "multiturn_cases.json"
)


REPORT_DIR = BASE_DIR / "reports"


def load_dataset():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def extract_tool_calls(messages):

    tools = []

    for message in messages:

        if message.get("role") != "assistant":
            continue

        for tool_call in message.get(
            "tool_calls",
            []
        ):

            tools.append(
                tool_call["function"]["name"]
            )

    return tools


def get_final_answer(messages):

    for message in reversed(messages):

        if (
            message.get("role") == "assistant"
            and message.get("content")
        ):
            return message["content"]

    return ""


def evaluate_case(
    test_case,
):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    all_messages = []

    turn_results = []

    for turn_number, user_input in enumerate(
        test_case["turns"],
        start=1,
    ):

        messages.append({
            "role": "user",
            "content": user_input,
        })

        result = agent.invoke({
            "messages": messages,
            "user_id": test_case["user_id"],
        })

        messages = result["messages"]

        turn_results.append({
            "turn": turn_number,
            "input": user_input,
            "messages": messages,
        })

        all_messages = messages

    tool_calls = extract_tool_calls(
        all_messages
    )

    expected = test_case["expected"]

    required_tools = expected.get(
        "required_tools",
        [],
    )

    forbidden_tools = expected.get(
        "forbidden_tools",
        [],
    )

    required_checks = {
        tool: tool in tool_calls
        for tool in required_tools
    }

    forbidden_checks = {
        tool: tool not in tool_calls
        for tool in forbidden_tools
    }

    checks = {
        "required_tools": required_checks,
        "forbidden_tools": forbidden_checks,
    }

    passed = all(
        required_checks.values()
    ) and all(
        forbidden_checks.values()
    )

    max_tool_calls = expected.get("max_tool_calls", {})

    for tool_name, max_count in max_tool_calls.items():
        actual_count = tool_calls.count(tool_name)

        checks["max_tool_calls"] = checks.get(
            "max_tool_calls",
            True
        ) and actual_count <= max_count

    return {
        "id": test_case["id"],
        "category": test_case["category"],
        "description": test_case["description"],
        "passed": passed,
        "tool_calls": tool_calls,
        "checks": checks,
        "final_answer": get_final_answer(
            all_messages
        ),
    }


def main():

    test_cases = load_dataset()

    results = []

    print(
        "\nStarting OpsAI multi-turn evaluation...\n"
    )

    for test_case in test_cases:

        print(
            f"Running {test_case['id']}: "
            f"{test_case['description']}"
        )

        try:

            result = evaluate_case(
                test_case
            )

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

        if "tool_calls" in result:

            print(
                f"  Tools: "
                f"{result['tool_calls']}"
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
        "evaluation": (
            "OpsAI multi-turn evaluation"
        ),
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
        / "multiturn_evaluation_report.json"
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
    print("OPS AI MULTI-TURN EVALUATION")
    print("=" * 45)
    print(f"Total tests: {total}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Pass rate:   {pass_rate:.2f}%")
    print()
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()