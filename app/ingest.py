from pathlib import Path
import re

import chromadb
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model ready.")


# ---------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_access_level(source_path):
    """
    Determine access level from the folder containing
    the source document.
    """

    source_path = Path(source_path)

    folder_name = source_path.parent.name.lower()

    if folder_name == "employee":
        return "employee"

    if folder_name == "customer":
        return "customer"

    if folder_name == "public":
        return "public"

    return "unknown"


def extract_document_id(text, source_path):
    """
    Extract the explicit Document ID from the Markdown
    document.

    Supports formats such as:

    Document ID: POL-FIN-2026-042
    **Document ID:** POL-FIN-2026-042

    If no explicit ID is found, fall back to the
    filename stem.
    """

    match = re.search(
        r"Document ID\s*[:*]+\s*([A-Za-z0-9_-]+)",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return Path(source_path).stem

def extract_sections(text):
    """
    Split Markdown content into sections using headings.

    Each section becomes a separate retrieval chunk.
    """

    lines = text.splitlines()

    sections = []

    current_title = "General"
    current_content = []

    for line in lines:

        stripped = line.strip()

        if stripped.startswith("#"):
            if current_content:
                content = "\n".join(
                    current_content
                ).strip()

                if content:
                    sections.append(
                        {
                            "section": current_title,
                            "content": content,
                        }
                    )

            current_title = stripped.lstrip("#").strip()
            current_content = []

        else:
            current_content.append(line)

    if current_content:

        content = "\n".join(
            current_content
        ).strip()

        if content:
            sections.append(
                {
                    "section": current_title,
                    "content": content,
                }
            )

    return sections


# ---------------------------------------------------------
# Build knowledge base
# ---------------------------------------------------------

def rebuild_knowledge_base():

    print("\nRebuilding enterprise knowledge base...\n")

    # Delete existing collection so the database is
    # rebuilt cleanly whenever the ingestion script runs.

    try:
        client.delete_collection(
            name="enterprise_kb"
        )
        print("Existing collection deleted.")

    except Exception:
        print("No existing collection found.")

    collection = client.get_or_create_collection(
        name="enterprise_kb"
    )

    documents = []
    metadatas = []
    ids = []

    chunk_number = 0

    source_files = sorted(
        DATA_PATH.rglob("*.md")
    )

    print(
        f"Found {len(source_files)} Markdown documents."
    )

    for source_path in source_files:

        print(
            f"\nProcessing: {source_path}"
        )

        text = source_path.read_text(
            encoding="utf-8"
        )

        access_level = get_access_level(
            source_path
        )

        document_id = extract_document_id(
            text,
            source_path
        )

        sections = extract_sections(
            text
        )

        print(
            f"  Document ID: {document_id}"
        )

        print(
            f"  Access level: {access_level}"
        )

        print(
            f"  Sections: {len(sections)}"
        )

        for section in sections:

            chunk_id = (
                f"chunk_{chunk_number}"
            )

            documents.append(
                section["content"]
            )

            metadatas.append(
                {
                    "access_level": access_level,
                    "domain": "enterprise",
                    "source": source_path.name,
                    "document_id": document_id,
                    "section": section["section"],
                    "synthetic": True,
                }
            )

            ids.append(chunk_id)

            chunk_number += 1

    if not documents:
        print(
            "\nNo documents were found."
        )
        return

    print(
        f"\nGenerating embeddings for "
        f"{len(documents)} chunks..."
    )

    embeddings = model.encode(
        documents,
        show_progress_bar=True,
    ).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(
        "\nKnowledge base rebuilt successfully."
    )

    print(
        f"Total chunks: {collection.count()}"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    rebuild_knowledge_base()