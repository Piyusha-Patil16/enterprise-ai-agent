from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


# --------------------------------------------------
# Export directory
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


# --------------------------------------------------
# 1. Export directory
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPORT_PATH = PROJECT_ROOT / "exports"

EXPORT_PATH.mkdir(exist_ok=True)


# --------------------------------------------------
# 2. Excel exporter
# --------------------------------------------------

def export_to_excel(
    structured_answer,
    filename="answer.xlsx"
):
    """
    Convert a validated StructuredAnswer object into
    a simple downloadable Excel file.
    """

    output_path = EXPORT_PATH / filename

    data = {
        "Field": [
            "Answer",
            "Source",
            "Document ID",
            "Section",
        ],
        "Value": [
            structured_answer.answer,
            structured_answer.source,
            structured_answer.document_id,
            structured_answer.section,
        ],
    }

    dataframe = pd.DataFrame(data)

    dataframe.to_excel(
        output_path,
        index=False,
    )

    return output_path


# --------------------------------------------------
# 3. XML exporter
# --------------------------------------------------

def export_to_xml(
    structured_answer,
    filename="answer.xml"
):
    """
    Convert a validated StructuredAnswer object into
    a simple XML file.
    """

    output_path = EXPORT_PATH / filename

    root = ET.Element(
        "enterprise_answer"
    )

    answer_element = ET.SubElement(
        root,
        "answer"
    )
    answer_element.text = structured_answer.answer

    source_element = ET.SubElement(
        root,
        "source"
    )
    source_element.text = structured_answer.source

    document_id_element = ET.SubElement(
        root,
        "document_id"
    )
    document_id_element.text = (
        structured_answer.document_id
    )

    section_element = ET.SubElement(
        root,
        "section"
    )
    section_element.text = (
        structured_answer.section
    )

    tree = ET.ElementTree(root)

    tree.write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )

    return output_path