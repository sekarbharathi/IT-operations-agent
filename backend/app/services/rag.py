import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.retrieval import search_knowledge_base
from app.services.tools import check_service_incidents


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

MODEL = "gpt-4o-mini"


SYSTEM_PROMPT = """
You are OpsAI, an internal IT operations assistant.

Your job is to help employees with IT-related questions.

Rules:

1. Answer using the provided company knowledge and tool results.
2. Do not invent company policies or procedures.
3. Use the check_service_incidents tool when the user asks
   about an outage, incident, or current service problem.
4. If the provided knowledge does not contain enough information,
   say that you do not have enough information.
5. Be concise and helpful.
6. Do not claim you performed an action unless a tool actually
   performed that action.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_service_incidents",
            "description": "Check whether there are incidents affecting a specific company service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The company service to check, such as vpn or email."
                    }
                },
                "required": ["service"]
            }
        }
    }
]


def execute_tool(name, arguments):

    if name == "check_service_incidents":
        return check_service_incidents(
            arguments["service"]
        )

    return {
        "error": f"Unknown tool: {name}"
    }


def generate_answer(question: str):

    # -----------------------------
    # 1. Retrieve company knowledge
    # -----------------------------

    results = search_knowledge_base(
        query=question,
        top_k=6
    )

    context_parts = []

    for result in results:
        context_parts.append(
            f"Source: {result['source']}\n"
            f"{result['text']}"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    # -----------------------------
    # 2. Initial LLM request
    # -----------------------------

    user_prompt = f"""
Use the following company knowledge to help answer the user's question.

COMPANY KNOWLEDGE:

{context}

USER QUESTION:

{question}
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    # -----------------------------
    # 3. Let the LLM decide
    #    whether to call a tool
    # -----------------------------

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )

    assistant_message = response.choices[0].message

    # -----------------------------
    # 4. No tool needed
    # -----------------------------

    if not assistant_message.tool_calls:

        return assistant_message.content

    # -----------------------------
    # 5. Tool call requested
    # -----------------------------

    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in assistant_message.tool_calls
            ]
        }
    )

    # -----------------------------
    # 6. Execute each requested tool
    # -----------------------------

    for tool_call in assistant_message.tool_calls:

        tool_name = tool_call.function.name

        arguments = json.loads(
            tool_call.function.arguments
        )

        tool_result = execute_tool(
            tool_name,
            arguments
        )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            }
        )

    # -----------------------------
    # 7. Send tool result back
    #    to the LLM
    # -----------------------------

    final_response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0
    )

    return final_response.choices[0].message.content


if __name__ == "__main__":

    question = input("Ask OpsAI: ")

    answer = generate_answer(question)

    print("\nOpsAI:")
    print(answer)