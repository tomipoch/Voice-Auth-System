"""
Script to assign book_id to existing phrases.
Since we don't have the original mapping, we'll distribute phrases evenly across books.
This is a temporary solution until PDFs are re-processed.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='../.env')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voice_biometrics')
DB_USER = os.getenv('DB_USER', 'voice_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'voice_password')

async def assign_books_to_phrases():
    """Assign book_id to existing phrases by distributing them evenly."""
    
    # Connect to database
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        # Get all books
        books = await conn.fetch("SELECT id, title, author FROM books ORDER BY title")
        print(f"\n📚 Found {len(books)} books")
        
        # Get total phrases
        total_phrases = await conn.fetchval("SELECT COUNT(*) FROM phrase WHERE book_id IS NULL")
        print(f"📝 Found {total_phrases} phrases without book_id")
        
        if total_phrases == 0:
            print("✅ All phrases already have book_id assigned!")
            return
        
        # Calculate phrases per book
        phrases_per_book = total_phrases // len(books)
        remainder = total_phrases % len(books)
        
        print(f"\n🔄 Assigning ~{phrases_per_book} phrases per book...")
        
        # Get all phrase IDs without book_id
        phrase_ids = await conn.fetch(
            "SELECT id FROM phrase WHERE book_id IS NULL ORDER BY created_at"
        )
        
        # Assign phrases to books
        current_index = 0
        for i, book in enumerate(books):
            # Calculate how many phrases for this book
            count = phrases_per_book + (1 if i < remainder else 0)
            
            # Get phrase IDs for this book
            book_phrase_ids = [p['id'] for p in phrase_ids[current_index:current_index + count]]
            
            if book_phrase_ids:
                # Update phrases with book_id
                await conn.execute(
                    "UPDATE phrase SET book_id = $1, source = $2 WHERE id = ANY($3)",
                    book['id'],
                    f"{book['title']} - {book['author']}" if book['author'] else book['title'],
                    book_phrase_ids
                )
                
                print(f"  ✓ {book['title']}: {len(book_phrase_ids)} phrases")
            
            current_index += count
        
        # Verify
        updated_count = await conn.fetchval("SELECT COUNT(*) FROM phrase WHERE book_id IS NOT NULL")
        print(f"\n✅ Successfully assigned book_id to {updated_count} phrases")
        
        # Show distribution
        print("\n📊 Distribution by book:")
        distribution = await conn.fetch("""
            SELECT b.title, b.author, COUNT(p.id) as phrase_count
            FROM books b
            LEFT JOIN phrase p ON p.book_id = b.id
            GROUP BY b.id, b.title, b.author
            ORDER BY phrase_count DESC
        """)
        
        for row in distribution:
            print(f"  {row['title']}: {row['phrase_count']} phrases")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Starting book assignment process...")
    asyncio.run(assign_books_to_phrases())
    print("\n✨ Done!")
