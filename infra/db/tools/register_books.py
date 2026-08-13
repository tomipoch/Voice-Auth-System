#!/usr/bin/env python3
"""
Register books from Libros/*.pdf into the books table.

Para usuarios externos sin la BD de libros: escanea infra/db/Libros/ e inserta
(upsert idempotente) cada PDF como fila en `books`. Así el pipeline de frases
puede vincular phrase.book_id correctamente.

Usage:
    python register_books.py [--dry-run]
    python register_books.py --update   # también actualiza título/autor existentes
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # infra/db
BOOKS_DIR = SCRIPT_DIR / 'Libros'

DEFAULT_TITLE_PATTERNS = [
    r'[_-]+',
    r'\.pdf$',
]


def readable_title(filename: str) -> str:
    """Derive a human-readable title from a PDF filename."""
    title = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
    for pattern in DEFAULT_TITLE_PATTERNS:
        title = re.sub(pattern, ' ', title)
    return ' '.join(title.split()).title()


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


async def register_books(dry_run: bool = False, update: bool = False):
    """Registra los PDFs de Libros/ en la tabla books (idempotente)."""
    pdf_files = sorted(BOOKS_DIR.glob('*.pdf'))
    if not pdf_files:
        print(f"❌ No PDF files found in {BOOKS_DIR}")
        print("   Coloque sus libros .pdf ahí y vuelva a ejecutar.")
        return

    conn = await asyncpg.connect(**_db_connection_params())
    try:
        if dry_run:
            print(f"🔍 DRY RUN - {len(pdf_files)} PDF(s) a registrar (sin cambios):")
            for pdf in pdf_files:
                print(f"   - {pdf.name} -> '{readable_title(pdf.name)}'")
            return

        for pdf in pdf_files:
            title = readable_title(pdf.name)
            if update:
                await conn.execute(
                    """
                    INSERT INTO books (title, author, filename, language)
                    VALUES ($1, NULL, $2, 'es')
                    ON CONFLICT (filename) DO UPDATE SET title = EXCLUDED.title
                    """,
                    title, pdf.name,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO books (title, author, filename, language)
                    VALUES ($1, NULL, $2, 'es')
                    ON CONFLICT (filename) DO NOTHING
                    """,
                    title, pdf.name,
                )
            print(f"   ✅ {pdf.name} -> '{title}'")

        total = await conn.fetchval("SELECT COUNT(*) FROM books")
        print(f"\n✅ Registrados. Total libros en BD: {total}")
    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra qué se registraría")
    parser.add_argument("--update", action="store_true",
                        help="Actualizar título/author de libros existentes (default: no toca)")
    args = parser.parse_args()
    asyncio.run(register_books(dry_run=args.dry_run, update=args.update))


if __name__ == "__main__":
    main()