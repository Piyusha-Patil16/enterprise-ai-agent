from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = PROJECT_ROOT / "data" / "employee" / "finance_guidelines.md"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"


# --------------------------------------------------
# 2. Load document
# --------------------------------------------------

print("Loading document...")

text = DOCUMENT_PATH.read_text(encoding="utf-8")

print(f"Document loaded: {DOCUMENT_PATH.name}")


# --------------------------------------------------
# 3. Create section-aware chunks
# --------------------------------------------------

def create_section_chunks(text):
    """
    Split the document using Markdown ## headings.

    Each policy section becomes its own retrieval chunk.
    """

    lines = text.splitlines()

    chunks = []
    current_section = []
    current_title = "Document Introduction"

    for line in lines:

        # Detect headings such as:
        # ## 1. Business Travel Eligibility
        # ## 2. Accommodation & Hotel Limits

        if line.startswith("## "):

            # Save the previous section
            if current_section:
                chunk_text = "\n".join(current_section).strip()

                if chunk_text:
                    chunks.append(
                        {
                            "title": current_title,
                            "text": chunk_text,
                        }
                    )

            # Start a new section
            current_title = line.replace("## ", "").strip()
            current_section = [line]

        else:
            current_section.append(line)

    # Save the final section
    if current_section:
        chunk_text = "\n".join(current_section).strip()

        if chunk_text:
            chunks.append(
                {
                    "title": current_title,
                    "text": chunk_text,
                }
            )

    return chunks


chunks = create_section_chunks(text)

print(f"Created {len(chunks)} section chunks")

for i, chunk in enumerate(chunks):
    print(f"  {i + 1}. {chunk['title']}")


# --------------------------------------------------
# 4. Load embedding model
# --------------------------------------------------

print()
print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model ready")


# --------------------------------------------------
# 5. Create embeddings
# --------------------------------------------------

print("Creating embeddings...")

chunk_texts = [
    chunk["text"]
    for chunk in chunks
]

embeddings = model.encode(
    chunk_texts
).tolist()

print("Embeddings created")


# --------------------------------------------------
# 6. Connect to ChromaDB
# --------------------------------------------------

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


# --------------------------------------------------
# 7. Rebuild the collection
# --------------------------------------------------

# We delete the old collection because its chunks
# were created using the previous chunking strategy.

try:
    client.delete_collection(
        name="enterprise_kb"
    )
    print("Old collection deleted")
except Exception:
    print("No existing collection to delete")


collection = client.get_or_create_collection(
    name="enterprise_kb"
)


# --------------------------------------------------
# 8. Prepare metadata
# --------------------------------------------------

ids = [
    f"finance_policy_section_{i}"
    for i in range(len(chunks))
]

metadatas = [
    {
        "domain": "finance",
        "access_level": "employee",
        "source": "finance_guidelines.md",
        "document_id": "POL-FIN-2026-042",
        "section": chunk["title"],
        "synthetic": "true",
    }
    for chunk in chunks
]


# --------------------------------------------------
# 9. Store chunks
# --------------------------------------------------

collection.add(
    ids=ids,
    documents=chunk_texts,
    embeddings=embeddings,
    metadatas=metadatas,
)


# --------------------------------------------------
# 10. Finished
# --------------------------------------------------

print()
print("========================================")
print("RAG ingestion completed successfully!")
print("========================================")
print(f"Sections stored: {len(chunks)}")
print(f"Database: {CHROMA_PATH}")
print("Collection: enterprise_kb")