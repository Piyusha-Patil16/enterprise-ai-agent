from pathlib import Path


document_path = Path("data/employee/finance_guidelines.md")

content = document_path.read_text(encoding="utf-8")

print("Document loaded successfully!")
print()
print("First 500 characters:")
print(content[:500])