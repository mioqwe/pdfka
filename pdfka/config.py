from dataclasses import dataclass
from typing import Optional


@dataclass
class PageConfig:
    width: str = "297mm"  # A4 Landscape (Album)
    height: str = "210mm"
    margin_top: str = "0mm"  # Padding is handled by CSS in .pdf-page
    margin_bottom: str = "0mm"
    margin_left: str = "0mm"
    margin_right: str = "0mm"


@dataclass
class OverflowConfig:
    max_characters: int = 4000  # Increased for landscape layout
    max_words: int = 600
    warning_message: str = "Content truncated on page {page_num}: {char_count} chars exceeded limit of {max_chars}"


DEFAULT_PAGE_CONFIG = PageConfig()
DEFAULT_OVERFLOW_CONFIG = OverflowConfig()
