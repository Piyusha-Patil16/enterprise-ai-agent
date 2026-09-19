from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

EXPORT_PATH = PROJECT_ROOT / "exports"

EXPORT_PATH.mkdir(
    exist_ok=True
)


# ---------------------------------------------------------
# Excel exporter
# ---------------------------------------------------------

def export_to_excel(
    structured_answer,
    filename="answer.xlsx",
):
    """
    Export a structured enterprise answer to Excel.
    """

    output_path = (
        EXPORT_PATH / filename
    )


    data = {
        "Field": [
            "Answer",
            "Source",
            "Document ID",
            "Section",
            "Confidence",
            "Access Level",
        ],

        "Value": [
            structured_answer.answer,
            structured_answer.source,
            structured_answer.document_id,
            structured_answer.section,
            structured_answer.confidence,
            structured_answer.access_level,
        ],
    }


    dataframe = pd.DataFrame(
        data
    )


    dataframe.to_excel(
        output_path,
        index=False,
    )


    return output_path


# ---------------------------------------------------------
# XML exporter
# ---------------------------------------------------------

def export_to_xml(
    structured_answer,
    filename="answer.xml",
):
    """
    Export a structured enterprise answer to XML.
    """

    output_path = (
        EXPORT_PATH / filename
    )


    root = ET.Element(
        "enterprise_answer"
    )


    answer_element = ET.SubElement(
        root,
        "answer",
    )

    answer_element.text = (
        structured_answer.answer
    )


    source_element = ET.SubElement(
        root,
        "source",
    )

    source_element.text = (
        structured_answer.source
    )


    document_id_element = ET.SubElement(
        root,
        "document_id",
    )

    document_id_element.text = (
        structured_answer.document_id
    )


    section_element = ET.SubElement(
        root,
        "section",
    )

    section_element.text = (
        structured_answer.section
    )


    confidence_element = ET.SubElement(
        root,
        "confidence",
    )

    confidence_element.text = str(
        structured_answer.confidence
    )


    access_level_element = ET.SubElement(
        root,
        "access_level",
    )

    access_level_element.text = (
        structured_answer.access_level
    )


    tree = ET.ElementTree(
        root
    )


    tree.write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )


    return output_path


# ---------------------------------------------------------
# Email draft exporter
# ---------------------------------------------------------

def export_to_email_draft(
    structured_answer,
    filename="email_draft.txt",
):
    """
    Export a ready-to-send email draft.
    """

    output_path = (
        EXPORT_PATH / filename
    )


    email_content = f"""Subject: Information Request — {structured_answer.section}

Hello,

Here is the information requested:

{structured_answer.answer}

Source: {structured_answer.source}
Document ID: {structured_answer.document_id}
Section: {structured_answer.section}
Confidence: {structured_answer.confidence:.3f}
Access Level: {structured_answer.access_level}

Best regards,
KOHLER Enterprise AI Copilot
"""


    output_path.write_text(
        email_content,
        encoding="utf-8",
    )


    return output_path