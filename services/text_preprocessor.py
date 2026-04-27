def preprocess_text(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text