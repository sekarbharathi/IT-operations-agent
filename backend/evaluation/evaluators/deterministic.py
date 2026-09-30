import json


def extract_tool_calls(messages):
    tool_calls = []

    for message in messages:
        if message.get("role") != "assistant":
            continue

        for tool_call in message.get("tool_calls", []):
            try:
                arguments = json.loads(
                    tool_call["function"]["arguments"]
                )
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            tool_calls.append(
                {
                    "name": tool_call["function"]["name"],
                    "arguments": arguments,
                }
            )

    return tool_calls


def extract_tool_results(messages):
    results = []

    for message in messages:
        if message.get("role") != "tool":
            continue

        content = message.get("content", "")

        try:
            results.append(json.loads(content))
        except (json.JSONDecodeError, TypeError):
            continue

    return results


def evaluate_tool_selection(tool_calls, expected_tool):
    actual_tools = [
        tool_call["name"]
        for tool_call in tool_calls
    ]

    # Some tests intentionally expect no tool call.
    if expected_tool is None:
        return {
            "passed": len(actual_tools) == 0,
            "expected": None,
            "actual": actual_tools,
        }

    return {
        "passed": expected_tool in actual_tools,
        "expected": expected_tool,
        "actual": actual_tools,
    }


def evaluate_tool_arguments(
    tool_calls,
    expected_tool,
    expected_arguments,
    arguments_were_specified,
):
    if not arguments_were_specified:
        return {
            "passed": True,
            "skipped": True,
        }

    if expected_tool is None:
        return {
            "passed": True,
            "skipped": True,
        }

    matching_calls = [
        tool_call
        for tool_call in tool_calls
        if tool_call["name"] == expected_tool
    ]

    if not matching_calls:
        return {
            "passed": False,
            "expected": expected_arguments,
            "actual": [],
            "reason": "Expected tool was not called",
        }

    for tool_call in matching_calls:
        actual_arguments = tool_call["arguments"]

        if actual_arguments == expected_arguments:
            return {
                "passed": True,
                "expected": expected_arguments,
                "actual": actual_arguments,
            }

    return {
        "passed": False,
        "expected": expected_arguments,
        "actual": [
            tool_call["arguments"]
            for tool_call in matching_calls
        ],
    }


def _evaluate_employee_details(
    result,
    expected_employee,
):
    if not isinstance(result, dict):
        return False

    employee = result.get("user", {})

    return all(
        employee.get(key) == value
        for key, value in expected_employee.items()
    )


def _evaluate_permissions(
    result,
    expected_permissions,
):
    if not isinstance(result, dict):
        return False

    actual_permissions = result.get(
        "permissions",
        [],
    )

    return (
        set(actual_permissions)
        == set(expected_permissions)
    )


def _evaluate_incident_status(
    result,
    expected_status,
):
    # check_service_incidents currently returns
    # a list directly.
    if isinstance(result, list):
        return any(
            isinstance(incident, dict)
            and incident.get("status") == expected_status
            for incident in result
        )

    # Also support a wrapped response:
    # {"success": true, "incidents": [...]}
    if isinstance(result, dict):
        incidents = result.get(
            "incidents",
            [],
        )

        return any(
            isinstance(incident, dict)
            and incident.get("status") == expected_status
            for incident in incidents
        )

    return False



def evaluate_tool_result(
    tool_results,
    expected
):
    if not tool_results:
        return {
            "passed": False,
            "reason": "No tool result found",
        }

    expected_success = expected.get("success")

    # Some tools return a list directly
    normalized_results = []

    for result in tool_results:
        if isinstance(result, list):
            normalized_results.extend(result)
        else:
            normalized_results.append(result)

    if expected_success is not None:
        matching_result = None

        for result in normalized_results:
            if (
                isinstance(result, dict)
                and result.get("success") == expected_success
            ):
                matching_result = result
                break

        if matching_result is None:
            # If the tool itself returns a list of records,
            # treat the list as the successful result.
            if normalized_results:
                matching_result = {
                    "data": normalized_results
                }
            else:
                return {
                    "passed": False,
                    "reason": "Expected result was not found",
                    "expected_success": expected_success,
                    "actual_results": tool_results,
                }
    else:
        matching_result = normalized_results[-1]

    checks = {
        "result_found": True,
    }

    if expected.get("error_contains"):
        error = matching_result.get(
            "error",
            ""
        )

        checks["expected_error"] = (
            expected["error_contains"].lower()
            in error.lower()
        )

    if expected.get("ticket_status"):
        ticket = matching_result.get(
            "ticket",
            {}
        )

        checks["ticket_status"] = (
            ticket.get("status")
            == expected["ticket_status"]
        )

    if expected.get("incident_status"):
        incidents = matching_result.get(
            "incidents",
            []
        )

        if not incidents:
            incidents = matching_result.get(
                "data",
                []
            )

        checks["incident_status"] = any(
            incident.get("status")
            == expected["incident_status"]
            for incident in incidents
        )

    if expected.get("employee"):
        employee = matching_result.get(
            "user",
            matching_result
        )

        expected_employee = expected["employee"]

        checks["employee_details"] = all(
            employee.get(key) == value
            for key, value in expected_employee.items()
        )

    if expected.get("permissions"):
        actual_permissions = matching_result.get(
            "permissions",
            []
        )

        checks["permissions"] = (
            set(actual_permissions)
            == set(expected["permissions"])
        )

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "result": matching_result,
    }

