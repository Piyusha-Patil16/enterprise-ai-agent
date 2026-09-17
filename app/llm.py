from google import genai

from retrieve import search_knowledge_base


# --------------------------------------------------
# 1. Gemini client
# --------------------------------------------------

client = genai.Client()


# --------------------------------------------------
# 2. Generate grounded answer
# --------------------------------------------------

def generate_answer(question, role="employee"):
    """
    Retrieve authorized evidence and ask Gemini
    to answer only from that evidence.
    """

    # Retrieve relevant information
    results = search_knowledge_base(
        question,
        role=role,
        top_k=3
    )

    # No evidence found
    if not results:
        return "I don't have enough information in the authorized knowledge base to answer that."


    # Build evidence for Gemini
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
# 3. Test
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