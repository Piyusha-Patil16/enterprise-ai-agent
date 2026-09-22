import hashlib

import streamlit as st

from llm import (
    generate_answer,
    generate_structured_answer,
    detect_prompt_injection,
)

from retrieve import search_knowledge_base

from exporters import (
    export_to_excel,
    export_to_xml,
    export_to_email_draft,
)

from audit import log_interaction


# =========================================================
# Human escalation
# =========================================================

def render_human_escalation(role, question, answer):
    """
    Role-aware human assistance workflow.

    Customer -> Customer Support
    Employee -> HR

    This prepares a request for human review.
    It does not send an email or create a real ticket.
    """

    role = role.lower().strip()

    if role == "customer":
        contact_team = "Customer Support"
        action_label = "Need more help? Contact Customer Support"
        intro = (
            "Prepare a support request with the current question "
            "and AI response for human review."
        )
        file_name = "customer_support_request.txt"

    else:
        contact_team = "HR"
        action_label = "Need more help? Contact HR"
        intro = (
            "Prepare an HR assistance request with the current "
            "question and AI response for human review."
        )
        file_name = "hr_assistance_request.txt"

    st.divider()

    with st.expander(action_label):

        st.caption(intro)

        subject = st.text_input(
            "Subject",
            value=f"Assistance request - {contact_team}",
            key=f"escalation_subject_{role}",
        )

        request = f"""Subject: {subject}

Hello {contact_team},

I need assistance with the following question:

Question:
{question}

AI response:
{answer}

Additional context:
Please review this request and provide guidance where the AI response is insufficient or requires human clarification.

Thank you.
"""

        edited_request = st.text_area(
            "Request",
            value=request,
            height=280,
            key=f"escalation_request_{role}",
        )

        st.caption(
            "This prepares a request for human review. "
            "It does not send a message or create a real ticket."
        )

        if st.download_button(
            label="Download Request",
            data=edited_request,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True,
        ):
            log_interaction(
                role=role,
                question=question,
                output_format=f"Human Escalation - {contact_team}",
                source="Human Support",
                document_id="N/A",
                section="Escalation",
                confidence=0.0,
                access_level=role,
                result_type="human_escalation",
            )


# =========================================================
# Evidence inspection
# =========================================================

def show_retrieved_evidence(question, role):
    """
    Show the authorized evidence retrieved for the current query.

    This is optional because it causes an additional local
    retrieval operation after the main answer generation.
    """

    results = search_knowledge_base(
        question,
        role=role.lower(),
        top_k=3,
    )

    with st.expander("Why this answer?"):

        if not results:
            st.warning(
                "No sufficiently relevant authorized evidence "
                "was retrieved for this query."
            )
            return False

        st.caption(
            "Authorized evidence retrieved for this query."
        )

        for index, result in enumerate(results, start=1):

            metadata = result["metadata"]

            st.markdown(
                f"**Evidence {index}**  \n"
                f"Source: `{metadata.get('source', 'N/A')}`  \n"
                f"Document ID: `{metadata.get('document_id', 'N/A')}`  \n"
                f"Section: `{metadata.get('section', 'N/A')}`  \n"
                f"Access: `{metadata.get('access_level', 'N/A')}`"
            )

            st.write(
                result["document"]
            )

            if index < len(results):
                st.divider()

        return True


# =========================================================
# Feedback
# =========================================================

