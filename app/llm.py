
from google import genai
from pydantic import BaseModel

try:
    from retrieve import search_knowledge_base
except ModuleNotFoundError:
    from app.retrieve import search_knowledge_base


# --------------------------------------------------
# 1. Gemini client
# --------------------------------------------------

client = genai.Client()


# --------------------------------------------------
# 2. Structured answer schema
# --------------------------------------------------

class StructuredAnswer(BaseModel):
    answer: str
    source: str
    document_id: str
    section: str


# --------------------------------------------------
# 3. Check whether the question is ambiguous
# --------------------------------------------------

def is_ambiguous(question):
    """
    Determine whether the user's question is too vague
    to answer reliably from the enterprise knowledge base.
    """

    prompt = f"""
Determine whether this user question is ambiguous or too vague
to answer reliably.

Return ONLY one word:
YES
or
NO

Examples:

Question: "What's the limit?"
Answer: YES

Question: "What is the hotel limit for an international standard region?"
Answer: NO

Question: "How long do I have to submit receipts?"
Answer: NO

Question: "What is the policy?"
Answer: YES

User question:
{question}
"""

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low"
        }
    )

    result = response.output_text.strip().upper()

    return result.startswith("YES")


# --------------------------------------------------
# 4. Generate structured JSON answer
# --------------------------------------------------

def generate_structured_answer(question, role="employee"):
    """
    Generate a validated structured answer using only
    authorized knowledge-base evidence.
    """

    # Retrieve only documents authorized for this role
    results = search_knowledge_base(
        question,
        role=role,
        top_k=3
    )

    # No authorized evidence
    if not results:
        return None

    # Check relevance
    best_score = results[0]["final_score"]

    if best_score < 0.55:
        return None

    # Use the strongest retrieved result
    best = results[0]

    metadata = best["metadata"]

    prompt = f"""
You are the KOHLER Enterprise AI Copilot.

Answer the user's question using ONLY the authorized evidence.

Return ONLY valid JSON with exactly these fields:

{{
  "answer": "concise answer",
  "source": "source filename",
  "document_id": "document ID",
  "section": "section name"
}}

Rules:

1. Do not add Markdown.
2. Do not add explanations outside the JSON.
3. Do not invent information.
4. Use only the authorized evidence.
5. Keep the answer concise.

AUTHORIZED EVIDENCE:
{best["document"]}

SOURCE:
{metadata.get("source", "Unknown")}

DOCUMENT ID:
{metadata.get("document_id", "Unknown")}

SECTION:
{metadata.get("section", "Unknown")}

USER QUESTION:
{question}
"""

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low"
        }
    )

    # Validate Gemini's JSON against our Pydantic schema
    structured = StructuredAnswer.model_validate_json(
        response.output_text
    )

    return structured


# --------------------------------------------------
# 5. Generate grounded natural-language answer
# --------------------------------------------------

def generate_answer(question, role="employee"):
    """
    Retrieve authorized evidence and ask Gemini
    to answer only from that evidence.
    """

    # --------------------------------------------------
    # Check ambiguity first
    # --------------------------------------------------

    if is_ambiguous(question):

        return (
            "Could you clarify what you mean? "
            "For example, you can specify whether you "
            "mean a hotel limit, meal limit, transportation "
            "limit, or another expense category."
        )

    # --------------------------------------------------
    # Retrieve authorized information
    # --------------------------------------------------

    results = search_knowledge_base(
        question,
        role=role,
        top_k=3
    )

    # --------------------------------------------------
    # Check evidence relevance
    # --------------------------------------------------

    if not results:

        return (
            "I don't have enough information in the authorized "
            "knowledge base to answer that reliably."
        )

    best_score = results[0]["final_score"]

    if best_score < 0.55:

        return (
            "I don't have enough information in the authorized "
            "knowledge base to answer that reliably."
        )

    # --------------------------------------------------
    # Build evidence for Gemini
    # --------------------------------------------------

    evidence_parts = []

    for i, result in enumerate(results):

        metadata = result["metadata"]

        evidence_parts.append(
            f"""
SOURCE {i + 1}
Document: {metadata.get("source", "Unknown")}
Document ID: {metadata.get("document_id", "Unknown")}
Section: {metadata.get("section", "Unknown")}

Content:
{result["document"]}
"""
        )

    evidence = "\n".join(evidence_parts)

    # --------------------------------------------------
    # Grounding instructions
    # --------------------------------------------------

    prompt = f"""
You are the KOHLER Enterprise AI Copilot.

The user has the role: {role}

Answer the user's question using ONLY the authorized
evidence provided below.

Rules:

1. Do not invent facts.
2. Do not use outside knowledge.
3. If the evidence does not contain enough information,
   clearly say that you do not have enough information.
4. Cite the relevant source document and section.
5. Keep the answer concise and useful.
6. Never reveal information that is outside the
   authorized evidence.

AUTHORIZED EVIDENCE:
{evidence}

USER QUESTION:
{question}
"""

    # --------------------------------------------------
    # Call Gemini
    # --------------------------------------------------

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low"
        }
    )

    return response.output_text


# --------------------------------------------------
# 6. Test
# --------------------------------------------------

if __name__ == "__main__":

    question = "What is the hotel limit for an international standard region?"

    answer = generate_answer(
        question,
        role="employee"
    )

    print()
    print("USER QUESTION")
    print("=" * 60)
    print(question)

    print()
    print("GEMINI ANSWER")
    print("=" * 60)
    print(answer)
