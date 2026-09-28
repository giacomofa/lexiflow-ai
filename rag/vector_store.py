from pathlib import Path
import re


CHROMA_PATH = Path(__file__).resolve().parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "lexiflow_documents"


def get_client():
    import chromadb

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


_SECTION_HEADER_RE = re.compile(r"^[A-ZÀ-Ú0-9º°\s]{3,60}:$")


def _is_section_header(line: str) -> bool:
    return bool(_SECTION_HEADER_RE.match(line.strip()))


def group_by_section(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    blocks: list[str] = []
    current_block: list[str] = []

    for line in lines:
        if _is_section_header(line) and current_block:
            blocks.append(" ".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        blocks.append(" ".join(current_block))

    return blocks


def chunk_document(text: str, max_chars: int = 700) -> list[str]:
    blocks = group_by_section(text)

    chunks: list[str] = []
    for block in blocks:
        chunks.extend(split_large_paragraph(block, max_chars=max_chars))

    return chunks


def index_document(document_id: int, file_name: str, document_text: str) -> int:
    collection = get_collection()
    chunks = chunk_document(document_text)

    # Limpa qualquer chunk já indexado para este documento antes de inserir
    # os novos. Sem isso, reprocessar/reindexar um documento cujo novo
    # chunking gera MENOS pedaços que uma indexação anterior só sobrescreve
    # os ids 0..len(chunks)-1 — os ids extras da vez anterior (ex.: chunk_9,
    # chunk_10 de uma indexação com 11 pedaços, se a nova gerar só 7) ficam
    # órfãos na coleção, com texto desatualizado, ainda retornados pelas
    # buscas semânticas para esse document_id.
    collection.delete(where={"document_id": document_id})

    if not chunks:
        return 0

    ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "file_name": file_name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def delete_document_chunks(document_id: int) -> None:
    """Remove do Chroma todos os chunks de um documento excluído — sem isso,
    o texto (com eventuais dados pessoais) continuaria pesquisável mesmo
    depois de o registro principal ser apagado do SQLite."""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})


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
        output.append({
            "text": doc,
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "distance": distances[i] if i < len(distances) else None,
        })

    return output
