#!/usr/bin/env python3
"""
Import phrases from reviewed TXT files (frases_por_libro/) into the phrase table.

Flujo:
    1. Coloque los PDFs en infra/db/Libros/
    2. python infra/db/tools/extract_phrases.py      -> genera los TXT
    3. Revise/ordene los TXT (formato "N. [score|style] frase")
    4. python infra/db/tools/import_phrases_from_txt.py [--dry-run] [--no-clear]

Persiste phoneme_score y style desde el formato "[score|style]" y vincula
phrase.book_id resolviendo el nombre del TXT contra books.filename. Si el libro
no existe, lo crea automáticamente (salvo --no-create-books).

Usage:
    python import_phrases_from_txt.py [--dry-run] [--no-clear] [--no-create-books]
"""

import re
import os
import sys
import argparse
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # infra/db
TXT_DIR = SCRIPT_DIR / 'frases_por_libro'


@dataclass
class Phrase:
    text: str
    word_count: int
    char_count: int
    difficulty: str
    source: str
    phoneme_score: Optional[int] = None
    style: Optional[str] = None


def _db_connection_params() -> dict:
    """Parámetros de conexión desde DATABASE_URL o variables DB_*."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": (parsed.path or "/voice_biometrics").lstrip("/"),
            "user": parsed.username or "voice_user",
            "password": parsed.password or "voice_password",
        }
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "voice_biometrics"),
        "user": os.getenv("DB_USER", "voice_user"),
        "password": os.getenv("DB_PASSWORD", "voice_password"),
    }


def parse_txt_file(filepath: Path) -> List[Phrase]:
    """Parse a TXT file and extract phrases with score/style metadata."""
    phrases = []
    current_difficulty = 'easy'
    book_title = filepath.stem

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Detect difficulty section
            if line.startswith('## EASY'):
                current_difficulty = 'easy'
                continue
            elif line.startswith('## MEDIUM'):
                current_difficulty = 'medium'
                continue
            elif line.startswith('## HARD'):
                current_difficulty = 'hard'
                continue

            # Skip headers and empty lines
            if not line or line.startswith('#') or line.startswith('=='):
                continue

            # Parse phrase line: "1. [85|narrative] Text here..."
            match = re.match(r'^(\d+)\.\s*\[(\d+)\|(\w+)\]\s*(.+)$', line)
            if match:
                text = match.group(4).strip()
                phoneme_score = int(match.group(2))
                style = match.group(3)

                if text:
                    word_count = len(text.split())
                    char_count = len(text)

                    # Only include phrases that meet char_count constraint (15-500)
                    if 15 <= char_count <= 500:
                        phrases.append(Phrase(
                            text=text,
                            word_count=word_count,
                            char_count=char_count,
                            difficulty=current_difficulty,
                            source=book_title,
                            phoneme_score=phoneme_score,
                            style=style,
                        ))

    return phrases


async def clear_existing_phrases(conn):
    """Clear existing phrases from database."""
    await conn.execute("DELETE FROM phrase_usage")
    await conn.execute("DELETE FROM phrase")
    print("🗑️  Cleared existing phrases")


async def resolve_book_ids(conn, sources: List[str]) -> dict:
    """Resolve book_id for each TXT source name against books.filename.

    Devuelve {source_name: book_id_or_None}.
    """
    stems = sorted({s[:-4] if s.lower().endswith('.txt') else s for s in set(sources)})
    book_map = {}
    if stems:
        rows = await conn.fetch(
            "SELECT filename, id FROM books WHERE filename = ANY($1::text[])",
            [f"{stem}.pdf" for stem in stems],
        )
        book_map = {row['filename']: row['id'] for row in rows}

    result = {}
    for source in set(sources):
        stem = source[:-4] if source.lower().endswith('.txt') else source
        result[source] = book_map.get(f"{stem}.pdf")
    return result


async def ensure_book(conn, source: str) -> Optional[str]:
    """Create a book row from the TXT source name and return its id."""
    stem = source[:-4] if source.lower().endswith('.txt') else source
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO books (title, author, filename, language)
            VALUES ($1, NULL, $2, 'es')
            ON CONFLICT (filename) DO NOTHING
            RETURNING id
            """,
            stem.replace('_', ' ').title(),
            f"{stem}.pdf",
        )
    except Exception as e:
        print(f"   ⚠️  No se pudo crear libro '{source}': {e}")
        return None
    if row:
        return row['id']
    return await conn.fetchval("SELECT id FROM books WHERE filename = $1", f"{stem}.pdf")