def show_answer_feedback(role, question):
    """
    Collect simple user feedback and write it to the audit log.
    """

    feedback_id = hashlib.md5(
        question.encode("utf-8")
    ).hexdigest()[:10]

    st.divider()

    st.caption("Was this answer helpful?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Yes",
            key=f"feedback_yes_{feedback_id}",
            use_container_width=True,
        ):
            log_interaction(
                role=role.lower(),
                question=question,
                output_format="Feedback",
                source="User Feedback",
                document_id="N/A",
                section="Feedback",
                confidence=0.0,
                access_level=role.lower(),
                result_type="feedback_positive",
            )

            st.success(
                "Thank you for your feedback."
            )

    with col2:

        if st.button(
            "No",
            key=f"feedback_no_{feedback_id}",
            use_container_width=True,
        ):
            log_interaction(
                role=role.lower(),
                question=question,
                output_format="Feedback",
                source="User Feedback",
                document_id="N/A",
                section="Feedback",
                confidence=0.0,
                access_level=role.lower(),
                result_type="feedback_negative",
            )

            st.warning(
                "Human assistance may be helpful for this request."
            )


# =========================================================
# Page configuration
# =========================================================

st.set_page_config(
    page_title="KOHLER Enterprise AI Copilot",
    page_icon="AI",
    layout="wide",
)


# =========================================================
# Session state
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# Header
# =========================================================

st.title(
    "KOHLER Enterprise AI Copilot"
)

st.caption(
    "Role-aware enterprise AI assistant for grounded, secure, "
    "structured responses."
)

st.divider()


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.header("Access")

    role = st.selectbox(
        "Select your role",
        ["Employee", "Customer"],
    )

    # Reset conversation when user switches roles.
    if "active_role" not in st.session_state:

        st.session_state.active_role = role

    elif st.session_state.active_role != role:

        st.session_state.messages = []
        st.session_state.active_role = role

        st.rerun()

    st.divider()

    st.header("Output Format")

    output_format = st.selectbox(
        "How would you like the answer?",
        [
            "Natural Language",
            "JSON",
            "Excel",
            "XML",
            "Email Draft",
        ],
    )

    st.divider()

    # Optional evidence mode.
    # OFF by default for faster demo responses.
    st.header("Transparency")

    show_evidence = st.checkbox(
        "Show retrieved evidence",
        value=False,
        help=(
            "Displays the document sections retrieved for "
            "the current query. This performs an additional "
            "local retrieval operation."
        ),
    )

    st.divider()

    st.header("Security")

    st.success("RBAC active")
    st.success("Prompt-injection protection active")
    st.success("Grounded retrieval active")
    st.success("Session isolation active")

    st.divider()

    if role == "Employee":

        st.success(
            "Employee access enabled"
        )

    else:

        st.info(
            "Customer access enabled"
        )

    st.divider()

    if st.button("Clear Conversation"):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.caption(
        "Prototype for the KOHLER-MITWPU AI Research Lab Challenge"
    )

    st.caption(
        "Synthetic demonstration data only."
    )


# =========================================================
# Main interface
# =========================================================

st.subheader(
    f"Welcome, {role}"
)

if role == "Employee":

    st.info(
        "Employee access: authorized internal enterprise "
        "information may be available."
    )

else:

    st.info(
        "Customer access: only customer-accessible "
        "information is available."
    )


# =========================================================
# Display previous conversation
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        if message.get("type") == "download":

            st.write(
                message["content"]
            )

        else:

            st.write(
                message["content"]
            )


# =========================================================
# User input
# =========================================================

question = st.chat_input(
    "Ask the KOHLER Enterprise AI Copilot something..."
)


# =========================================================
# Provenance helper
# =========================================================

