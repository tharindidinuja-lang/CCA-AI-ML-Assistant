"""
Utility functions for the CCA AI Assistant.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
import hashlib


def setup_logging(log_file: str = "logs/app.log"):
    """Set up logging configuration."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)


def generate_file_hash(file_path: str) -> str:
    """Generate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None