async def insert_phrases(conn, phrases: List[Phrase], create_missing: bool = True) -> int:
    """Insert phrases with score/style and book linkage."""
    if not phrases:
        return 0

    book_ids = await resolve_book_ids(conn, [p.source for p in phrases])
    missing = sorted({p.source for p in phrases if book_ids.get(p.source) is None})

    if missing:
        if create_missing:
            print(f"📚 Creando libros faltantes en BD: {', '.join(missing)}")
            for source in missing:
                await ensure_book(conn, source)
            book_ids = await resolve_book_ids(conn, [p.source for p in phrases])
            missing = sorted({p.source for p in phrases if book_ids.get(p.source) is None})
        if missing:
            print(f"   ⚠️  Libros sin registro en BD (phrase.book_id quedará NULL): {', '.join(missing)}")

    rows = []
    for p in phrases:
        rows.append((
            p.text, p.source, p.word_count, p.char_count, p.difficulty,
            p.phoneme_score, p.style, book_ids.get(p.source),
        ))

    await conn.executemany(
        """
        INSERT INTO phrase (
            text, source, word_count, char_count, language, difficulty, is_active,
            phoneme_score, style, book_id
        )
        VALUES ($1, $2, $3, $4, 'es', $5, TRUE, $6, $7, $8)
        """,
        rows,
    )
    return len(rows)


async def main(dry_run: bool = False, clear: bool = True, create_missing: bool = True):
    """Main import process."""
    print("=" * 60)
    print("📚 PHRASE IMPORT FROM TXT FILES")
    print("=" * 60)

    if dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made")

    try:
        conn = await asyncpg.connect(**_db_connection_params())
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

    try:
        if clear and not dry_run:
            await clear_existing_phrases(conn)

        txt_files = list(TXT_DIR.glob('*.txt'))
        print(f"📄 Found {len(txt_files)} TXT files")

        all_phrases = []
        stats = {'easy': 0, 'medium': 0, 'hard': 0}
        files_without_metadata = []

        for txt_file in sorted(txt_files):
            phrases = parse_txt_file(txt_file)
            for p in phrases:
                stats[p.difficulty] += 1
            all_phrases.extend(phrases)
            if not phrases:
                print(f"   ⚠️  {txt_file.name}: sin frases válidas (¿formato incorrecto?)")
            else:
                print(f"   📕 {txt_file.name}: {len(phrases)} frases")

        print(f"\n📊 STATISTICS:")
        print(f"   EASY:   {stats['easy']:,}")
        print(f"   MEDIUM: {stats['medium']:,}")
        print(f"   HARD:   {stats['hard']:,}")
        print(f"   TOTAL:  {sum(stats.values()):,}")

        if not dry_run and all_phrases:
            inserted = await insert_phrases(conn, all_phrases, create_missing=create_missing)
            print(f"\n✅ Inserted {inserted:,} phrases into database")
        elif dry_run:
            print(f"\n🔍 Would insert {len(all_phrases):,} phrases (dry run)")
            if create_missing:
                book_ids = await resolve_book_ids(conn, [p.source for p in all_phrases]) if all_phrases else {}
                missing = sorted({p.source for p in all_phrases if book_ids.get(p.source) is None})
                if missing:
                    print(f"   ℹ️  Libros que se crearían automáticamente: {', '.join(missing)}")
    finally:
        await conn.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import phrases from TXT files to database")
    parser.add_argument("--dry-run", action="store_true", help="Run without database changes")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear existing phrases")
    parser.add_argument("--no-create-books", action="store_true",
                        help="No auto-crear libros faltantes en BD (exige registro previo)")
    args = parser.parse_args()

    asyncio.run(main(
        dry_run=args.dry_run,
        clear=not args.no_clear,
        create_missing=not args.no_create_books,
    ))