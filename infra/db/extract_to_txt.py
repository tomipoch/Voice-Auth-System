#!/usr/bin/env python3
"""
Extract phrases from PDF books to TXT files (no database).
Each book gets its own TXT file for manual review and correction.

Usage:
    python extract_to_txt.py
"""

import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

# Paths
BOOKS_DIR = Path(__file__).parent / 'Libros'
OUTPUT_DIR = Path(__file__).parent / 'frases_por_libro'

# Spanish phonemes for diversity calculation
SPANISH_VOWELS = set('aeiouáéíóúü')
SPANISH_CONSONANTS = set('bcdfghjklmnñpqrstvwxyz')
SPANISH_SPECIAL_PHONEMES = ['ch', 'll', 'rr', 'ñ', 'qu', 'gu']


def calculate_phoneme_score(text: str) -> int:
    """Calculate phonemic diversity score (0-100)."""
    text_lower = text.lower()
    
    vowels_used = set(c for c in text_lower if c in SPANISH_VOWELS)
    vowel_score = len(vowels_used) / 6 * 30
    
    consonants_used = set(c for c in text_lower if c in SPANISH_CONSONANTS)
    consonant_score = len(consonants_used) / 21 * 40
    
    special_bonus = sum(5 for p in SPANISH_SPECIAL_PHONEMES if p in text_lower)
    special_bonus = min(special_bonus, 20)
    
    words = text_lower.split()
    if words:
        lengths = [len(w) for w in words]
        length_variety = len(set(lengths)) / max(len(words), 1) * 10
    else:
        length_variety = 0
    
    return min(int(vowel_score + consonant_score + special_bonus + length_variety), 100)


def classify_difficulty(word_count: int) -> str:
    """Classify phrase difficulty based on word count."""
    if word_count <= 15:
        return 'easy'
    elif word_count <= 21:
        return 'medium'
    else:
        return 'hard'


def detect_style(text: str) -> str:
    """
    Detect the style of the phrase.
    Returns: 'narrative', 'descriptive', 'dialogue', or 'poetic'
    """
    text_lower = text.lower()
    
    # Dialogue indicators - more extensive
    dialogue_patterns = [
        '—', '–', '"', '«', '»',
        ' dijo', ' preguntó', ' respondió', ' exclamó',
        ' gritó', ' murmuró', ' susurró', ' contestó',
        ' replicó', ' añadió', ' interrumpió', ' comentó',
        ' afirmó', ' negó', ' insistió', ' explicó',
        '¿', '?', '!',
        ':—', ': —', ':-',
    ]
    dialogue_score = sum(1 for p in dialogue_patterns if p in text)
    
    # Descriptive indicators - more extensive
    descriptive_patterns = [
        ' era ', ' estaba ', ' parecía ', ' tenía ',
        ' grande', ' pequeño', ' hermoso', ' oscuro',
        ' alto', ' bajo', ' largo', ' ancho',
        ' color', ' forma', ' aspecto', ' rostro',
        ' ojos ', ' manos ', ' cabello', ' piel ',
        ' brillante', ' suave', ' duro', ' frío', ' caliente',
        ' rojo', ' azul', ' verde', ' blanco', ' negro',
        ' luz ', ' sombra', ' silencio', ' ruido',
        ' viejo', ' joven', ' antiguo', ' nuevo',
    ]
    descriptive_score = sum(1 for p in descriptive_patterns if p in text_lower)
    
    # Poetic indicators - more extensive
    poetic_patterns = [
        ' cual ', ' como el ', ' como la ', ' cual si ',
        ' oh ', ' ay ', '¡oh', '¡ay', '¡ah',
        ' amor ', ' alma ', ' cielo ', ' tierra ',
        ' eterno', ' infinito', ' sublime', ' divino',
        ' corazón', ' suspiro', ' lágrima', ' sueño',
        ' estrella', ' luna ', ' sol ', ' mar ',
        ' muerte ', ' vida ', ' destino', ' tiempo',
        ' belleza', ' gloria', ' pasión',
    ]
    poetic_score = sum(1 for p in poetic_patterns if p in text_lower)
    
    # Lower thresholds to capture more variety
    if dialogue_score >= 1:  # Was 2
        return 'dialogue'
    elif poetic_score >= 1:  # Was 2
        return 'poetic'
    elif descriptive_score >= 1:  # Was 2
        return 'descriptive'
    else:
        return 'narrative'