def evaluate_final_answer(
    final_answer,
    expected,
):
    checks = {}

    contains = expected.get(
        "final_answer_contains",
        [],
    )
    contains_any = expected.get(
        "final_answer_contains_any",
        [],
    )

    if contains_any:
        answer_lower = final_answer.lower()

        checks["contains_any"] = any(
            phrase.lower() in answer_lower
            for phrase in contains_any
        )

    if isinstance(contains, str):
        contains = [contains]

    if contains:
        answer_lower = final_answer.lower()

        checks["contains"] = all(
            phrase.lower() in answer_lower
            for phrase in contains
        )

    not_contains = expected.get(
        "final_answer_not_contains",
        [],
    )

    if isinstance(not_contains, str):
        not_contains = [not_contains]

    if not_contains:
        answer_lower = final_answer.lower()

        checks["not_contains"] = all(
            phrase.lower() not in answer_lower
            for phrase in not_contains
        )

    if not checks:
        return {
            "passed": True,
            "skipped": True,
        }

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "answer": final_answer,
    }

def evaluate_rag_result(
    tool_results,
    expected,
):
    rag_results = []

    for result in tool_results:
        if isinstance(result, list):
            rag_results.extend(result)
        elif isinstance(result, dict):
            rag_results.append(result)

    checks = {}

    # Some RAG queries are expected to return
    # no relevant documents.
    if expected.get("rag_no_results"):
        checks["no_results"] = len(rag_results) == 0

    # Other RAG queries must return at least one result.
    elif not rag_results:
        return {
            "passed": False,
            "reason": "No RAG results found",
        }

    else:
        checks["result_found"] = True

    expected_source = expected.get("rag_source")

    if expected_source:
        checks["expected_source"] = any(
            isinstance(item, dict)
            and item.get("source") == expected_source
            for item in rag_results
        )

    forbidden_source = expected.get("rag_source_not")

    if forbidden_source:
        checks["forbidden_source_absent"] = not any(
            isinstance(item, dict)
            and item.get("source") == forbidden_source
            for item in rag_results
        )

    expected_text = expected.get("rag_contains")

    if expected_text:
        combined_text = " ".join(
            item.get("text", "")
            for item in rag_results
            if isinstance(item, dict)
        )

        checks["expected_content"] = (
            expected_text.lower()
            in combined_text.lower()
        )

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "results": rag_results,
    }


def evaluate_case(
    messages,
    expected,
    final_answer="",
):
    tool_calls = extract_tool_calls(messages)
    tool_results = extract_tool_results(messages)

    expected_tool = expected.get("tool")

    tool_check = evaluate_tool_selection(
        tool_calls,
        expected_tool,
    )

    arguments_were_specified = (
        "arguments" in expected
    )

    expected_arguments = expected.get(
        "arguments",
        {},
    )

    argument_check = evaluate_tool_arguments(
        tool_calls,
        expected_tool,
        expected_arguments,
        arguments_were_specified,
    )

    if expected_tool == "search_knowledge_base":
        result_check = evaluate_rag_result(
            tool_results,
            expected,
        )
    elif expected_tool is None:
        result_check = {
            "passed": True,
            "skipped": True,
        }
    else:
        result_check = evaluate_tool_result(
            tool_results,
            expected,
        )

    answer_check = evaluate_final_answer(
        final_answer,
        expected,
    )

    return {
        "passed": (
            tool_check["passed"]
            and argument_check["passed"]
            and result_check["passed"]
            and answer_check["passed"]
        ),
        "tool_selection": tool_check,
        "tool_arguments": argument_check,
        "tool_result": result_check,
        "final_answer": answer_check,
    }