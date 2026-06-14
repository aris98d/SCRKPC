from pathlib import Path
import fitz
import docx


def parse_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def parse_docx(file_path: str) -> str:
    document = docx.Document(file_path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_pdf(file_path: str) -> str:
    pdf = fitz.open(file_path)
    pages = []

    for index, page in enumerate(pdf):
        text = page.get_text()
        pages.append(f"[Page {index + 1}]\n{text}")

    return "\n\n".join(pages)


def parse_document(file_path: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".txt":
        return parse_txt(file_path)

    if suffix == ".docx":
        return parse_docx(file_path)

    if suffix == ".pdf":
        return parse_pdf(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")
