#!/usr/bin/env python3
"""Run a specific database migration."""

import asyncio
import asyncpg
import sys
from pathlib import Path


async def run_migration(migration_file_path):
    """Execute the migration script."""
    migration_file = Path(migration_file_path)
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    migration_sql = migration_file.read_text()
    
    # Connect to database
    print(f"Connecting to database...")
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="voice_user",
        password="voice_password",
        database="voice_biometrics"
    )
    
    try:
        print(f"Running migration: {migration_file.name}...")
        await conn.execute(migration_sql)
        print("✓ Migration completed successfully!")
        
        # Verify books table if this is the books migration
        if "books" in migration_file.name:
            books_count = await conn.fetchval("SELECT COUNT(*) FROM books")
            print(f"\n✓ Books table created with {books_count} records")
            
            # Show some books
            books = await conn.fetch("SELECT title, author FROM books ORDER BY title LIMIT 5")
            print("\nSample books:")
            for book in books:
                print(f"  - {book['title']} - {book['author']}")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_specific_migration.py <migration_file>")
        sys.exit(1)
    
    asyncio.run(run_migration(sys.argv[1]))
