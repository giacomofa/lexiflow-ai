from pypdf import PdfReader


def load_txt(file) -> str:
    return file.read().decode("utf-8")


def load_pdf(file) -> str:
    reader = PdfReader(file)
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n".join(pages_text)


def load_document(uploaded_file) -> str:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return load_txt(uploaded_file)

    if file_name.endswith(".pdf"):
        return load_pdf(uploaded_file)

    raise ValueError("Formato de arquivo não suportado. Use PDF ou TXT.")