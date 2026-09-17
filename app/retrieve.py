from pathlib import Path
import re

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_PATH = PROJECT_ROOT / "chroma_db"


# --------------------------------------------------
# 2. Load embedding model
# --------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model ready")


# --------------------------------------------------
# 3. Connect to ChromaDB
# --------------------------------------------------

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_collection(
    name="enterprise_kb"
)


# --------------------------------------------------
# 4. Keyword extraction
# --------------------------------------------------

STOP_WORDS = {
    "what",
    "is",
    "the",
    "a",
    "an",
    "for",
    "to",
    "of",
    "and",
    "in",
    "on",
    "can",
    "i",
    "me",
    "my",
    "are",
    "how",
}


def extract_keywords(text):
    """
    Extract meaningful words from a question.
    """

    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower()
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    }


# --------------------------------------------------
# 5. Hybrid retrieval
# --------------------------------------------------

def search_knowledge_base(
    question,
    role="employee",
    top_k=3
):
    """
    Hybrid retrieval:

    1. Chroma semantic similarity
    2. Keyword overlap
    3. Combined ranking

    Access control is applied during retrieval.
    """

    # ----------------------------------------------
    # Create question embedding
    # ----------------------------------------------

    question_embedding = model.encode(
        [question]
    ).tolist()[0]


    # ----------------------------------------------
    # Semantic search
    # ----------------------------------------------

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=collection.count(),
        where={
            "access_level": role
        },
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )


    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]


    # ----------------------------------------------
    # Keyword scoring
    # ----------------------------------------------

    question_keywords = extract_keywords(question)

    ranked_results = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        section_title = metadata.get("section", "")

        document_text = (
            section_title + " " + document
        ).lower()

        keyword_matches = sum(
            1
            for keyword in question_keywords
            if keyword in document_text
        )

        keyword_score = (
            keyword_matches / len(question_keywords)
            if question_keywords
            else 0
        )


        # Convert distance into a similarity-like score.
        semantic_score = 1 / (1 + distance)


        # Hybrid score.
        final_score = (
            0.65 * semantic_score
            + 0.35 * keyword_score
        )


        ranked_results.append(
            {
                "document": document,
                "metadata": metadata,
                "distance": distance,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "final_score": final_score,
            }
        )


    # ----------------------------------------------
    # Sort by final score
    # ----------------------------------------------

    ranked_results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )


    return ranked_results[:top_k]


# --------------------------------------------------
# 6. Test retrieval
# --------------------------------------------------

if __name__ == "__main__":

    question = "international standard hotel limit"

    print()
    print("Question:")
    print(question)

    results = search_knowledge_base(
        question,
        role="employee",
        top_k=3
    )

    print()
    print("Hybrid retrieval results:")
    print("=" * 60)

    for i, result in enumerate(results):

        print()
        print(f"Result {i + 1}")
        print("-" * 60)

        print(
            result["document"][:500]
        )

        print()
        print("Section:")
        print(
            result["metadata"].get(
                "section",
                "Unknown"
            )
        )

        print()
        print(
            f"Semantic score: "
            f"{result['semantic_score']:.3f}"
        )

        print(
            f"Keyword score: "
            f"{result['keyword_score']:.3f}"
        )

        print(
            f"Final score: "
            f"{result['final_score']:.3f}"
        )