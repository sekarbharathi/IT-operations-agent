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
    / "end_to_end_cases.json"
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


def extract_tool_results(messages):

    results = []

    for message in messages:

        if message.get("role") != "tool":
            continue

        try:
            content = json.loads(
                message.get("content", "{}")
            )

        except json.JSONDecodeError:

            continue

        if isinstance(content, list):

            results.extend(content)

        else:

            results.append(content)

    return results


def get_final_answer(messages):

    for message in reversed(messages):

        if (
            message.get("role") == "assistant"
            and message.get("content")
        ):

            return message["content"]

    return ""


def evaluate_rag_result(
    tool_results,
    expected,
):

    rag_results = []

    for result in tool_results:

        if not isinstance(result, dict):
            continue

        if "matches" in result:
            rag_results.extend(
                result["matches"]
            )

        elif (
            "source" in result
            and "text" in result
        ):
            rag_results.append(result)

    checks = {}

    expected_source = expected.get(
        "rag_source"
    )

    if expected_source:

        checks["rag_source"] = (
            any(
                match.get("source")
                == expected_source
                for match in rag_results
                if isinstance(match, dict)
            )
        )

    expected_top_source = expected.get(
        "rag_top_source"
    )

    if expected_top_source:

        checks["rag_top_source"] = (
            bool(rag_results)
            and isinstance(
                rag_results[0],
                dict,
            )
            and rag_results[0].get("source")
            == expected_top_source
        )

    forbidden_source = expected.get(
        "rag_source_not"
    )

    if forbidden_source:

        checks["rag_source_not"] = (
            all(
                match.get("source")
                != forbidden_source
                for match in rag_results
                if isinstance(match, dict)
            )
        )

    return checks


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

    for user_input in test_case["turns"]:

        messages.append({
            "role": "user",
            "content": user_input,
        })

        result = agent.invoke({
            "messages": messages,
            "user_id": test_case["user_id"],
        })

        messages = result["messages"]

        all_messages = messages

    tool_calls = extract_tool_calls(
        all_messages
    )

    tool_results = extract_tool_results(
        all_messages
    )

    final_answer = get_final_answer(
        all_messages
    )

    expected = test_case["expected"]

    checks = {}

    # Required tools
    required_tools = expected.get(
        "required_tools",
        [],
    )

    checks["required_tools"] = {
        tool: tool in tool_calls
        for tool in required_tools
    }

    # Forbidden tools
    forbidden_tools = expected.get(
        "forbidden_tools",
        [],
    )

    checks["forbidden_tools"] = {
        tool: tool not in tool_calls
        for tool in forbidden_tools
    }

    # Maximum number of calls for specific tools
    max_tool_calls = expected.get(
        "max_tool_calls",
        {},
    )

    if max_tool_calls:

        checks["max_tool_calls"] = {}

        for tool, maximum in max_tool_calls.items():

            actual_count = tool_calls.count(tool)

            checks["max_tool_calls"][tool] = (
                actual_count <= maximum
            )

    # RAG checks
    rag_checks = evaluate_rag_result(
        tool_results,
        expected,
    )

    if rag_checks:

        checks.update(
            rag_checks
        )

    # Final answer must contain
    expected_contains = expected.get(
        "final_answer_contains",
        [],
    )

    if expected_contains:

        checks["final_answer_contains"] = {
            text: text.lower()
            in final_answer.lower()
            for text in expected_contains
        }

    # Final answer must contain at least one
    expected_contains_any = expected.get(
        "final_answer_contains_any",
        [],
    )

    if expected_contains_any:

        checks["final_answer_contains_any"] = any(
            text.lower()
            in final_answer.lower()
            for text in expected_contains_any
        )

    # Final answer must not contain
    forbidden_text = expected.get(
        "final_answer_not_contains",
        [],
    )

    if forbidden_text:

        checks["final_answer_not_contains"] = {
            text: text.lower()
            not in final_answer.lower()
            for text in forbidden_text
        }

    passed = all(
        value
        if isinstance(value, bool)
        else all(value.values())
        for value in checks.values()
    )

    return {
        "id": test_case["id"],
        "category": test_case["category"],
        "description": test_case["description"],
        "passed": passed,
        "tool_calls": tool_calls,
        "checks": checks,
        "final_answer": final_answer,
    }


def main():

    test_cases = load_dataset()

    results = []

    print(
        "\nStarting OpsAI end-to-end evaluation...\n"
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
                "description": test_case["description"],
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
            "OpsAI end-to-end evaluation"
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
        / "end_to_end_evaluation_report.json"
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
    print("OPS AI END-TO-END EVALUATION")
    print("=" * 45)
    print(f"Total tests: {total}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Pass rate:   {pass_rate:.2f}%")
    print()
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()