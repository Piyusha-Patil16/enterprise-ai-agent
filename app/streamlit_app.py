import streamlit as st

from llm import generate_answer, generate_structured_answer
from exporters import (
    export_to_excel,
    export_to_xml,
    export_to_email_draft,
)


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="KOHLER Enterprise AI Copilot",
    page_icon="🤖",
    layout="wide",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🤖 KOHLER Enterprise AI Copilot")

st.caption(
    "Role-aware enterprise AI assistant for grounded, secure, "
    "structured responses."
)

st.divider()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Access")

    role = st.selectbox(
        "Select your role",
        ["Employee", "Customer"],
    )

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

    if role == "Employee":
        st.success("Employee access enabled")
    else:
        st.info("Customer access enabled")

    st.divider()

    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.caption(
        "Prototype for the KOHLER-MITWPU AI Research Lab Challenge"
    )

    st.caption(
        "Synthetic demonstration data only."
    )


# ---------------------------------------------------------
# Main interface
# ---------------------------------------------------------

st.subheader(f"Welcome, {role}")

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


# ---------------------------------------------------------
# Display previous conversation
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("type") == "download":

            st.write(message["content"])

        else:

            st.write(message["content"])


# ---------------------------------------------------------
# User input
# ---------------------------------------------------------

question = st.chat_input(
    "Ask the KOHLER Enterprise AI Copilot something..."
)


if question:

    # ---------------------------------------------
    # Save and display user message
    # ---------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "type": "text",
        }
    )

    with st.chat_message("user"):
        st.write(question)

    # ---------------------------------------------
    # Previous conversation
    # ---------------------------------------------

    previous_messages = (
        st.session_state.messages[:-1]
    )

    # ---------------------------------------------
    # Generate response
    # ---------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching authorized knowledge..."
        ):

            try:

                # =====================================================
                # NATURAL LANGUAGE
                # =====================================================

                if output_format == "Natural Language":

                    answer = generate_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    st.write(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "type": "text",
                        }
                    )


                # =====================================================
                # JSON
                # =====================================================

                elif output_format == "JSON":

                    structured_answer = generate_structured_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    json_output = structured_answer.model_dump_json(
                        indent=2
                    )

                    st.code(
                        json_output,
                        language="json",
                    )

                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_output,
                        file_name="enterprise_answer.json",
                        mime="application/json",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": json_output,
                            "type": "text",
                        }
                    )


                # =====================================================
                # EXCEL
                # =====================================================

                elif output_format == "Excel":

                    structured_answer = generate_structured_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    output_path = export_to_excel(
                        structured_answer,
                        filename="enterprise_answer.xlsx",
                    )

                    st.success(
                        "Excel summary generated successfully."
                    )

                    st.download_button(
                        label="⬇️ Download Excel",
                        data=output_path.read_bytes(),
                        file_name="enterprise_answer.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.spreadsheetml.sheet"
                        ),
                    )

                    # Show a preview as well.
                    st.write("### Excel Summary")

                    st.write(
                        {
                            "Answer": structured_answer.answer,
                            "Source": structured_answer.source,
                            "Document ID": structured_answer.document_id,
                            "Section": structured_answer.section,
                        }
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


                # =====================================================
                # XML
                # =====================================================

                elif output_format == "XML":

                    structured_answer = generate_structured_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    output_path = export_to_xml(
                        structured_answer,
                        filename="enterprise_answer.xml",
                    )

                    xml_output = output_path.read_text(
                        encoding="utf-8"
                    )

                    st.code(
                        xml_output,
                        language="xml",
                    )

                    st.download_button(
                        label="⬇️ Download XML",
                        data=output_path.read_bytes(),
                        file_name="enterprise_answer.xml",
                        mime="application/xml",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": xml_output,
                            "type": "text",
                        }
                    )


                # =====================================================
                # EMAIL DRAFT
                # =====================================================

                elif output_format == "Email Draft":

                    structured_answer = generate_structured_answer(
                        question,
                        role=role.lower(),
                        conversation_history=previous_messages,
                    )

                    output_path = export_to_email_draft(
                        structured_answer,
                        filename="email_draft.txt",
                    )

                    email_output = output_path.read_text(
                        encoding="utf-8"
                    )

                    st.success(
                        "Ready-to-send email draft generated."
                    )

                    st.code(
                        email_output,
                        language="text",
                    )

                    st.download_button(
                        label="⬇️ Download Email Draft",
                        data=output_path.read_bytes(),
                        file_name="email_draft.txt",
                        mime="text/plain",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": email_output,
                            "type": "text",
                        }
                    )


            except Exception as error:

                error_message = (
                    "Something went wrong while processing "
                    "your request."
                )

                st.error(error_message)

                st.exception(error)