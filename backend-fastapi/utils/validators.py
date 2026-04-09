from typing import Dict, Any, List
import re


def validate_document(filename: str, content: bytes) -> Dict[str, Any]:
    """Validate document before processing"""
    errors = []

    # Check file size (50MB max)
    if len(content) > 50 * 1024 * 1024:
        errors.append("File too large (max 50MB)")

    # Check file extension
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.csv']
    file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    if file_ext not in allowed_extensions:
        errors.append(f"Unsupported file type: {file_ext}")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_query(query: str) -> Dict[str, Any]:
    """Validate user query"""
    errors = []

    if not query or not query.strip():
        errors.append("Query cannot be empty")

    if len(query) > 10000:
        errors.append("Query too long (max 10000 characters)")

    # Check for potential injection
    if re.search(r'[<>{}]', query):
        errors.append("Query contains invalid characters")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "clean_query": query.strip() if query else ""
    }