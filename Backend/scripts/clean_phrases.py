"""
Script para limpiar y mejorar la calidad de las frases en la base de datos.

Problemas a corregir:
- Símbolos especiales incorrectos (Ø, Æ, œ, etc.)
- Números y paréntesis
- Frases demasiado largas
- Palabras cortadas o mal formateadas
"""

import asyncio
import asyncpg
import os
import re
from typing import List, Dict

# Mapeo de caracteres corruptos a correctos
CHAR_REPLACEMENTS = {
    'Ø': 'é',
    'Æ': 'á',
    'æ': 'ñ',
    'œ': 'ú',  
    '\u2019': "'",  # Right single quotation mark
    '«': '"',
    '»': '"',
}

async def get_db_connection():
    """Create database connection."""
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'voice_biometrics'),
        user=os.getenv('DB_USER', 'voice_user'),
        password=os.getenv('DB_PASSWORD', 'voice_password')
    )

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Replace corrupt characters
    for old_char, new_char in CHAR_REPLACEMENTS.items():
        text = text.replace(old_char, new_char)
    
    # Remove numbers in parentheses like (1), (2), etc.
    text = re.sub(r'\(\d+\)', '', text)
    
    # Remove standalone numbers at start/end
    text = re.sub(r'^\d+\s+', '', text)
    text = re.sub(r'\s+\d+$', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove leading/trailing punctuation except final period
    text = text.strip(' .,;:-')
    
    return text

def should_delete_phrase(text: str, word_count: int) -> bool:
    """Determine if phrase should be deleted."""
    # Delete if too long (more than 15 words)
    if word_count > 15:
        return True
    
    # Delete if contains year numbers
    if re.search(r'\b(19|20)\d{2}\b', text):
        return True
    
    # Delete if starts with non-letter (likely corrupted)
    if not text[0].isalpha():
        return True
    
    # Delete if contains multiple special symbols
    special_count = sum(1 for c in text if c in 'Ø Æ æ œ § ¥ ¢ £')
    if special_count > 2:
        return True
    
    return False

async def main():
    """Main cleanup function."""
    conn = await get_db_connection()
    
    try:
        # Get all Spanish phrases
        phrases = await conn.fetch(
            "SELECT id, text, difficulty, word_count FROM phrase WHERE language = 'es'"
        )
        
        print(f"\n📊 Total frases encontradas: {len(phrases)}")
        
        cleaned_count = 0
        deleted_count = 0
        
        for phrase in phrases:
            phrase_id = phrase['id']
            original_text = phrase['text']
            difficulty = phrase['difficulty']
            word_count = phrase['word_count']
            
            # Check if should delete
            if should_delete_phrase(original_text, word_count):
                await conn.execute("DELETE FROM phrase WHERE id = $1", phrase_id)
                print(f"❌ ELIMINADA ({difficulty}): {original_text[:60]}...")
                deleted_count += 1
                continue
            
            # Clean text
            cleaned_text = clean_text(original_text)
            
            # Update if changed
            if cleaned_text != original_text:
                await conn.execute(
                    "UPDATE phrase SET text = $1 WHERE id = $2",
                    cleaned_text,
                    phrase_id
                )
                print(f"✅ LIMPIADA ({difficulty}):")
                print(f"   Antes: {original_text}")
                print(f"   Después: {cleaned_text}\n")
                cleaned_count += 1
        
        print("\n🎯 Resumen:")
        print(f"   - Frases limpiadas: {cleaned_count}")
        print(f"   - Frases eliminadas: {deleted_count}")
        print(f"   - Frases restantes: {len(phrases) - deleted_count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
