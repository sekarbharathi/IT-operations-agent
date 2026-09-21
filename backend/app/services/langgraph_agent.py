import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.services.rag import (
    openai_client,
    MODEL,
    SYSTEM_PROMPT,
    TOOLS,
    execute_tool,
    CURRENT_USER_ID
)

from app.services.retrieval import search_knowledge_base


class AgentState(TypedDict):
    messages: list
    user_id: str
    retrieved_context: str


def retrieve_knowledge(state: AgentState):
    """
    Retrieve relevant company knowledge for the current user request.
    The retrieved knowledge is stored separately from the conversation.
    """

    latest_user_message = ""

    for message in reversed(state["messages"]):
        if message["role"] == "user":
            latest_user_message = message["content"]
            break

    results = search_knowledge_base(
        query=latest_user_message,
        top_k=6
    )

    context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}"
        for item in results
    )

    return {
        "retrieved_context": context
    }


def call_model(state: AgentState):

    # Build the messages sent to the LLM.
    messages = list(state["messages"])

    # Add RAG context only for this LLM call.
    if state["retrieved_context"]:
        messages.append({
            "role": "system",
            "content": f"""
Relevant company knowledge for the current request:

{state["retrieved_context"]}
"""
        })

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )

    assistant_message = response.choices[0].message

    message = {
        "role": "assistant",
        "content": assistant_message.content
    }

    if assistant_message.tool_calls:

        message["tool_calls"] = [
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

    return {
        "messages": state["messages"] + [message]
    }


def execute_tools(state: AgentState):

    last_message = state["messages"][-1]

    tool_messages = []

    print("\nLLM requested tool(s):")

    for tool_call in last_message["tool_calls"]:

        tool_name = tool_call["function"]["name"]

        arguments = json.loads(
            tool_call["function"]["arguments"]
        )

        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        result = execute_tool(
        tool_name,
        arguments,
        state["user_id"]
        )

        print(f"Tool result: {result}")

        tool_messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(result)
        })

    return {
        "messages": state["messages"] + tool_messages
    }


def should_continue(state: AgentState):

    last_message = state["messages"][-1]

    if last_message.get("tool_calls"):
        return "tools"

    return END


def build_agent():

    graph = StateGraph(AgentState)

    graph.add_node(
        "retrieve_knowledge",
        retrieve_knowledge
    )

    graph.add_node(
        "agent",
        call_model
    )

    graph.add_node(
        "tools",
        execute_tools
    )

    graph.add_edge(
        START,
        "retrieve_knowledge"
    )

    graph.add_edge(
        "retrieve_knowledge",
        "agent"
    )

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    graph.add_edge(
        "tools",
        "agent"
    )

    return graph.compile()


agent = build_agent()


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

        messages.append({
            "role": "user",
            "content": question
        })

        result = agent.invoke({
            "messages": messages,
            "user_id": CURRENT_USER_ID,
            "retrieved_context": ""
        })

        messages = result["messages"]

        answer = messages[-1]["content"]

        print("\nOpsAI:")
        print(answer)