def is_valid_phrase(text: str) -> bool:
    """Check if a phrase is valid for voice biometric use."""
    # Relaxed criteria to get more phrases
    if len(text) < 30 or len(text) > 500:
        return False
    
    words = text.split()
    if len(words) < 8:
        return False
    
    # Patterns to reject (only the most obvious problems)
    reject_patterns = [
        r'^\d+$', r'^\d+\s*$',
        r'^cap[íi]tulo\s+\d', r'^CAPÍTULO\s+\d',
        r'^índice', r'^ÍNDICE',
        r'^www\.', r'^http',
        r'^\[[\d\*]+\]',  # Footnotes
        r'^•', r'^-{3,}', r'^_{3,}', r'^\*{3,}',
        r'^Página\s+\d+',
        r'\d{6,}',  # Only reject very long numbers (ISBN, etc)
    ]
    
    # Patterns that indicate corruption anywhere in text (use re.search)
    corruption_patterns = [
        # Rayuela two-column corruption: intercalated page numbers like "34 116", "71 216"
        r'\b\d{2}\s+\d{2,3}\b(?!\s*(años|días|horas|metros|kilómetros|pesos|dólares|mil|hombres|mujeres|páginas))',
        # Rayuela merged words with impossible patterns
        r'\blen[a-z]+recía\b',  # like "lenparecía" 
        r'\b[a-z]+á[a-z]*crean\b',  # like "Conceptuácrean"
        r'\b[a-z]+á[a-z]*brimiento\b',  # merged discoveries
        r'\b[a-z]+degene[a-z]*familia\b',  # merged text
    ]
    
    text_lower = text.lower().strip()
    for pattern in reject_patterns:
        if re.match(pattern, text_lower, re.IGNORECASE):
            return False
    
    for pattern in corruption_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # Check for excessive special characters (more than 15%)
    special_chars = len(re.findall(r'[^\w\sáéíóúüñ¿¡.,;:!?\'\"()—–-]', text, re.IGNORECASE))
    if special_chars > len(text) * 0.15:
        return False
    
    # Check for excessive numbers (more than 25%)
    digits = len(re.findall(r'\d', text))
    if digits > len(text) * 0.25:
        return False
    
    # Must start with a letter or ¿¡«"
    if not re.match(r'^[A-ZÁÉÍÓÚÜÑa-záéíóúüñ¿¡«\"]', text):
        return False
    
    # Detect severe OCR artifacts only (4+ consecutive short words)
    short_word_streak = 0
    max_streak = 0
    for word in words:
        if len(word) <= 2 and word.isalpha():
            short_word_streak += 1
            max_streak = max(max_streak, short_word_streak)
        else:
            short_word_streak = 0
    
    if max_streak >= 4:
        return False
    
    # Detect Rayuela two-column corruption: malformed merged words
    # These are words with impossible Spanish letter combinations
    malformed_patterns = [
        r'\b\w+á[a-z]{2,}me\b',  # like "Conceptuácrean" - verb endings merged
        r'\b\w+[aeiou][bcdfghjklmnpqrstvwxyz]{4,}\w*\b',  # 4+ consonants together
        r'\b[a-záéíóúüñ]+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+\b',  # CamelCase in middle
        r'\b\w*[áéíóúü]\w*[áéíóúü]\w*[áéíóúü]\w*\b',  # 3+ accented vowels in one word
    ]
    for pattern in malformed_patterns:
        if re.search(pattern, text):
            return False
    
    return True


