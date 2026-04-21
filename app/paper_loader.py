"""Load paper from text, .docx, or .pdf."""
from pathlib import Path


def load_paper(source, format=None):
    """
    Load paper content from text string, .docx, or .pdf.

    Args:
        source: Either a file path (str/Path) or raw text content.
        format: 'text', 'docx', 'pdf', or None (auto-detect from path extension).

    Returns:
        str: Extracted paper text.

    Raises:
        ValueError: If format is unsupported.
    """
    if format is None:
        if isinstance(source, Path):
            format = source.suffix.lower().lstrip('.')
        else:
            # If source is a path string, try to detect extension
            s = str(source)
            if s.endswith('.docx'):
                format = 'docx'
            elif s.endswith('.pdf'):
                format = 'pdf'
            else:
                format = 'text'

    if format == "text":
        return source

    if format == "docx":
        import zipfile
        import xml.etree.ElementTree as ET

        ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        with zipfile.ZipFile(source, 'r') as z:
            with z.open('word/document.xml') as f:
                tree = ET.parse(f)

        texts = []
        for para in tree.iter(f'{{{ns}}}p'):
            parts = []
            for t in para.iter(f'{{{ns}}}t'):
                if t.text:
                    parts.append(t.text)
            line = ''.join(parts)
            if line.strip():
                texts.append(line)
        return '\n'.join(texts)

    if format == "pdf":
        import pymupdf

        doc = pymupdf.open(source)
        texts = []
        for page in doc:
            texts.append(page.get_text())
        return '\n'.join(texts)

    raise ValueError(f"Unsupported format: {format}. Supported: text, docx, pdf")