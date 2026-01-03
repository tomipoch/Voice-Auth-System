#!/usr/bin/env python3
"""
Phrase Extraction Script
Extracts quality phrases from PDF books for voice biometric enrollment/verification.

Usage:
    python extract_phrases.py [--dry-run] [--min-per-book 30] [--max-per-book 100]
"""

import re
import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / 'apps/backend/.env')
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Database config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voice_biometrics')
DB_USER = os.getenv('DB_USER', 'voice_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'voice_password')

# Paths
BOOKS_DIR = Path(__file__).parent / 'Libros'

# Spanish phonemes for diversity calculation
SPANISH_VOWELS = set('aeiouáéíóúü')
SPANISH_CONSONANTS = set('bcdfghjklmnñpqrstvwxyz')
SPANISH_SPECIAL_PHONEMES = ['ch', 'll', 'rr', 'ñ', 'qu', 'gu']


@dataclass
class Phrase:
    text: str
    word_count: int
    char_count: int
    difficulty: str
    book_id: str
    source: str
    phoneme_score: int = 0
    style: str = 'narrative'


def calculate_phoneme_score(text: str) -> int:
    """
    Calculate phonemic diversity score (0-100).
    Higher score = more varied phonemes = better for voice biometrics.
    """
    text_lower = text.lower()
    
    # Count unique vowels used
    vowels_used = set(c for c in text_lower if c in SPANISH_VOWELS)
    vowel_score = len(vowels_used) / 6 * 30  # Max 30 points for vowels
    
    # Count unique consonants used
    consonants_used = set(c for c in text_lower if c in SPANISH_CONSONANTS)
    consonant_score = len(consonants_used) / 21 * 40  # Max 40 points for consonants
    
    # Bonus for special Spanish phonemes
    special_bonus = 0
    for phoneme in SPANISH_SPECIAL_PHONEMES:
        if phoneme in text_lower:
            special_bonus += 5
    special_bonus = min(special_bonus, 20)  # Max 20 points for special phonemes
    
    # Bonus for length variety (mixture of short and long words)
    words = text_lower.split()
    if words:
        lengths = [len(w) for w in words]
        length_variety = len(set(lengths)) / max(len(words), 1) * 10  # Max 10 points
    else:
        length_variety = 0
    
    total = int(vowel_score + consonant_score + special_bonus + length_variety)
    return min(total, 100)


def detect_style(text: str) -> str:
    """
    Detect the style of the phrase.
    Returns: 'narrative', 'descriptive', 'dialogue', or 'poetic'
    """
    text_lower = text.lower()
    
    # Dialogue indicators
    dialogue_patterns = [
        '—', '–', '"', '«',
        ' dijo ', ' preguntó ', ' respondió ', ' exclamó ',
        ' gritó ', ' murmuró ', ' susurró ', ' contestó ',
        '¿', '!',
    ]
    dialogue_score = sum(1 for p in dialogue_patterns if p in text)
    
    # Descriptive indicators (adjectives, descriptions)
    descriptive_patterns = [
        ' era ', ' estaba ', ' parecía ', ' tenía ',
        ' grande ', ' pequeño ', ' hermoso ', ' oscuro ',
        ' alto ', ' bajo ', ' largo ', ' ancho ',
        ' color ', ' forma ', ' aspecto ',
    ]
    descriptive_score = sum(1 for p in descriptive_patterns if p in text_lower)
    
    # Poetic indicators
    poetic_patterns = [
        ' cual ', ' como el ', ' como la ', ' cual si ',
        ' oh ', ' ay ', '¡oh', '¡ay',
        ' amor ', ' alma ', ' cielo ', ' tierra ',
        ' eterno ', ' infinito ',
    ]
    poetic_score = sum(1 for p in poetic_patterns if p in text_lower)
    
    # Determine style based on scores
    if dialogue_score >= 2:
        return 'dialogue'
    elif poetic_score >= 2:
        return 'poetic'
    elif descriptive_score >= 2:
        return 'descriptive'
    else:
        return 'narrative'


def classify_difficulty(word_count: int) -> str:
    """
    Classify phrase difficulty based on word count.
    Optimized for voice biometric enrollment/verification.
    - Easy: 8-15 words
    - Medium: 16-21 words
    - Hard: 22+ words
    """
    if word_count <= 15:
        return 'easy'
    elif word_count <= 21:
        return 'medium'
    else:
        return 'hard'


def is_valid_phrase(text: str) -> bool:
    """
    Check if a phrase is valid for voice biometric use.
    
    Filters out:
    - Too short or too long phrases
    - Lines with page numbers, headers, footers
    - Lines with URLs or special formatting
    - Lines with too many numbers or special characters
    """
    # Length checks (minimum 40 chars for voice biometrics)
    if len(text) < 40 or len(text) > 500:
        return False
    
    # Word count check (minimum 8 words for proper voice recognition)
    words = text.split()
    if len(words) < 8:
        return False
    
    # Patterns to reject
    reject_patterns = [
        r'^\d+$',  # Just numbers (page numbers)
        r'^\d+\s*$',  # Numbers with whitespace
        r'^cap[íi]tulo',  # Chapter headers
        r'^CAPÍTULO',
        r'^índice',
        r'^ÍNDICE',
        r'^prólogo',
        r'^PRÓLOGO',
        r'^epílogo',
        r'^EPÍLOGO',
        r'^www\.',
        r'^http',
        r'^\[\d+\]',  # Footnote references
        r'^•',  # Bullet points
        r'^-{3,}',  # Separators
        r'^_{3,}',
        r'^\*{3,}',
        r'^\d+\.',  # Numbered lists at start
        r'^Página\s+\d+',
        r'^\.\.\.',  # Ellipsis only
        r'^…',
        r'^P\.\s*\d+',  # Page references like "P. 11529"
        r'^C\.P\.',  # Postal codes
        r'Ciudad de México',  # Publisher addresses
        r'^ESTROFA',  # Theater/poetry annotations
        r'^ESCENA',
        r'^ACTO',
        r'\d{5,}',  # Long numbers (ISBN, phone, etc.)
    ]
    
    text_lower = text.lower().strip()
    for pattern in reject_patterns:
        if re.match(pattern, text_lower, re.IGNORECASE):
            return False
    
    # Check for excessive special characters (more than 10%)
    special_chars = len(re.findall(r'[^\w\sáéíóúüñ¿¡.,;:!?\'\"()-]', text, re.IGNORECASE))
    if special_chars > len(text) * 0.1:
        return False
    
    # Check for excessive numbers (more than 20%)
    digits = len(re.findall(r'\d', text))
    if digits > len(text) * 0.2:
        return False
    
    # Must start with a capital letter or ¿¡
    if not re.match(r'^[A-ZÁÉÍÓÚÜÑ¿¡]', text):
        return False
    
    # Should end with proper punctuation or be a complete thought
    if not re.search(r'[.!?»"]$', text):
        # Allow if it's long enough to be a clause
        if len(words) < 6:
            return False
    
    # Detect OCR artifacts: consecutive single-letter words (broken text)
    # e.g., "vie ra ga nan do" instead of "viera ganando"
    short_word_streak = 0
    max_streak = 0
    for word in words:
        if len(word) <= 2 and word.isalpha():
            short_word_streak += 1
            max_streak = max(max_streak, short_word_streak)
        else:
            short_word_streak = 0
    
    # If more than 3 consecutive short words, likely OCR issue
    if max_streak >= 3:
        return False
    
    # Reject if more than 40% of words are very short (1-2 chars)
    short_words = sum(1 for w in words if len(w) <= 2)
    if short_words > len(words) * 0.4:
        return False
    
    # Reject author/publisher credits
    if re.search(r'Autor|AUTOR|Editorial|edición|ISBN|Copyright|©|rights reserved', text):
        return False
    
    # Reject text with suspicious patterns (broken words from OCR)
    # Pattern: "secre­\xadto" or "es tá" (space in middle of word)
    if re.search(r'\w­\s*\w', text):  # soft hyphen word break
        return False
    
    # Pattern: single letter followed by space then letter(s) that should be one word
    # Like "es tá" or "na da" - but allow valid short words like "a", "o", "y", "e"
    if re.search(r'\b[bcdfghjklmnpqrstvwxz][aeiouáéíóú]\s[a-záéíóú]{1,3}\b', text, re.IGNORECASE):
        return False
    
    return True


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Fix end-of-line word breaks (e.g., "peque- ños" -> "pequeños")
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    
    # Remove soft hyphens
    text = text.replace('\xad', '')
    text = text.replace('­', '')  # Another form of soft hyphen
    
    # Fix common OCR issues
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces
    text = text.replace(' ,', ',')
    text = text.replace(' .', '.')
    text = text.replace(' ;', ';')
    text = text.replace(' :', ':')
    text = text.replace('( ', '(')
    text = text.replace(' )', ')')
    
    # Remove trailing page numbers
    text = re.sub(r'\s+\d{1,3}$', '', text)
    
    # Normalize quotes
    text = text.replace('«', '"')
    text = text.replace('»', '"')
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    
    return text.strip()


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text using regex.
    Tries to split on sentence boundaries.
    """
    # Split on sentence-ending punctuation followed by space and capital letter
    # But preserve the punctuation
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡])', text)
    
    return [clean_text(s) for s in sentences if s.strip()]


def extract_phrases_from_pdf(pdf_path: Path) -> List[str]:
    """Extract text phrases from a PDF file."""
    phrases = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if not text:
                continue
            
            # Split into sentences
            sentences = extract_sentences(text)
            
            for sentence in sentences:
                if is_valid_phrase(sentence):
                    phrases.append(sentence)
        
        doc.close()
        
    except Exception as e:
        print(f"  ⚠️  Error processing {pdf_path.name}: {e}")
    
    return phrases


async def get_books_from_db(conn) -> dict:
    """Get book mapping from database."""
    rows = await conn.fetch("SELECT id, filename, title, author FROM books")
    return {row['filename']: dict(row) for row in rows}


async def clear_existing_phrases(conn):
    """Clear existing phrases from database."""
    # First clear phrase_usage to avoid FK constraint
    await conn.execute("DELETE FROM phrase_usage")
    await conn.execute("DELETE FROM phrase")
    print("🗑️  Cleared existing phrases")


async def insert_phrases(conn, phrases: List[Phrase]):
    """Insert phrases into database."""
    if not phrases:
        return 0
    
    # Prepare data for batch insert
    await conn.executemany(
        """
        INSERT INTO phrase (text, source, word_count, char_count, language, difficulty, is_active, book_id, phoneme_score, style)
        VALUES ($1, $2, $3, $4, 'es', $5, TRUE, $6, $7, $8)
        """,
        [(p.text, p.source, p.word_count, p.char_count, p.difficulty, p.book_id, p.phoneme_score, p.style) for p in phrases]
    )
    
    return len(phrases)


async def main(dry_run: bool = False, min_per_book: int = 30, max_per_book: int = 100):
    """Main extraction process."""
    print("\n" + "="*60)
    print("📚 PHRASE EXTRACTION FROM PDF BOOKS")
    print("="*60)
    
    # Connect to database
    if not dry_run:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        books_db = await get_books_from_db(conn)
    else:
        print("🔍 DRY RUN MODE - No database changes will be made")
        books_db = {}
    
    # Get all PDFs
    pdf_files = list(BOOKS_DIR.glob("*.pdf"))
    print(f"\n📂 Found {len(pdf_files)} PDF files in {BOOKS_DIR}")
    
    all_phrases = []
    stats = {
        'easy': 0,
        'medium': 0,
        'hard': 0,
        'by_book': {},
        'by_style': {'narrative': 0, 'descriptive': 0, 'dialogue': 0, 'poetic': 0},
        'phoneme_scores': []
    }
    
    for pdf_file in sorted(pdf_files):
        print(f"\n📖 Processing: {pdf_file.name}")
        
        # Get book info from DB
        book_info = books_db.get(pdf_file.name, {})
        book_id = book_info.get('id')
        book_title = book_info.get('title', pdf_file.stem)
        book_author = book_info.get('author', '')
        source = f"{book_title} - {book_author}" if book_author else book_title
        
        # Extract phrases
        raw_phrases = extract_phrases_from_pdf(pdf_file)
        print(f"   Found {len(raw_phrases)} valid phrases")
        
        # Limit per book to ensure variety
        if len(raw_phrases) > max_per_book:
            # Sample evenly by difficulty
            easy = [p for p in raw_phrases if classify_difficulty(len(p.split())) == 'easy']
            medium = [p for p in raw_phrases if classify_difficulty(len(p.split())) == 'medium']
            hard = [p for p in raw_phrases if classify_difficulty(len(p.split())) == 'hard']
            
            # Take proportionally from each
            target = max_per_book // 3
            raw_phrases = easy[:target] + medium[:target] + hard[:target]
        
        # Create Phrase objects
        book_phrases = []
        for text in raw_phrases:
            words = text.split()
            phrase = Phrase(
                text=text,
                word_count=len(words),
                char_count=len(text),
                difficulty=classify_difficulty(len(words)),
                book_id=str(book_id) if book_id else None,
                source=source,
                phoneme_score=calculate_phoneme_score(text),
                style=detect_style(text)
            )
            book_phrases.append(phrase)
            stats[phrase.difficulty] += 1
            stats['by_style'][phrase.style] += 1
            stats['phoneme_scores'].append(phrase.phoneme_score)
        
        stats['by_book'][book_title] = len(book_phrases)
        all_phrases.extend(book_phrases)
        
        if len(book_phrases) < min_per_book:
            print(f"   ⚠️  Only {len(book_phrases)} phrases (minimum: {min_per_book})")
        else:
            print(f"   ✓ {len(book_phrases)} phrases extracted")
    
    # Summary
    print("\n" + "="*60)
    print("📊 EXTRACTION SUMMARY")
    print("="*60)
    print(f"\n Total phrases: {len(all_phrases)}")
    print(f" • Easy:   {stats['easy']} ({stats['easy']*100//len(all_phrases) if all_phrases else 0}%)")
    print(f" • Medium: {stats['medium']} ({stats['medium']*100//len(all_phrases) if all_phrases else 0}%)")
    print(f" • Hard:   {stats['hard']} ({stats['hard']*100//len(all_phrases) if all_phrases else 0}%)")
    
    # Phoneme score stats
    if stats['phoneme_scores']:
        avg_score = sum(stats['phoneme_scores']) // len(stats['phoneme_scores'])
        min_score = min(stats['phoneme_scores'])
        max_score = max(stats['phoneme_scores'])
        print(f"\n🔊 Phoneme Diversity Score:")
        print(f" • Average: {avg_score}/100")
        print(f" • Range: {min_score} - {max_score}")
    
    # Style distribution
    print(f"\n✍️  By Style:")
    for style, count in stats['by_style'].items():
        pct = count * 100 // len(all_phrases) if all_phrases else 0
        print(f" • {style.capitalize()}: {count} ({pct}%)")
    
    print("\n📚 By Book:")
    for book, count in sorted(stats['by_book'].items(), key=lambda x: x[1], reverse=True):
        status = "✓" if count >= min_per_book else "⚠️"
        print(f"   {status} {book}: {count}")
    
    # Insert into database
    if not dry_run and all_phrases:
        print("\n💾 Inserting into database...")
        await clear_existing_phrases(conn)
        inserted = await insert_phrases(conn, all_phrases)
        print(f"✅ Inserted {inserted} phrases")
        await conn.close()
    elif dry_run:
        print("\n🔍 Dry run complete. No changes made.")
        # Show sample phrases
        print("\n📝 Sample phrases:")
        import random
        samples = random.sample(all_phrases, min(10, len(all_phrases)))
        for i, p in enumerate(samples, 1):
            print(f"\n{i}. [{p.difficulty}] ({p.word_count} words)")
            print(f"   \"{p.text[:100]}{'...' if len(p.text) > 100 else ''}\"")
    
    print("\n✨ Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract phrases from PDF books")
    parser.add_argument("--dry-run", action="store_true", help="Run without database changes")
    parser.add_argument("--min-per-book", type=int, default=30, help="Minimum phrases per book (warning if less)")
    parser.add_argument("--max-per-book", type=int, default=100, help="Maximum phrases per book")
    
    args = parser.parse_args()
    
    asyncio.run(main(
        dry_run=args.dry_run,
        min_per_book=args.min_per_book,
        max_per_book=args.max_per_book
    ))
