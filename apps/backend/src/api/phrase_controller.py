"""API controller for phrase management."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..application.phrase_service import PhraseService
from ..application.dto.phrase_dto import PhraseDTO, PhraseStatsDTO
from ..infrastructure.config.dependencies import get_phrase_service, get_current_admin_user

router = APIRouter()


# Request/Response Models
class PhraseResponse(BaseModel):
    """Response model for a phrase."""
    id: str
    text: str
    source: Optional[str]
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    word_count: int
    char_count: int
    language: str
    difficulty: str
    is_active: bool
    created_at: str
    phoneme_score: Optional[int] = None
    style: Optional[str] = None


class PhraseStatsResponse(BaseModel):
    """Response model for phrase statistics."""
    total: int
    active: int
    inactive: int
    easy: int
    medium: int
    hard: int
    language: str


class BookResponse(BaseModel):
    """Response model for a book."""
    id: str
    title: str
    author: Optional[str] = None


class PhraseListResponse(BaseModel):
    """Response model for paginated phrase list."""
    phrases: List[PhraseResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class UpdatePhraseStatusRequest(BaseModel):
    """Request model for updating phrase status."""
    is_active: bool


class UpdatePhraseTextRequest(BaseModel):
    """Request model for updating phrase text."""
    text: str


# Endpoints

@router.get("/books", response_model=List[BookResponse])
async def get_books(
    _current_user=Depends(get_current_admin_user)
):
    """
    Get list of all books.
    Admin only.
    """
    from ..infrastructure.config.dependencies import get_db_pool
    
    pool = await get_db_pool()
    
    books = await pool.fetch(
        "SELECT id, title, author FROM books ORDER BY title"
    )
    
    return [
        BookResponse(
            id=str(book['id']),
            title=book['title'],
            author=book['author']
        )
        for book in books
    ]


@router.get("/stats", response_model=PhraseStatsResponse)
async def get_phrase_stats(
    language: str = Query(default="es"),
    phrase_service: PhraseService = Depends(get_phrase_service),
    _current_user=Depends(get_current_admin_user)
):
    """
    Get statistics about available phrases.
    Admin only.
    """
    from ..infrastructure.config.dependencies import get_db_pool
    
    pool = await get_db_pool()
    
    # Get basic stats
    stats = await phrase_service.get_phrase_stats(language=language)
    
    # Get active/inactive counts
    active_count = await pool.fetchval(
        "SELECT COUNT(*) FROM phrase WHERE is_active = TRUE AND language = $1",
        language
    )
    inactive_count = await pool.fetchval(
        "SELECT COUNT(*) FROM phrase WHERE is_active = FALSE AND language = $1",
        language
    )
    
    return PhraseStatsResponse(
        total=stats.total,
        active=active_count or 0,
        inactive=inactive_count or 0,
        easy=stats.easy,
        medium=stats.medium,
        hard=stats.hard,
        language=stats.language
    )


@router.get("/list", response_model=PhraseListResponse)
async def list_phrases(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    difficulty: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    book_id: Optional[str] = Query(default=None),
    author: Optional[str] = Query(default=None),
    phrase_service: PhraseService = Depends(get_phrase_service),
    _current_user=Depends(get_current_admin_user)
):
    """
    Get paginated list of phrases with optional filters.
    Admin only.
    
    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 100)
    - difficulty: Filter by difficulty (easy/medium/hard)
    - is_active: Filter by active status
    - search: Search in phrase text
    - book_id: Filter by book ID
    - author: Filter by author name
    """
    from ..infrastructure.persistence.PostgresPhraseRepository import PostgresPhraseRepository
    from ..infrastructure.config.dependencies import get_db_pool
    from uuid import UUID
    
    pool = await get_db_pool()
    phrase_repo = PostgresPhraseRepository(pool)
    
    # Convert book_id to UUID if provided
    book_uuid = UUID(book_id) if book_id else None
    
    phrases, total = await phrase_repo.find_paginated(
        page=page,
        limit=limit,
        difficulty=difficulty,
        is_active=is_active,
        search=search,
        book_id=book_uuid,
        author=author
    )
    
    # Convert to response model
    phrase_responses = [
        PhraseResponse(
            id=str(p['id']),
            text=p['text'],
            source=p['source'],
            book_title=p.get('book_title'),
            book_author=p.get('book_author'),
            word_count=p['word_count'],
            char_count=p['char_count'],
            language=p['language'],
            difficulty=p['difficulty'],
            is_active=p['is_active'],
            created_at=p['created_at'].isoformat(),
            phoneme_score=p.get('phoneme_score'),
            style=p.get('style')
        )
        for p in phrases
    ]
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return PhraseListResponse(
        phrases=phrase_responses,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/random", response_model=List[PhraseResponse])
async def get_random_phrases(
    count: int = Query(default=1, ge=1, le=10),
    difficulty: Optional[str] = Query(default=None),
    language: str = Query(default="es"),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Get random phrases for enrollment or verification.
    Public endpoint (used by enrollment/verification flows).
    
    Query parameters:
    - count: Number of phrases to return (default: 1, max: 10)
    - difficulty: Filter by difficulty (easy/medium/hard)
    - language: Language code (default: es)
    """
    phrases = await phrase_service.get_random_phrases(
        count=count,
        difficulty=difficulty,
        language=language
    )
    
    return [
        PhraseResponse(
            id=p.id,
            text=p.text,
            source=p.source,
            word_count=p.word_count,
            char_count=p.char_count,
            language=p.language,
            difficulty=p.difficulty,
            is_active=p.is_active,
            created_at=p.created_at
        )
        for p in phrases
    ]


