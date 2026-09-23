import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.retrieval import search_knowledge_base
from app.services.tools import (
    check_service_incidents,
    get_user,
    get_user_permissions,
    create_ticket,
    get_employee,
    get_all_employees,
    get_ticket
)


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

MODEL = "gpt-4o-mini"

CURRENT_USER_ID = "user_002"


SYSTEM_PROMPT = """
            You are OpsAI, an internal IT operations assistant.

            You help users troubleshoot IT problems, check operational status,
            view employee information according to backend authorization,
            and perform authorized actions.

            Important rules:

            1. The authenticated user is the user represented by the current user ID.
            Never ask the LLM user to provide or choose their own user ID.

            2. Use tools whenever the required information can be obtained from
            the backend or knowledge base.

            3. Never invent company policies, incidents, employee information,
            permissions, or ticket information.

            4. For IT troubleshooting questions, use search_knowledge_base first
            when the user is asking how to solve or troubleshoot a problem.

            5. Do not create a ticket merely because the user reports a problem.

            6. Only call create_ticket when the user explicitly asks to:
            - create a ticket
            - open a ticket
            - raise a ticket
            - submit a support request
            - report the issue through a support ticket
            or uses an equivalent explicit request.

            7. Reporting that something is broken is NOT an implicit request
            to create a ticket.

            8. If the user reports a VPN problem, first use search_knowledge_base
            when troubleshooting guidance is appropriate.

            9. If the user says they already followed troubleshooting steps and
            the problem still exists, use check_service_incidents to check
            whether there is a relevant active incident.

            10. Do not repeatedly call the same incident tool when the same
                incident information has already been retrieved in the conversation,
                unless the user explicitly asks to check again.

            11. When the user explicitly asks to create a ticket, call create_ticket.
                Use information from the conversation to create a useful description.
                Do not ask for information that is already available in the conversation.

            12. An explicit ticket request should result in a create_ticket tool call,
                even if another ticket was created earlier in the conversation.
                The user is explicitly requesting a ticket now.

            13. Do not say that a ticket has already been created instead of calling
                create_ticket when the user explicitly asks to create a new ticket.

            14. The create_ticket tool uses the authenticated user automatically.
                Never pass a different user ID unless the tool definition explicitly
                requires it.

            15. When the user asks to see their own details, call get_user.

            16. When the user asks about their own permissions, call get_user_permissions.

            17. When the user asks to list employees, list their employees,
                or view employees they manage, always call get_all_employees.
                Do not determine whether the user is authorized before calling
                the tool. The backend applies the user's role and access scope.

            18. Never assume that a request is unauthorized based only on
                the wording of the request. Use the appropriate tool and let
                the backend authorization result determine what can be returned.

            19. When the user asks about a specific employee, always call
                get_employee with the target employee's user_id. Do not decide
                whether the authenticated user is allowed to view that employee.
                The backend performs the authorization check.

            20. Do not call get_user_permissions before get_all_employees
                or get_employee. Those tools perform their own backend authorization
                using the authenticated user.

            21. When the user asks about an existing ticket, asks whether a ticket
                was created, or asks for the status or details of a ticket, use get_ticket
                to retrieve the ticket from the backend.

                22. If the user refers to "my ticket", use the ticket ID from the
                conversation when one is available. Do not invent a ticket ID.

                23. Do not claim that a ticket exists or provide its status based only
                on conversation history when the ticket can be verified using get_ticket.
            """


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": """
            Search the internal company knowledge base for relevant information.

            Use this tool when the user asks about:
            - IT troubleshooting
            - company policies
            - internal procedures
            - how to perform an IT-related task
            - information that may be contained in company documentation

            Do not use this tool for current operational status,
            employee information, permissions, or actions handled by other tools.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or information needed from the company knowledge base."
                    }
                },
                "required": ["query"]
            }
        }
    },
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
            },
        {
            "type": "function",
            "function": {
                "name": "get_ticket",
                "description": (
                    "Retrieve the details and current status of an existing IT support ticket. "
                    "Use this when the user asks about a ticket, asks whether a ticket was created, "
                    "or asks for the status/details of a ticket."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The ID of the ticket to retrieve."
                        }
                    },
                    "required": ["ticket_id"]
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "get_employee",
            "description": """
            Get information about a specific employee.

            Use this when the user asks about another employee by user ID.

            The backend determines whether the currently authenticated
            user is allowed to view that employee.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The ID of the employee to look up."
                    }
                },
                "required": [
                    "user_id"
                ]
            }
        }
    },
        {
            "type": "function",
            "function": {
                "name": "get_all_employees",
                "description": """
                Get the employees that the currently authenticated user is
                authorized to view.

                Admins can view all employees.
                Managers can view employees in their own team.
                Employees can only view themselves.

                The backend enforces these access rules.
                """,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
]


def execute_tool(name, arguments, user_id):

    if name == "search_knowledge_base":
        results = search_knowledge_base(
            query=arguments["query"],
            top_k=6
        )

        return [
            {
                "source": item["source"],
                "text": item["text"]
            }
            for item in results
        ]

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

    if name == "get_employee":
        return get_employee(
            target_user_id=arguments["user_id"],
            requester_user_id=user_id
        )

    if name == "get_all_employees":
        return get_all_employees(
            requester_user_id=user_id
        )

    if name == "create_ticket":
        return create_ticket(
            user_id=user_id,
            category=arguments["category"],
            description=arguments["description"]
        )
    
    if name == "get_ticket":
        return get_ticket(
            ticket_id=arguments["ticket_id"],
            requester_user_id=user_id
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