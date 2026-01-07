#!/usr/bin/env python3
"""
Import Phrases from TXT to Database
Imports cleaned phrases from TXT files to the PostgreSQL database.

Usage:
    python import_phrases_from_txt.py [--dry-run] [--clear]
"""

import re
import os
import argparse
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not installed. Run: pip install asyncpg")
    exit(1)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://voice_user:voice_password@localhost:5432/voice_biometrics')
TXT_DIR = Path(__file__).parent / 'frases_por_libro'


@dataclass
class Phrase:
    text: str
    word_count: int
    char_count: int
    difficulty: str
    source: str


def parse_txt_file(filepath: Path) -> List[Phrase]:
    """Parse a TXT file and extract phrases."""
    phrases = []
    current_difficulty = 'easy'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detect difficulty section (convert to lowercase for DB)
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
            match = re.match(r'^\d+\.\s*\[(\d+)\|(\w+)\]\s*(.+)$', line)
            if match:
                text = match.group(3).strip()
                
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
                            source=filepath.stem
                        ))
    
    return phrases


async def clear_existing_phrases(conn):
    """Clear existing phrases from database."""
    await conn.execute("DELETE FROM phrase_usage")
    await conn.execute("DELETE FROM phrase")
    print("🗑️  Cleared existing phrases")


async def insert_phrases(conn, phrases: List[Phrase]) -> int:
    """Insert phrases into database."""
    if not phrases:
        return 0
    
    await conn.executemany(
        """
        INSERT INTO phrase (text, source, word_count, char_count, language, difficulty, is_active)
        VALUES ($1, $2, $3, $4, 'es', $5, TRUE)
        """,
        [(p.text, p.source, p.word_count, p.char_count, p.difficulty) for p in phrases]
    )
    
    return len(phrases)


async def main(dry_run: bool = False, clear: bool = True):
    """Main import process."""
    print("=" * 60)
    print("📚 PHRASE IMPORT FROM TXT FILES")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made")
    
    # Connect to database
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    try:
        # Clear existing phrases if requested
        if clear and not dry_run:
            await clear_existing_phrases(conn)
        
        # Process TXT files
        txt_files = list(TXT_DIR.glob('*.txt'))
        print(f"📄 Found {len(txt_files)} TXT files")
        
        all_phrases = []
        stats = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for txt_file in sorted(txt_files):
            # Parse phrases from TXT
            phrases = parse_txt_file(txt_file)
            
            for p in phrases:
                stats[p.difficulty] += 1
            
            all_phrases.extend(phrases)
            print(f"   📕 {txt_file.name}: {len(phrases)} frases")
        
        print(f"\n📊 STATISTICS:")
        print(f"   EASY:   {stats['easy']:,}")
        print(f"   MEDIUM: {stats['medium']:,}")
        print(f"   HARD:   {stats['hard']:,}")
        print(f"   TOTAL:  {sum(stats.values()):,}")
        
        # Insert into database
        if not dry_run and all_phrases:
            inserted = await insert_phrases(conn, all_phrases)
            print(f"\n✅ Inserted {inserted:,} phrases into database")
        elif dry_run:
            print(f"\n🔍 Would insert {len(all_phrases):,} phrases (dry run)")
        
    finally:
        await conn.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import phrases from TXT files to database")
    parser.add_argument("--dry-run", action="store_true", help="Run without database changes")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear existing phrases")
    
    args = parser.parse_args()
    
    asyncio.run(main(
        dry_run=args.dry_run,
        clear=not args.no_clear
    ))
