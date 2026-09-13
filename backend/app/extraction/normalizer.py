import re

def normalize_text(text: str) -> str:
    """Cleans up raw OCR text for robust regex and semantic parsing."""
    if not text:
        return ""
    
    # Replace common OCR misreadings for currency symbols
    normalized = text.replace("₹", " Rs. ")
    normalized = re.sub(r'[\u20B9\u09F3]', ' Rs. ', normalized)
    
    # Clean non-standard quotes and dashes
    normalized = re.sub(r'[\u2018\u2019]', "'", normalized)
    normalized = re.sub(r'[\u201C\u201D]', '"', normalized)
    normalized = re.sub(r'[\u2013\u2014]', '-', normalized)
    
    # Standardize whitespace
    lines = [re.sub(r'\s+', ' ', line).strip() for line in normalized.splitlines()]
    return "\n".join([line for line in lines if line])

def clean_value(value: str) -> str:
    """Trims trailing punctuation, extra colons, and stray symbols."""
    if not value:
        return ""
    val = value.strip(" :-;,|~#*")
    return re.sub(r'\s+', ' ', val)
