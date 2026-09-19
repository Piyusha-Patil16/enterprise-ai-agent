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
    "does",
    "do",
    "about",

    # Generic enterprise words
    "policy",
    "policies",
    "information",
    "company",
    "customer",
    "employee",
    "employees",
    "data",
}


def extract_keywords(text):
    """
    Extract meaningful whole words from a question.
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
# 5. Access control
# --------------------------------------------------

def get_allowed_access_levels(role):
    """
    Return the knowledge-base access levels available
    to the specified user role.

    Employee:
        - employee
        - public

    Customer:
        - customer
        - public

    Unknown roles:
        - no access
    """

    role = role.lower().strip()

    if role == "employee":
        return ["employee", "public"]

    if role == "customer":
        return ["customer", "public"]

    return []


# --------------------------------------------------
# 6. Hybrid retrieval
# --------------------------------------------------

def search_knowledge_base(
    question,
    role="employee",
    top_k=3
):
    """
    Hybrid retrieval:

    1. Chroma semantic similarity
    2. Whole-word keyword overlap
    3. Combined ranking
    4. Role-based access control
    5. Relevance safeguard

    Access control is applied during retrieval.
    """

    # ----------------------------------------------
    # Determine authorized document classes
    # ----------------------------------------------

    allowed_access_levels = get_allowed_access_levels(
        role
    )

    if not allowed_access_levels:
        return []


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
            "access_level": {
                "$in": allowed_access_levels
            }
        },
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )


    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]


    # ----------------------------------------------
    # Keyword scoring
    # ----------------------------------------------

    question_keywords = extract_keywords(
        question
    )

    ranked_results = []


    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        section_title = metadata.get(
            "section",
            ""
        )

        document_text = (
            section_title + " " + document
        ).lower()


        # ------------------------------------------
        # Whole-word keyword matching
        # ------------------------------------------

        document_words = set(
            re.findall(
                r"\b[a-zA-Z0-9]+\b",
                document_text
            )
        )


        keyword_matches = sum(
            1
            for keyword in question_keywords
            if keyword in document_words
        )


        keyword_score = (
            keyword_matches / len(question_keywords)
            if question_keywords
            else 0
        )


        # ------------------------------------------
        # Semantic similarity
        # ------------------------------------------

        semantic_score = 1 / (1 + distance)


        # ------------------------------------------
        # Hybrid score
        # ------------------------------------------

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


    ranked_results = ranked_results[:top_k]


    # ----------------------------------------------
    # Relevance safeguard
    # ----------------------------------------------
    #
    # A document should not be considered useful
    # merely because semantic search found it nearby.
    #
    # If semantic similarity is only moderate AND
    # there is almost no keyword overlap, reject it.
    #
    # This prevents situations such as:
    #
    # Customer asks:
    # "What is the annual leave policy?"
    #
    # Retrieval finds:
    # "privacy_policy.md"
    #
    # even though the privacy document is unrelated.
    # ----------------------------------------------

    filtered_results = []

    for result in ranked_results:

        semantic_score = result["semantic_score"]
        keyword_score = result["keyword_score"]

        if (
            semantic_score < 0.50
            and keyword_score < 0.20
        ):
            continue

        filtered_results.append(
            result
        )


    return filtered_results


# --------------------------------------------------
# 7. Test retrieval
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "international standard hotel limit"
    )

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


    for i, result in enumerate(
        results
    ):

        print()
        print(
            f"Result {i + 1}"
        )

        print(
            "-" * 60
        )

        print(
            result["document"][:500]
        )

        print()
        print("Source:")

        print(
            result["metadata"].get(
                "source",
                "Unknown"
            )
        )

        print()
        print("Access level:")

        print(
            result["metadata"].get(
                "access_level",
                "Unknown"
            )
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