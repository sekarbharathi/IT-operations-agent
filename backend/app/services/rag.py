import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.retrieval import search_knowledge_base


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

1. Answer using the provided company knowledge.
2. Do not invent company policies or procedures.
3. If the provided knowledge does not contain enough information,
   say that you do not have enough information.
4. Be concise and helpful.
5. Do not claim that you performed an action unless a tool actually
   performed that action.
"""


def generate_answer(question: str):

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

    user_prompt = f"""
        Use the following company knowledge to answer the user's question.

        COMPANY KNOWLEDGE:

        {context}

        USER QUESTION:

        {question}
        """

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content

if __name__ == "__main__":

    question = input("Ask OpsAI: ")

    answer = generate_answer(question)

    print("\nOpsAI:")
    print(answer)