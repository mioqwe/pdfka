import re
from typing import Any, Dict, List


def validate_json_structure(json_data: Dict[str, Any]) -> None:
    if not isinstance(json_data, dict):
        raise ValueError("JSON_FILE_ERROR: Input JSON must be a dictionary")

    if not json_data:
        raise ValueError("JSON_FILE_ERROR: JSON cannot be empty")

    page_keys = []

    for key, page in json_data.items():
        key_str = str(key)

        # Handle special keys: header, footer
        if key_str in ("header", "footer"):
            if not isinstance(page, str):
                raise ValueError(f"JSON_FILE_ERROR: '{key}' must be a string")
            continue

        # Page keys must be numeric
        if not key_str.isdigit():
            raise ValueError(f"JSON_FILE_ERROR: Page key '{key}' must be a number")

        page_num = int(key)
        if page_num < 1:
            raise ValueError(
                f"JSON_FILE_ERROR: Page key '{key}' must be a positive integer"
            )

        page_keys.append(page_num)

        if not isinstance(page, dict):
            raise ValueError(f"JSON_FILE_ERROR: Page {key} must be a dictionary")

        required_fields = ["h1", "content"]
        missing_fields = [field for field in required_fields if field not in page]

        if missing_fields:
            raise ValueError(
                f"JSON_FILE_ERROR: Page {key} is missing required fields: {', '.join(missing_fields)}"
            )

        allowed_fields = {"h1", "content", "image"}
        extra_fields = set(page.keys()) - allowed_fields
        if extra_fields:
            raise ValueError(
                f"JSON_FILE_ERROR: Page {key} contains invalid fields: {', '.join(extra_fields)}"
            )

        if not isinstance(page["h1"], str):
            raise ValueError(f"JSON_FILE_ERROR: Page {key} 'h1' must be a string")

        if not isinstance(page["content"], str):
            raise ValueError(f"JSON_FILE_ERROR: Page {key} 'content' must be a string")

        if "image" in page and not isinstance(page["image"], str):
            raise ValueError(f"JSON_FILE_ERROR: Page {key} 'image' must be a string")

    sorted_keys = sorted(page_keys)

    if not sorted_keys:
        raise ValueError("JSON_FILE_ERROR: At least one page (numeric key) is required")

    if sorted_keys[0] != 1:
        raise ValueError(
            f"JSON_FILE_ERROR: Page keys must start from 1 (found {sorted_keys[0]})"
        )

    for i in range(1, len(sorted_keys)):
        if sorted_keys[i] - sorted_keys[i - 1] != 1:
            raise ValueError(
                f"JSON_FILE_ERROR: Page keys must be consecutive integers (expected {sorted_keys[i - 1] + 1}, found {sorted_keys[i]})"
            )


def apply_truncation(content: str, max_chars: int, max_words: int) -> tuple[str, bool]:
    if len(content) <= max_chars:
        word_count = len(content.split())
        if word_count <= max_words:
            return content, False

    words = content.split()
    truncated_words = words[:max_words]
    truncated_content = " ".join(truncated_words)

    if len(truncated_content) > max_chars:
        truncated_content = truncated_content[: max_chars - 3] + "..."

    return truncated_content, True


def count_words(text: str) -> int:
    words = re.findall(r"\b\w+\b", text)
    return len(words)