def clean_text(text: str) -> str:
    """Clean extracted text - remove PDF artifacts and preserve word spacing."""
    # Normalize whitespace but preserve word boundaries
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Fix hyphenated words split across lines (e.g., "Ma- condo" -> "Macondo")
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    
    # Fix soft hyphens (­) that split words across lines (e.g., "ciu­ dad" -> "ciudad")
    text = re.sub(r'(\w+)\u00ad\s*(\w+)', r'\1\2', text)
    
    # Fix OCR ligatures (common in scanned books)
    text = text.replace('ﬁ', 'fi')  # fi ligature
    text = text.replace('ﬂ', 'fl')  # fl ligature
    
    # Remove roman numerals at the start of text or after punctuation (chapter markers)
    text = re.sub(r'^[IVXLCDM]+\s+', '', text)
    text = re.sub(r'\.\s+[IVXLCDM]+\s+', '. ', text)
    # Remove standalone roman numerals followed by uppercase (like "IX El")
    text = re.sub(r'\b(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI{1,3}|XIV|XV|XVI{0,3}|XIX|XX)\s+([A-ZÁÉÍÓÚÜÑ])', r'\2', text)
    
    # Remove common PDF header/footer patterns
    pdf_artifacts = [
        # Book titles that appear as headers (these get mixed into text)
        r'Crónica de una muerte anunciada',  # Plain title - very common
        r'Cien años de soledad\s*[IVXLCDM]+\s*',  # With roman numerals
        r'Cien años de soledad',  # Plain title
        # Author + title combinations
        r'Gabriel García Márquez Cien años de soledad EDITADO POR[^.]*',
        r'Gabriel García Márquez Crónica de una muerte anunciada',
        r'Gabriel García Márquez \d+',
        # Julio Verne book headers
        r'JULIO VERNE\s*\d*',  # Author name with optional page number
        r'Veinte Mil Leguas de Viaje Submarino',  # Book title intercalated
        # Editorial headers
        r'EDITADO POR\s*"[^"]*"\s*Prólogo\s*[A-Za-z]+\s*[A-Za-z]+',
        r'EDITADO POR[^.]*',
        # University/website artifacts
        r'www\.philosophia\.cl / Escuelade Filosofía Universidad ARCIS\.?',
        r'www\.philosophia\.cl',
        r'/ Escuela de Filosofía Universidad ARCIS\.?',
        r'Escuela de Filosofía Universidad ARCIS\.?',
        # Lectulandia watermark (Sub-terra, etc)
        r'www\.lectulandia\.com\s*-?\s*',
        # Wikipedia and source URLs
        r'Fuente:\s*http[^\s]*\s*',
        r'http://es\.wikipedia\.org[^\s]*\s*',
        # Email addresses (e.g., contacto@pruebat.org)
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*',
        # Generic www URLs and book sites
        r'www\.\s*[A-Za-z0-9.-]+\.(com|org|net|ar|cl)[^\s]*\s*',
        r'Libros\s*Tauro[^.]*',
        # Editorial credits
        r'Título original:[^.]*\.?',
        r'Editor original:[^.]*\.?',
        r'Traducción:[^.]*\.?',
        r'Reservados todos los derechos\.?',
        # Page numbers
        r'Página \d+',
        r'página \d+',
        r'- \d+ -',
        r'\b\d{1,3}\s+—',  # Page number before em dash like "49 —"
        r'(?<=[a-záéíóúüñ])\d{1,3}\s+(?=[a-záéíóúüñ])',  # Page number splitting words like "cho76 rro"
        # Sub-sole and other books: page numbers in middle of text like "la 51 volví" or ", 20 bebió"
        r'(?<=[,;:\s])\s*\d{1,3}\s+(?=[a-záéíóúüñ])',  # After punctuation/space, before lowercase
        r'(?<=[a-záéíóúüñ])\s+\d{1,3}\s+(?=[a-záéíóúüñ])',  # Between two lowercase words
        # Chapter markers
        r'\b[IVXLCDM]+\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+\s+años\s+después',
        r'CAPÍTULO\s+[IVXLCDM]+\.?',  # CAPÍTULO VIII.
        r'capítulo\s+[ivxlcdm]+\s+\d+',  # capítulo i 29
        r'CAPITULO\s+',  # CAPITULO without number (intercalated header)
        r'CAPÍTULO\s+',  # CAPÍTULO without number
        # Page numbers at start of sentence (e.g., "122 El hombre")
        r'^\d{1,3}\s+(?=[A-ZÁÉÍÓÚÜÑ])',  # At line start before capital letter
        r'(?<=…\s)\d{1,3}\s+(?=[A-ZÁÉÍÓÚÜÑ])',  # After ellipsis before capital
        r'CAPÍTULO\s+[A-Z][a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+)*',  # CAPÍTULO El señor Thomas Marvel
        # Don Quijote page headers
        r'don quijote de la mancha\s+\d+',
        # Dan Brown book headers
        r'Dan Brown El código Da Vinci\s+\d+',
        # El jardín secreto headers
        r'El jardín secreto\s+\d+',
        # El Diario de Ana Frank headers/footers
        r'EL DIARIO DE ANA FRANK © Pehuén Editores, 2001\.',
        r'\)\d+\(',  # Inverted page numbers like )16(
        # El niño con el pijama de rayas
        r'John Boyne EL NIÑO CON EL PIJAMA DE RAYAS[^.]*',
        r'Queda rigurosamente prohibida[^.]*\.',
        # El Señor de los anillos headers
        r'El Señor de los anillos:\s*La Comunidad del anillo\s+\d+',
        # La guerra de los mundos section markers (letter + number)
        r'\b[A-Z]\s+\d{1,3}\b',  # Single letter + number like "E 94", "L 10"
        r'\blo\s+\d{1,3}\s+',  # "lo 8 difícil"
        # La Iliada verse numbers before quotes
        r'\d{1,4}\s+[«¿¡]',  # "824 «" or "502 ¿"
        r'[»"]\s+\d{1,4}\s+',  # "» 232 " after closing quote
        # La sombra del viento page headers
        r'Carlos Ruiz Zafón La sombra del viento de\s*\d*',
    ]
    
    for pattern in pdf_artifacts:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # Common OCR error corrections (Spanish specific)
    ocr_corrections = {
        # Verb conjugation errors (é instead of ó - past tense)
        ' lloré ': ' lloró ',
        ' experimenté ': ' experimentó ',
        ' reiteré ': ' reiteró ',
        ' concentré ': ' concentró ',
        ' exclamé ': ' exclamó ',
        ' murmuré ': ' murmuró ',
        ' susurré ': ' susurró ',
        ' pensé ': ' pensó ',
        ' sintié ': ' sintió ',
        ' decidié ': ' decidió ',
        ' descubrié ': ' descubrió ',
        ' comprendié ': ' comprendió ',
        ' contesté ': ' contestó ',
        # Common word errors
        '¿Can ': '¿Con ',
        '«¿Can ': '«¿Con ',
        ' can ': ' con ',
        ' qne ': ' que ',
        'desangraría': 'desangrarla',
        'desalentaría': 'desalentarlo',
        # Corrupted characters from OCR
        "le'contó": "le contó",
        "Ros¡": "Rosi",
        " 1a ": " la ",
        " tina ": " una ",
        " nosj ": " nos ",
        # Words split by page breaks
        "cho rro": "chorro",
        "histo ria": "historia",
        # Missing characters
        "ara tenía diez años": "Clara tenía diez años",
    }
    
    for wrong, correct in ocr_corrections.items():
        text = text.replace(wrong, correct)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Fix punctuation spacing
    text = re.sub(r'([.!?])\s*([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', text)
    
    return text


