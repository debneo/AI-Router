from pathlib import Path

def extract_text(path:str) -> str:
    """Read raw text out of a file, picking the right reader by extension.
    Each file type has its own library; we hide that behind one function."""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if ext == ".docx":
        import docx

        return "\n\n".join(p.text for p in docx.Document(path).paragraphs)
    if ext in (".txt",".md"):
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {ext}")