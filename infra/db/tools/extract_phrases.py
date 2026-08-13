#!/usr/bin/env python3
"""
Extract phrases from PDF books into TXT files for manual review.

Pipeline de frases reproducible (para usuarios externos sin la BD de libros):
    1. Coloque sus libros .pdf en infra/db/Libros/
    2. (Opcional) python infra/db/tools/register_books.py   -> registra los libros en BD
    3. python infra/db/tools/extract_phrases.py             -> genera TXT en frases_por_libro/
    4. Revise/ordene los TXT (formato ## EASY/MEDIUM/HARD + "N. [score|style] frase")
    5. python infra/db/tools/import_phrases_from_txt.py     -> importa a la tabla phrase

No requiere base de datos: solo los PDFs. No reemplaza TXT existentes a menos que
se pase --force.

Usage:
    python extract_phrases.py [--output-dir DIR] [--min-phoneme-score N] [--force]
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
SCRIPT_DIR = Path(__file__).resolve().parent.parent  # infra/db
BOOKS_DIR = SCRIPT_DIR / 'Libros'
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / 'frases_por_libro'

# Spanish phonemes for diversity calculation
SPANISH_VOWELS = set('aeiouáéíóúü')
SPANISH_CONSONANTS = set('bcdfghjklmnñpqrstvwxyz')
SPANISH_SPECIAL_PHONEMES = ['ch', 'll', 'rr', 'ñ', 'qu', 'gu']

MIN_PHONEME_SCORE = 80


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

    if dialogue_score >= 1:
        return 'dialogue'
    elif poetic_score >= 1:
        return 'poetic'
    elif descriptive_score >= 1:
        return 'descriptive'
    else:
        return 'narrative'


def is_valid_phrase(text: str) -> bool:
    """Check if a phrase is valid for voice biometric use."""
    if len(text) < 30 or len(text) > 500:
        return False

    words = text.split()
    if len(words) < 8:
        return False

    reject_patterns = [
        r'^\d+$', r'^\d+\s*$',
        r'^cap[íi]tulo\s+\d', r'^CAPÍTULO\s+\d',
        r'^índice', r'^ÍNDICE',
        r'^www\.', r'^http',
        r'^\[[\d\*]+\]',  # Footnotes
        r'^•', r'^-{3,}', r'^_{3,}', r'^\*{3,}',
        r'^Página\s+\d+',
        r'\d{6,}',  # ISBNs and other long numbers
    ]

    # Patterns that indicate corruption anywhere in text (use re.search)
    corruption_patterns = [
        r'\b\d{2}\s+\d{2,3}\b(?!\s*(años|días|horas|metros|kilómetros|pesos|dólares|mil|hombres|mujeres|páginas))',
        r'\blen[a-z]+recía\b',
        r'\b[a-z]+á[a-z]*crean\b',
        r'\b[a-z]+á[a-z]*brimiento\b',
        r'\b[a-z]+degene[a-z]*familia\b',
    ]

    text_lower = text.lower().strip()
    for pattern in reject_patterns:
        if re.match(pattern, text_lower, re.IGNORECASE):
            return False

    for pattern in corruption_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # Excessive special characters (more than 15%)
    special_chars = len(re.findall(r'[^\w\sáéíóúüñ¿¡.,;:!?\'\"()—–-]', text, re.IGNORECASE))
    if special_chars > len(text) * 0.15:
        return False

    # Excessive numbers (more than 25%)
    digits = len(re.findall(r'\d', text))
    if digits > len(text) * 0.25:
        return False

    # Must start with a letter or ¿¡«"
    if not re.match(r'^[A-ZÁÉÍÓÚÜÑa-záéíóúüñ¿¡«\"]', text):
        return False

    # Severe OCR artifacts: 4+ consecutive short words
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

    # Malformed merged words (two-column corruption)
    malformed_patterns = [
        r'\b\w+á[a-z]{2,}me\b',
        r'\b\w+[aeiou][bcdfghjklmnpqrstvwxyz]{4,}\w*\b',
        r'\b[a-záéíóúüñ]+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+\b',
        r'\b\w*[áéíóúü]\w*[áéíóúü]\w*[áéíóúü]\w*\b',
    ]
    for pattern in malformed_patterns:
        if re.search(pattern, text):
            return False

    return True


def clean_text(text: str) -> str:
    """Clean extracted text - remove PDF artifacts and preserve word spacing."""
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Fix hyphenated words split across lines (e.g., "Ma- condo" -> "Macondo")
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

    # Fix soft hyphens (­) that split words across lines (e.g., "ciu­ dad" -> "ciudad")
    text = re.sub(r'(\w+)\u00ad\s*(\w+)', r'\1\2', text)

    # Fix OCR ligatures
    text = text.replace('ﬁ', 'fi')
    text = text.replace('ﬂ', 'fl')

    # Remove roman numerals at start of text or after punctuation (chapter markers)
    text = re.sub(r'^[IVXLCDM]+\s+', '', text)
    text = re.sub(r'\.\s+[IVXLCDM]+\s+', '. ', text)
    text = re.sub(r'\b(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI{1,3}|XIV|XV|XVI{0,3}|XIX|XX)\s+([A-ZÁÉÍÓÚÜÑ])', r'\2', text)

    pdf_artifacts = [
        r'Crónica de una muerte anunciada',
        r'Cien años de soledad\s*[IVXLCDM]+\s*',
        r'Cien años de soledad',
        r'Gabriel García Márquez Cien años de soledad EDITADO POR[^.]*',
        r'Gabriel García Márquez Crónica de una muerte anunciada',
        r'Gabriel García Márquez \d+',
        r'JULIO VERNE\s*\d*',
        r'Veinte Mil Leguas de Viaje Submarino',
        r'EDITADO POR\s*"[^"]*"\s*Prólogo\s*[A-Za-z]+\s*[A-Za-z]+',
        r'EDITADO POR[^.]*',
        r'www\.philosophia\.cl / Escuelade Filosofía Universidad ARCIS\.?',
        r'www\.philosophia\.cl',
        r'/ Escuela de Filosofía Universidad ARCIS\.?',
        r'Escuela de Filosofía Universidad ARCIS\.?',
        r'www\.lectulandia\.com\s*-?\s*',
        r'Fuente:\s*http[^\s]*\s*',
        r'http://es\.wikipedia\.org[^\s]*\s*',
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*',
        r'www\.\s*[A-Za-z0-9.-]+\.(com|org|net|ar|cl)[^\s]*\s*',
        r'Libros\s*Tauro[^.]*',
        r'Título original:[^.]*\.?',
        r'Editor original:[^.]*\.?',
        r'Traducción:[^.]*\.?',
        r'Reservados todos los derechos\.?',
        r'Página \d+',
        r'página \d+',
        r'- \d+ -',
        r'\b\d{1,3}\s+—',
        r'(?<=[a-záéíóúüñ])\d{1,3}\s+(?=[a-záéíóúüñ])',
        r'(?<=[,;:\s])\s*\d{1,3}\s+(?=[a-záéíóúüñ])',
        r'(?<=[a-záéíóúüñ])\s+\d{1,3}\s+(?=[a-záéíóúüñ])',
        r'\b[IVXLCDM]+\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+\s+años\s+después',
        r'CAPÍTULO\s+[IVXLCDM]+\.?',
        r'capítulo\s+[ivxlcdm]+\s+\d+',
        r'CAPITULO\s+',
        r'CAPÍTULO\s+',
        r'^\d{1,3}\s+(?=[A-ZÁÉÍÓÚÜÑ])',
        r'(?<=…\s)\d{1,3}\s+(?=[A-ZÁÉÍÓÚÜÑ])',
        r'CAPÍTULO\s+[A-Z][a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+)*',
        r'don quijote de la mancha\s+\d+',
        r'Dan Brown El código Da Vinci\s+\d+',
        r'El jardín secreto\s+\d+',
        r'EL DIARIO DE ANA FRANK © Pehuén Editores, 2001\.',
        r'\)\d+\(',
        r'John Boyne EL NIÑO CON EL PIJAMA DE RAYAS[^.]*',
        r'Queda rigurosamente prohibida[^.]*\.',
        r'El Señor de los anillos:\s*La Comunidad del anillo\s+\d+',
        r'\b[A-Z]\s+\d{1,3}\b',
        r'\blo\s+\d{1,3}\s+',
        r'\d{1,4}\s+[«¿¡]',
        r'[»"]\s+\d{1,4}\s+',
        r'Carlos Ruiz Zafón La sombra del viento de\s*\d*',
    ]

    for pattern in pdf_artifacts:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)

    # Common OCR error corrections (Spanish specific)
    ocr_corrections = {
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
        '¿Can ': '¿Con ',
        '«¿Can ': '«¿Con ',
        ' can ': ' con ',
        ' qne ': ' que ',
        'desangraría': 'desangrarla',
        'desalentaría': 'desalentarlo',
        "le'contó": "le contó",
        "Ros¡": "Rosi",
        " 1a ": " la ",
        " tina ": " una ",
        " nosj ": " nos ",
        "cho rro": "chorro",
        "histo ria": "historia",
        "ara tenía diez años": "Clara tenía diez años",
    }
    for wrong, correct in ocr_corrections.items():
        text = text.replace(wrong, correct)

    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'([.!?])\s*([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', text)

    return text


def extract_from_pdf(pdf_path: Path) -> list:
    """Extract phrases from a PDF file."""
    phrases = []
    seen = set()

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"   ❌ Error opening PDF: {e}")
        return phrases

    full_text = ""
    for page in doc:
        full_text += page.get_text() + " "
    doc.close()

    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    for sentence in sentences:
        cleaned = clean_text(sentence)
        if cleaned and cleaned not in seen and is_valid_phrase(cleaned):
            phrases.append(cleaned)
            seen.add(cleaned)

    return phrases


def main(output_dir: Path = DEFAULT_OUTPUT_DIR, min_phoneme_score: int = MIN_PHONEME_SCORE, force: bool = False):
    """Main extraction function."""
    print("=" * 60)
    print("📚 PHRASE EXTRACTION TO TXT FILES")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(BOOKS_DIR.glob('*.pdf'))
    if not pdf_files:
        print(f"❌ No PDF files found in {BOOKS_DIR}")
        print("   Coloque sus libros .pdf ahí y vuelva a ejecutar.")
        sys.exit(1)

    print(f"\n📖 Found {len(pdf_files)} PDF files")

    stats = {'easy': 0, 'medium': 0, 'hard': 0}
    skipped = []

    for pdf_path in sorted(pdf_files):
        book_title = pdf_path.stem.replace('_', ' ')
        output_file = output_dir / f"{pdf_path.stem}.txt"

        if output_file.exists() and not force:
            skipped.append(str(output_file))
            continue

        print(f"\n📕 Processing: {book_title}")

        phrases = extract_from_pdf(pdf_path)
        if not phrases:
            print(f"   ⚠️  No valid phrases extracted")
            continue

        scored_phrases = []
        for phrase in phrases:
            word_count = len(phrase.split())
            phoneme_score = calculate_phoneme_score(phrase)
            if phoneme_score >= min_phoneme_score:
                difficulty = classify_difficulty(word_count)
                style = detect_style(phrase)
                scored_phrases.append((phrase, word_count, phoneme_score, style, difficulty))

        if not scored_phrases:
            print(f"   ⚠️  No phrases passed quality filter")
            continue

        # Balance narrative vs other styles (1:1)
        non_narrative = [p for p in scored_phrases if p[3] != 'narrative']
        narrative = [p for p in scored_phrases if p[3] == 'narrative']
        narrative.sort(key=lambda x: x[2], reverse=True)
        max_narrative = len(non_narrative)
        narrative = narrative[:max_narrative]
        scored_phrases = non_narrative + narrative

        if not scored_phrases:
            print(f"   ⚠️  No phrases after balancing")
            continue

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title}\n")
            f.write(f"# Total frases: {len(scored_phrases)} (filtradas y balanceadas)\n")
            f.write("# ========================================\n\n")

            grouped = {'easy': [], 'medium': [], 'hard': []}
            style_stats = {'narrative': 0, 'descriptive': 0, 'dialogue': 0, 'poetic': 0}

            for phrase, wc, ps, style, diff in scored_phrases:
                grouped[diff].append((phrase, wc, ps, style))
                style_stats[style] += 1

            for diff in grouped:
                grouped[diff].sort(key=lambda x: x[2], reverse=True)

            for diff in ['easy', 'medium', 'hard']:
                if grouped[diff]:
                    f.write(f"\n## {diff.upper()} ({len(grouped[diff])} frases)\n\n")
                    for i, (phrase, wc, ps, style) in enumerate(grouped[diff], 1):
                        f.write(f"{i}. [{ps}|{style}] {phrase}\n\n")
                    stats[diff] += len(grouped[diff])

        print(f"   ✅ {len(scored_phrases)} frases → {output_file.name}")

    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"\n • Easy:   {stats['easy']}")
    print(f" • Medium: {stats['medium']}")
    print(f" • Hard:   {stats['hard']}")
    print(f"\n📁 Output directory: {output_dir}")
    if skipped:
        print(f"\n⏭️  {len(skipped)} archivo(s) ya existente(s) no reemplazado(s) (use --force para regenerar):")
        for s in skipped:
            print(f"   - {s}")
    print("\n✅ Done! Review the TXT files and correct any issues.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Directorio de salida (default: infra/db/frases_por_libro)")
    parser.add_argument("--min-phoneme-score", type=int, default=MIN_PHONEME_SCORE,
                        help="Score fonémico mínimo para conservar una frase (default: 80)")
    parser.add_argument("--force", action="store_true",
                        help="Regenerar/sobrescribir TXT existentes (default: no pisa)")
    args = parser.parse_args()
    main(output_dir=args.output_dir, min_phoneme_score=args.min_phoneme_score, force=args.force)