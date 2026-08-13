"""DTOs for phrase management."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class PhraseDTO:
    """Data transfer object for a phrase."""

    id: str
    text: str
    source: Optional[str]
    word_count: int
    char_count: int
    language: str
    difficulty: str
    is_active: bool
    created_at: str


@dataclass
class PhraseStatsDTO:
    """Statistics about available phrases."""

    total: int
    active: int
    inactive: int
    easy: int
    medium: int
    hard: int
    language: str


@dataclass
class GetPhrasesRequestDTO:
    """Request DTO for getting random phrases."""

    user_id: Optional[str] = None
    count: int = 1
    difficulty: Optional[str] = None
    language: str = "es"


@dataclass
class RecordUsageRequestDTO:
    """Request DTO for recording phrase usage."""

    phrase_id: str
    user_id: str
    used_for: str  # 'enrollment' or 'verification'


@dataclass
class PhraseListDTO:
    """Paginated phrase list response."""

    phrases: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 50
    total_pages: int = 1


@dataclass
class BookDTO:
    """Book metadata."""

    id: str
    title: str
    author: Optional[str] = None