def extract_from_pdf(pdf_path: Path) -> list:
    """Extract phrases from a PDF file."""
    phrases = []
    seen = set()  # Avoid duplicates
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"   ❌ Error opening PDF: {e}")
        return phrases
    
    # Collect all text
    full_text = ""
    for page in doc:
        full_text += page.get_text() + " "
    
    doc.close()
    
    # Split by sentence-ending punctuation only
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    
    for sentence in sentences:
        cleaned = clean_text(sentence)
        if cleaned and cleaned not in seen and is_valid_phrase(cleaned):
            phrases.append(cleaned)
            seen.add(cleaned)
    
    return phrases


def main():
    """Main extraction function."""
    print("=" * 60)
    print("📚 PHRASE EXTRACTION TO TXT FILES")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Find all PDFs
    pdf_files = list(BOOKS_DIR.glob('*.pdf'))
    if not pdf_files:
        print(f"❌ No PDF files found in {BOOKS_DIR}")
        sys.exit(1)
    
    print(f"\n📖 Found {len(pdf_files)} PDF files")
    
    total_phrases = 0
    stats = {'easy': 0, 'medium': 0, 'hard': 0}
    
    for pdf_path in sorted(pdf_files):
        book_title = pdf_path.stem.replace('_', ' ')
        print(f"\n📕 Processing: {book_title}")
        
        phrases = extract_from_pdf(pdf_path)
        
        if not phrases:
            print(f"   ⚠️  No valid phrases extracted")
            continue
        
        # Calculate scores and filter by minimum phoneme score
        MIN_PHONEME_SCORE = 80  # Keep only phrases with high phonemic diversity
        
        scored_phrases = []
        for phrase in phrases:
            word_count = len(phrase.split())
            phoneme_score = calculate_phoneme_score(phrase)
            if phoneme_score >= MIN_PHONEME_SCORE:
                difficulty = classify_difficulty(word_count)
                style = detect_style(phrase)
                scored_phrases.append((phrase, word_count, phoneme_score, style, difficulty))
        
        if not scored_phrases:
            print(f"   ⚠️  No phrases passed quality filter")
            continue
        
        # Separate by style and limit narrative
        non_narrative = [p for p in scored_phrases if p[3] != 'narrative']
        narrative = [p for p in scored_phrases if p[3] == 'narrative']
        
        # Sort narrative by phoneme score and keep only top ones
        # Keep same proportion as other styles combined
        narrative.sort(key=lambda x: x[2], reverse=True)
        max_narrative = len(non_narrative)  # 1:1 ratio narrative:other
        narrative = narrative[:max_narrative]
        
        # Combine back
        scored_phrases = non_narrative + narrative
        
        if not scored_phrases:
            print(f"   ⚠️  No phrases after balancing")
            continue
        
        # Create output file
        output_file = OUTPUT_DIR / f"{pdf_path.stem}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title}\n")
            f.write(f"# Total frases: {len(scored_phrases)} (filtradas y balanceadas)\n")
            f.write("# ========================================\n\n")
            
            # Group by difficulty and sort by phoneme score descending
            grouped = {'easy': [], 'medium': [], 'hard': []}
            style_stats = {'narrative': 0, 'descriptive': 0, 'dialogue': 0, 'poetic': 0}
            
            for phrase, wc, ps, style, diff in scored_phrases:
                grouped[diff].append((phrase, wc, ps, style))
                style_stats[style] += 1
            
            # Sort each group by phoneme score descending
            for diff in grouped:
                grouped[diff].sort(key=lambda x: x[2], reverse=True)
            
            for diff in ['easy', 'medium', 'hard']:
                if grouped[diff]:
                    f.write(f"\n## {diff.upper()} ({len(grouped[diff])} frases)\n\n")
                    for i, (phrase, wc, ps, style) in enumerate(grouped[diff], 1):
                        # Format: [num] [phoneme_score|style] Phrase text
                        f.write(f"{i}. [{ps}|{style}] {phrase}\n\n")
                    stats[diff] += len(grouped[diff])
        
        print(f"   ✅ {len(scored_phrases)} frases → {output_file.name}")
        total_phrases += len(phrases)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"\n Total: {total_phrases} frases")
    print(f" • Easy:   {stats['easy']}")
    print(f" • Medium: {stats['medium']}")
    print(f" • Hard:   {stats['hard']}")
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print("\n✅ Done! Review the TXT files and correct any issues.")


if __name__ == "__main__":
    main()