@router.patch("/{phrase_id}/status")
async def update_phrase_status(
    phrase_id: str,
    request: UpdatePhraseStatusRequest,
    phrase_service: PhraseService = Depends(get_phrase_service),
    _current_user=Depends(get_current_admin_user)
):
    """
    Update the active status of a phrase.
    Admin only.
    """
    try:
        phrase_uuid = UUID(phrase_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid phrase ID format")
    
    success = await phrase_service.update_phrase_status(
        phrase_id=phrase_uuid,
        is_active=request.is_active
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    return {
        "success": True,
        "message": f"Phrase {'activated' if request.is_active else 'deactivated'} successfully",
        "phrase_id": phrase_id,
        "is_active": request.is_active
    }


@router.delete("/{phrase_id}")
async def delete_phrase(
    phrase_id: str,
    phrase_service: PhraseService = Depends(get_phrase_service),
    _current_user=Depends(get_current_admin_user)
):
    """
    Delete a phrase from the system.
    Admin only.
    """
    try:
        phrase_uuid = UUID(phrase_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid phrase ID format")
    
    success = await phrase_service.delete_phrase(phrase_id=phrase_uuid)
    
    if not success:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    return {
        "success": True,
        "message": "Phrase deleted successfully",
        "phrase_id": phrase_id
    }


@router.put("/{phrase_id}")
async def update_phrase_text(
    phrase_id: str,
    request: UpdatePhraseTextRequest,
    _current_user=Depends(get_current_admin_user)
):
    """
    Update the text of a phrase.
    Admin only.
    """
    from ..infrastructure.config.dependencies import get_db_pool
    
    try:
        phrase_uuid = UUID(phrase_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid phrase ID format")
    
    # Validate text
    text = request.text.strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Text must be at least 20 characters")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text must be at most 500 characters")
    
    # Calculate word and char count
    word_count = len(text.split())
    char_count = len(text)
    
    pool = await get_db_pool()
    
    result = await pool.execute(
        """
        UPDATE phrase 
        SET text = $1, word_count = $2, char_count = $3
        WHERE id = $4
        """,
        text, word_count, char_count, phrase_uuid
    )
    
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    return {
        "success": True,
        "message": "Phrase updated successfully",
        "phrase_id": phrase_id,
        "text": text,
        "word_count": word_count,
        "char_count": char_count
    }

