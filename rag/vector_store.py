from pathlib import Path
import re

import chromadb


CHROMA_PATH = Path(__file__).resolve().parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "lexiflow_documents"


def get_client():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def get_collection():
    client = get_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)


def split_large_paragraph(paragraph: str, max_chars: int = 700) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current += " " + sentence
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_document(text: str, max_chars: int = 700) -> list[str]:
    paragraphs = [
        " ".join(line.split())
        for line in text.splitlines()
        if line.strip()
    ]

    normalized_paragraphs = []
    for paragraph in paragraphs:
        normalized_paragraphs.extend(split_large_paragraph(paragraph, max_chars=max_chars))

    return normalized_paragraphs


def index_document(document_id: int, file_name: str, document_text: str) -> int:
    collection = get_collection()
    chunks = chunk_document(document_text)

    if not chunks:
        return 0

    ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "file_name": file_name,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )

    return len(chunks)


def query_document(document_id: int, question: str, n_results: int = 3) -> list[dict]:
    collection = get_collection()

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where={"document_id": document_id},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for i, doc in enumerate(documents):
        output.append(
            {
                "text": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            }
        )

    return output