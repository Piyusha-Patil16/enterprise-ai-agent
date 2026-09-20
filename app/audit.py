from datetime import datetime, timezone
from pathlib import Path
import csv


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_PATH = PROJECT_ROOT / "logs"

LOG_FILE = LOG_PATH / "audit_log.csv"


# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------

LOG_PATH.mkdir(
    exist_ok=True
)


# ---------------------------------------------------------
# CSV fields
# ---------------------------------------------------------

FIELDNAMES = [
    "timestamp",
    "role",
    "question",
    "output_format",
    "source",
    "document_id",
    "section",
    "confidence",
    "access_level",
    "result_type",
]


# ---------------------------------------------------------
# Audit logging
# ---------------------------------------------------------

def log_interaction(
    role,
    question,
    output_format,
    source="N/A",
    document_id="N/A",
    section="N/A",
    confidence=0.0,
    access_level="N/A",
    result_type="answer",
):
    """
    Append one interaction to the audit log.

    The log is intentionally local and CSV-based so that
    the prototype remains simple and easy to inspect.
    """

    file_exists = LOG_FILE.exists()

    row = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "role": role,

        "question": question,

        "output_format": output_format,

        "source": source,

        "document_id": document_id,

        "section": section,

        "confidence": confidence,

        "access_level": access_level,

        "result_type": result_type,
    }

    with LOG_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# ---------------------------------------------------------
# Simple test
# ---------------------------------------------------------

if __name__ == "__main__":

    log_interaction(
        role="employee",
        question="Test audit event",
        output_format="Natural Language",
        source="finance_guidelines.md",
        document_id="POL-FIN-2026-042",
        section="Accommodation & Hotel Limits",
        confidence=0.624,
        access_level="employee",
        result_type="test",
    )

    print(
        f"Audit log written to: {LOG_FILE}"
    )