import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

pinecone_client = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pinecone_client.Index(
    PINECONE_INDEX_NAME
)


EMBEDDING_MODEL = "text-embedding-3-small"


def create_query_embedding(query: str):
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )

    return response.data[0].embedding


def search_knowledge_base(
    query: str,
    top_k: int = 3
):
    query_embedding = create_query_embedding(query)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    matches = []

    for match in results.matches:
        matches.append({
            "score": match.score,
            "source": match.metadata.get("source"),
            "text": match.metadata.get("text")
        })

    return matches

if __name__ == "__main__":

    query = input("Ask a knowledge question: ")

    results = search_knowledge_base(query)

    for result in results:
        print("\n---")
        print("Score:", result["score"])
        print("Source:", result["source"])
        print("Text:")
        print(result["text"])