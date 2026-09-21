import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.retrieval import search_knowledge_base
from app.services.tools import (
    check_service_incidents,
    get_user,
    get_user_permissions,
    create_ticket
)


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

MODEL = "gpt-4o-mini"

CURRENT_USER_ID = "user_003"


SYSTEM_PROMPT = """
        You are OpsAI, an internal IT operations assistant.

        Your job is to help employees troubleshoot IT issues, check operational status,
        and perform authorized IT actions using the available tools.

        Rules:

        1. Use the company knowledge provided in the conversation to answer
        troubleshooting and policy questions.

        2. Use tools when the user asks for information that requires current
        operational data or an action.

        3. Use check_service_incidents when:
        - the user asks whether there is an active incident or outage, OR
        - the user explicitly asks about the current status of a service.

        4. Do NOT call check_service_incidents just because the conversation is
        about a service that has had an incident before.

        5. If the user provides additional information about an existing problem,
        such as an error message, operating system, or troubleshooting result,
        use the information from the conversation. Do not repeat tool calls
        unless current data is actually needed.

        6. Only create a ticket when the user explicitly asks for one.

        7. When creating a ticket, use information already available in the
        conversation to write a concise and useful description. Do not ask for
        unnecessary additional troubleshooting details.

        8. Always use the current authenticated user ID when calling user-related
        tools.

        9. Never claim that an action was completed unless the corresponding tool
        successfully completed it.

        10. If a tool returns an error or permission failure, clearly explain that
        the action could not be completed.

        11. Keep responses concise and practical.

        12. When the user gives a short follow-up message, interpret it in the
        context of the existing conversation rather than treating it as a
        completely new request.

        13. If a tool returns an error or reports that a service is unavailable,
        do not invent or assume the missing information. Clearly tell the user
        that the requested information or action could not be completed.
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get information about a company employee.",
            "parameters": {
                "type": "object",
                "properties": {
                   
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_permissions",
            "description": "Get the permissions assigned to a company employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    
                },
                "required": []
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": """
        Create an IT support ticket for an employee.

        Use this tool when the user explicitly requests a ticket.
        The ticket does not require operating system, VPN version,
        error message, start time, or troubleshooting history.

        Use the information already available in the conversation
        to create a concise ticket description.
        """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "The category of the IT issue, such as VPN, Email, or WiFi."
                        },
                        "description": {
                            "type": "string",
                            "description": """
                                A concise description of the user's problem.
                                Use the information already provided by the user.
                                Do not ask the user for additional troubleshooting details.
                                """
                        }
                    },
                    "required": [
                        "category",
                        "description"
                    ]
                }
            }
        }
]


def execute_tool(name, arguments, user_id):

    if name == "check_service_incidents":
        return check_service_incidents(
            arguments["service"]
        )

    if name == "get_user":
        return get_user(
            user_id
        )

    if name == "get_user_permissions":
        return get_user_permissions(
            user_id
        )

    if name == "create_ticket":
        return create_ticket(
            user_id=user_id,
            category=arguments["category"],
            description=arguments["description"]
        )

    return {
        "error": f"Unknown tool: {name}"
    }

def generate_answer(question, messages):
    # Retrieve relevant knowledge for this user message
    results = search_knowledge_base(
        query=question,
        top_k=6
    )

    context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}"
        for item in results
    )

    user_prompt = f"""
        Current authenticated user ID: {CURRENT_USER_ID}

        Company knowledge:
        {context}

        User message:
        {question}
    """

    # Add the new user message to the existing conversation
    messages.append({
        "role": "user",
        "content": user_prompt
    })

    # Keep running until the LLM gives a normal answer
    while True:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0
        )

        assistant_message = response.choices[0].message

        # No tool call = final response
        if not assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content
            })

            return assistant_message.content

        # Add the assistant's tool request to conversation history
        messages.append({
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
        })

        print("\nLLM requested tool(s):")

        # Execute every requested tool
        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"Tool: {tool_name}")
            print(f"Arguments: {arguments}")

            result = execute_tool(
                tool_name,
                arguments
            )

            print(f"Tool result: {result}")

            # Give the tool result back to the LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })
        

if __name__ == "__main__":

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    while True:

        question = input("\nAsk OpsAI: ")

        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        answer = generate_answer(
            question,
            messages
        )

        print("\nOpsAI:")
        print(answer)