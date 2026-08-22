import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from pathlib import Path
import re

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not configured")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not configured")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is not configured")

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

pinecone_client = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pinecone_client.Index(
    PINECONE_INDEX_NAME
)

KNOWLEDGE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge"
)


def load_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.md"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents



def chunk_text(text: str):
    text = text.strip()

    title_match = re.match(
        r"^# (.+?)(?:\n|$)",
        text
    )

    title = title_match.group(1) if title_match else ""

    sections = re.split(
        r"\n(?=## )",
        text
    )

    chunks = []

    for section in sections:
        section = section.strip()

        # Skip the standalone document title
        if not section or section.startswith("# ") and "\n## " not in section:
            continue

        if title:
            section = (
                f"Document: {title}\n\n"
                f"{section}"
            )

        chunks.append(section)

    return chunks

EMBEDDING_MODEL = "text-embedding-3-small"


def create_embedding(text):
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding

def ingest_documents():
    documents = load_documents()

    vectors = []

    for document in documents:

        chunks = chunk_text(document["text"])

        for index_number, chunk in enumerate(chunks):

            embedding = create_embedding(chunk)

            vector_id = (
                f"{document['source']}-{index_number}"
            )

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "source": document["source"],
                    "text": chunk
                }
            })
    index.delete(delete_all=True)

    index.upsert(vectors=vectors)

    return len(vectors)

if __name__ == "__main__":
    count = ingest_documents()

    print(
        f"Successfully indexed {count} chunks."
    )