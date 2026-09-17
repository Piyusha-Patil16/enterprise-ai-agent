from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"


# --------------------------------------------------
# 2. Find documents
# --------------------------------------------------

DOCUMENTS = []

for access_level in ["employee", "customer", "public"]:
    folder = DATA_PATH / access_level

    if folder.exists():
        for document_path in folder.glob("*.md"):
            DOCUMENTS.append(
                {
                    "path": document_path,
                    "access_level": access_level,
                }
            )


print(f"Found {len(DOCUMENTS)} documents")

for document in DOCUMENTS:
    print(
        f"  - {document['path'].name} "
        f"({document['access_level']})"
    )


# --------------------------------------------------
# 3. Section-aware chunking
# --------------------------------------------------

def create_section_chunks(text):
    """
    Split a Markdown document using ## headings.

    Each policy/support section becomes its own
    retrieval chunk.
    """

    lines = text.splitlines()

    chunks = []
    current_section = []
    current_title = "Document Introduction"

    for line in lines:

        if line.startswith("## "):

            # Save previous section
            if current_section:

                chunk_text = "\n".join(
                    current_section
                ).strip()

                if chunk_text:

                    chunks.append(
                        {
                            "title": current_title,
                            "text": chunk_text,
                        }
                    )

            # Start new section
            current_title = line.replace(
                "## ", ""
            ).strip()

            current_section = [line]

        else:
            current_section.append(line)

    # Save final section
    if current_section:

        chunk_text = "\n".join(
            current_section
        ).strip()

        if chunk_text:

            chunks.append(
                {
                    "title": current_title,
                    "text": chunk_text,
                }
            )

    return chunks


# --------------------------------------------------
# 4. Load all documents and create chunks
# --------------------------------------------------

all_chunks = []

for document in DOCUMENTS:

    document_path = document["path"]
    access_level = document["access_level"]

    print()
    print(f"Loading document: {document_path.name}")

    text = document_path.read_text(
        encoding="utf-8"
    )

    chunks = create_section_chunks(text)

    print(
        f"Created {len(chunks)} section chunks"
    )

    for chunk in chunks:

        all_chunks.append(
            {
                "text": chunk["text"],
                "title": chunk["title"],
                "source": document_path.name,
                "access_level": access_level,
            }
        )


print()
print(
    f"Total chunks created: {len(all_chunks)}"
)


# --------------------------------------------------
# 5. Load embedding model
# --------------------------------------------------

print()
print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model ready")


# --------------------------------------------------
# 6. Create embeddings
# --------------------------------------------------

print("Creating embeddings...")

chunk_texts = [
    chunk["text"]
    for chunk in all_chunks
]

embeddings = model.encode(
    chunk_texts
).tolist()

print("Embeddings created")


# --------------------------------------------------
# 7. Connect to ChromaDB
# --------------------------------------------------

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


# --------------------------------------------------
# 8. Rebuild collection
# --------------------------------------------------

try:

    client.delete_collection(
        name="enterprise_kb"
    )

    print("Old collection deleted")

except Exception:

    print(
        "No existing collection to delete"
    )


collection = client.get_or_create_collection(
    name="enterprise_kb"
)


# --------------------------------------------------
# 9. Prepare metadata
# --------------------------------------------------

ids = []

metadatas = []

for i, chunk in enumerate(all_chunks):

    ids.append(
        f"document_section_{i}"
    )

    metadatas.append(
        {
            "domain": "enterprise",
            "access_level": chunk[
                "access_level"
            ],
            "source": chunk["source"],
            "document_id": Path(
                chunk["source"]
            ).stem,
            "section": chunk["title"],
            "synthetic": "true",
        }
    )


# --------------------------------------------------
# 10. Store chunks
# --------------------------------------------------

collection.add(
    ids=ids,
    documents=chunk_texts,
    embeddings=embeddings,
    metadatas=metadatas,
)


# --------------------------------------------------
# 11. Finished
# --------------------------------------------------

print()
print("========================================")
print("RAG ingestion completed successfully!")
print("========================================")
print(
    f"Documents stored: {len(DOCUMENTS)}"
)
print(
    f"Sections stored: {len(all_chunks)}"
)
print(f"Database: {CHROMA_PATH}")
print("Collection: enterprise_kb")