def show_provenance(structured_answer):

    st.divider()

    st.caption(
        "Answer Provenance"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write("**Source**")

        st.write(
            structured_answer.source
        )

    with col2:

        st.write("**Document ID**")

        st.write(
            structured_answer.document_id
        )

    with col3:

        st.write("**Section**")

        st.write(
            structured_answer.section
        )

    col4, col5 = st.columns(2)

    with col4:

        st.write("**Confidence**")

        st.progress(
            min(
                max(
                    structured_answer.confidence,
                    0.0,
                ),
                1.0,
            )
        )

        st.caption(
            f"{structured_answer.confidence:.3f}"
        )

    with col5:

        st.write("**Access Level**")

        st.write(
            structured_answer.access_level
        )


# =========================================================
# Generate response
# =========================================================

if question:

    # -----------------------------------------------------
    # Save and display user message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "type": "text",
        }
    )

    with st.chat_message("user"):

        st.write(
            question
        )

    # -----------------------------------------------------
    # Previous conversation
    # -----------------------------------------------------

    previous_messages = (
        st.session_state.messages[:-1]
    )

    # -----------------------------------------------------
    # Tracking variables
    # -----------------------------------------------------

    escalation_answer = None

    # Only calculated when evidence mode is enabled.
    evidence_found = True

    # -----------------------------------------------------
    # Generate response
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching authorized knowledge..."
        ):

            try:

                # =================================================
                # NATURAL LANGUAGE
                # =================================================

                if output_format == "Natural Language":

                    answer = generate_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    st.write(
                        answer
                    )

                    escalation_answer = answer

                    if show_evidence:

                        evidence_found = (
                            show_retrieved_evidence(
                                question,
                                role,
                            )
                        )

                    show_answer_feedback(
                        role,
                        question,
                    )

                    log_interaction(
                        role=role.lower(),
                        question=question,
                        output_format="Natural Language",
                        source="Generated response",
                        document_id="N/A",
                        section="N/A",
                        confidence=0.0,
                        access_level=role.lower(),
                        result_type="answer",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "type": "text",
                        }
                    )

                # =================================================
                # JSON
                # =================================================

                elif output_format == "JSON":

                    structured_answer = (
                        generate_structured_answer(
                            question,
                            role=role.lower(),
                            conversation_history=previous_messages,
                        )
                    )

                    json_output = (
                        structured_answer.model_dump_json(
                            indent=2
                        )
                    )

                    st.code(
                        json_output,
                        language="json",
                    )

                    show_provenance(
                        structured_answer
                    )

                    escalation_answer = (
                        structured_answer.answer
                    )

                    if show_evidence:

                        evidence_found = (
                            show_retrieved_evidence(
                                question,
                                role,
                            )
                        )

                    show_answer_feedback(
                        role,
                        question,
                    )

                    st.download_button(
                        label="Download JSON",
                        data=json_output,
                        file_name="enterprise_answer.json",
                        mime="application/json",
                    )

                    log_interaction(
                        role=role.lower(),
                        question=question,
                        output_format="JSON",
                        source=structured_answer.source,
                        document_id=structured_answer.document_id,
                        section=structured_answer.section,
                        confidence=structured_answer.confidence,
                        access_level=structured_answer.access_level,
                        result_type="structured_answer",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": json_output,
                            "type": "text",
                        }
                    )

                # =================================================
                # EXCEL
                # =================================================

                elif output_format == "Excel":

                    structured_answer = (
                        generate_structured_answer(
                            question,
                            role=role.lower(),
                            conversation_history=previous_messages,
                        )
                    )

                    output_path = export_to_excel(
                        structured_answer,
                        filename="enterprise_answer.xlsx",
                    )

                    st.success(
                        "Excel summary generated successfully."
                    )

                    show_provenance(
                        structured_answer
                    )

                    escalation_answer = (
                        structured_answer.answer
                    )

                    if show_evidence:

                        evidence_found = (
                            show_retrieved_evidence(
                                question,
                                role,
                            )
                        )

                    show_answer_feedback(
                        role,
                        question,
                    )

                    st.download_button(
                        label="Download Excel",
                        data=output_path.read_bytes(),
                        file_name="enterprise_answer.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.spreadsheetml.sheet"
                        ),
                    )

                    st.write(
                        "### Excel Summary"
                    )

                    st.write(
                        {
                            "Answer": structured_answer.answer,
                            "Source": structured_answer.source,
                            "Document ID": structured_answer.document_id,
                            "Section": structured_answer.section,
                            "Confidence": structured_answer.confidence,
                            "Access Level": structured_answer.access_level,
                        }
                    )

                    log_interaction(
                        role=role.lower(),
                        question=question,
                        output_format="Excel",
                        source=structured_answer.source,
                        document_id=structured_answer.document_id,
                        section=structured_answer.section,
                        confidence=structured_answer.confidence,
                        access_level=structured_answer.access_level,
                        result_type="exported_answer",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                "Excel summary generated for: "
                                f"{question}"
                            ),
                            "type": "download",
                        }
                    )

                # =================================================
                # XML
                # =================================================

                elif output_format == "XML":

                    structured_answer = (
                        generate_structured_answer(
                            question,
                            role=role.lower(),
                            conversation_history=previous_messages,
                        )
                    )

                    output_path = export_to_xml(
                        structured_answer,
                        filename="enterprise_answer.xml",
                    )

                    xml_output = (
                        output_path.read_text(
                            encoding="utf-8"
                        )
                    )

                    st.code(
                        xml_output,
                        language="xml",
                    )

                    show_provenance(
                        structured_answer
                    )

                    escalation_answer = (
                        structured_answer.answer
                    )

                    if show_evidence:

                        evidence_found = (
                            show_retrieved_evidence(
                                question,
                                role,
                            )
                        )

                    show_answer_feedback(
                        role,
                        question,
                    )

                    st.download_button(
                        label="Download XML",
                        data=output_path.read_bytes(),
                        file_name="enterprise_answer.xml",
                        mime="application/xml",
                    )

                    log_interaction(
                        role=role.lower(),
                        question=question,
                        output_format="XML",
                        source=structured_answer.source,
                        document_id=structured_answer.document_id,
                        section=structured_answer.section,
                        confidence=structured_answer.confidence,
                        access_level=structured_answer.access_level,
                        result_type="exported_answer",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": xml_output,
                            "type": "text",
                        }
                    )

                # =================================================
                # EMAIL DRAFT
                # =================================================

                elif output_format == "Email Draft":

                    structured_answer = (
                        generate_structured_answer(
                            question,
                            role=role.lower(),
                            conversation_history=previous_messages,
                        )
                    )

                    output_path = (
                        export_to_email_draft(
                            structured_answer,
                            filename="email_draft.txt",
                        )
                    )

                    email_output = (
                        output_path.read_text(
                            encoding="utf-8"
                        )
                    )

                    st.success(
                        "Ready-to-edit email draft generated."
                    )

                    st.code(
                        email_output,
                        language="text",
                    )

                    show_provenance(
                        structured_answer
                    )

                    escalation_answer = (
                        structured_answer.answer
                    )

                    if show_evidence:

                        evidence_found = (
                            show_retrieved_evidence(
                                question,
                                role,
                            )
                        )

                    show_answer_feedback(
                        role,
                        question,
                    )

                    st.download_button(
                        label="Download Email Draft",
                        data=email_output,
                        file_name="email_draft.txt",
                        mime="text/plain",
                    )

                    log_interaction(
                        role=role.lower(),
                        question=question,
                        output_format="Email Draft",
                        source=structured_answer.source,
                        document_id=structured_answer.document_id,
                        section=structured_answer.section,
                        confidence=structured_answer.confidence,
                        access_level=structured_answer.access_level,
                        result_type="exported_answer",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": email_output,
                            "type": "text",
                        }
                    )

            except Exception as error:

                escalation_answer = None
                evidence_found = False

                st.error(
                    "Something went wrong while processing "
                    "your request."
                )

                st.exception(
                    error
                )

    # -----------------------------------------------------
    # Human escalation
    # -----------------------------------------------------

    if (
        escalation_answer
        and not detect_prompt_injection(question)
    ):

        if not evidence_found:

            st.warning(
                "The assistant could not find sufficiently "
                "relevant authorized evidence. Human assistance "
                "may be appropriate."
            )

        render_human_escalation(
            role=role,
            question=question,
            answer=escalation_answer,
        )