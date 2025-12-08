#!/usr/bin/env python3
"""
Script para extraer frases de archivos PDF y escribirlas en un archivo .txt para revisión.

Este script:
1. Lee archivos PDF de la carpeta Database/Libros/
2. Extrae el texto y lo divide en frases
3. Filtra frases apropiadas para verificación de voz
4. Las escribe en un archivo .txt para revisión manual

Uso:
    python scripts/extract_phrases_to_txt.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
    sys.exit(1)


class PhraseExtractor:
    """Extrae y procesa frases de archivos PDF."""

    def __init__(self, min_words: int = 20, max_words: int = 40):
        self.min_words = min_words
        self.max_words = max_words
        self.min_chars = 100
        self.max_chars = 600
        
        # Mapeo de caracteres corruptos
        self.char_replacements = {
            'Ø': 'é',
            'Æ': 'á',
            'æ': 'ñ',
            'œ': 'ú',
            '\u2019': "'",
            '«': '"',
            '»': '"',
        }

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrae todo el texto de un archivo PDF."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error al leer {pdf_path.name}: {e}")
        return text

    def clean_text(self, text: str) -> str:
        """Limpia el texto extraído de manera agresiva."""
        # Reemplazar caracteres corruptos
        for old_char, new_char in self.char_replacements.items():
            text = text.replace(old_char, new_char)
        
        # Reemplazar saltos de línea múltiples
        text = re.sub(r'\n+', ' ', text)
        
        # Eliminar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Eliminar números de página (números solos o con guiones/paréntesis)
        text = re.sub(r'\b\d+\s*[-–—]\s*\d+\b', '', text)  # Rangos como "45-67"
        text = re.sub(r'\(\d+\)', '', text)  # Números en paréntesis
        text = re.sub(r'^\d+\s+', '', text)  # Números al inicio
        text = re.sub(r'\s+\d+$', '', text)  # Números al final
        text = re.sub(r'\b(pág|página|page|p)\.\s*\d+', '', text, flags=re.IGNORECASE)
        
        # Eliminar referencias bibliográficas típicas
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\d{4}', '', text)  # Años
        
        return text.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        """Divide el texto en oraciones."""
        # Patrón para detectar fin de oración
        sentence_pattern = r'[.!?…]+[\s]+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def is_valid_phrase(self, phrase: str) -> bool:
        """Verifica si una frase es válida con filtros MUY estrictos."""
        # Contar palabras
        words = phrase.split()
        word_count = len(words)
        
        # Filtro estricto: 20-40 palabras
        if word_count < self.min_words or word_count > self.max_words:
            return False
        
        # Verificar longitud de caracteres
        char_count = len(phrase)
        if char_count < self.min_chars or char_count > self.max_chars:
            return False
        
        # Debe empezar con letra mayúscula
        if not phrase[0].isupper():
            return False
        
        # Rechazar si tiene demasiados números
        digit_count = sum(c.isdigit() for c in phrase)
        if digit_count > 3:  # Máximo 3 dígitos en total
            return False
        
        # Rechazar frases con muchos caracteres especiales
        special_chars = sum(1 for c in phrase if not c.isalnum() and not c.isspace())
        if special_chars / len(phrase) > 0.12:  # Máximo 12% de caracteres especiales
            return False
        
        # Debe contener suficientes letras
        letter_count = sum(c.isalpha() for c in phrase)
        if letter_count < char_count * 0.75:  # Al menos 75% letras
            return False
        
        # Rechazar si tiene guiones sospechosos (diálogos)
        if phrase.count('—') > 0 or phrase.count('–') > 1:
            return False
        
        # Rechazar si empieza con símbolos raros
        if phrase[0] in ['—', '–', '«', '»', '(', ')', '[', ']']:
            return False
        
        # Rechazar si contiene palabras muy cortas consecutivas (fragmentos)
        short_words = [w for w in words if len(w) <= 2]
        if len(short_words) > word_count * 0.3:  # Máximo 30% de palabras de 1-2 letras
            return False
        
        # Rechazar si tiene palabras sospechosamente largas (probablemente errores)
        if any(len(w) > 20 for w in words):
            return False
        
        # Rechazar si contiene muchas mayúsculas (probablemente títulos/encabezados)
        uppercase_count = sum(1 for c in phrase if c.isupper())
        if uppercase_count > len(phrase) * 0.15:  # Máximo 15% mayúsculas
            return False
        
        return True

    def calculate_difficulty(self, phrase: str) -> str:
        """Calcula la dificultad de una frase."""
        words = phrase.split()
        word_count = len(words)
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        # Para el rango 20-40, usamos medium y hard
        if word_count >= 30 or avg_word_length >= 8:
            return 'hard'
        else:
            return 'medium'

    def extract_phrases_from_pdf(self, pdf_path: Path) -> List[Tuple[str, str, int, int, str]]:
        """
        Extrae frases válidas de un PDF.
        
        Returns:
            Lista de tuplas (text, source, word_count, char_count, difficulty)
        """
        print(f"Procesando: {pdf_path.name}")
        
        # Extraer y limpiar texto
        raw_text = self.extract_text_from_pdf(pdf_path)
        clean_text = self.clean_text(raw_text)
        
        # Dividir en oraciones
        sentences = self.split_into_sentences(clean_text)
        
        # Filtrar frases válidas
        phrases = []
        source = pdf_path.stem  # Nombre del archivo sin extensión
        
        for sentence in sentences:
            if self.is_valid_phrase(sentence):
                words = sentence.split()
                word_count = len(words)
                char_count = len(sentence)
                difficulty = self.calculate_difficulty(sentence)
                
                phrases.append((
                    sentence,
                    source,
                    word_count,
                    char_count,
                    difficulty
                ))
        
        print(f"  Extraídas {len(phrases)} frases válidas de {len(sentences)} oraciones")
        return phrases


def write_phrases_to_file(phrases: List[Tuple[str, str, int, int, str]], output_path: Path):
    """Escribe las frases en un archivo de texto."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("FRASES EXTRAÍDAS PARA REVISIÓN\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total de frases: {len(phrases)}\n")
        f.write(f"Generado: {Path(__file__).name}\n\n")
        f.write("Formato: [DIFICULTAD] [PALABRAS] [CARACTERES] | FUENTE\n")
        f.write("Frase\n")
        f.write("-" * 80 + "\n\n")
        
        for i, (text, source, word_count, char_count, difficulty) in enumerate(phrases, 1):
            f.write(f"{i}. [{difficulty.upper()}] [{word_count} palabras] [{char_count} caracteres] | {source}\n")
            f.write(f"{text}\n\n")
    
    print(f"\n✅ Frases escritas en: {output_path}")


def main():
    """Función principal."""
    # Ruta a los PDFs
    books_dir = Path(__file__).parent.parent.parent / 'Database' / 'Libros'
    
    if not books_dir.exists():
        print(f"Error: No se encuentra el directorio {books_dir}")
        sys.exit(1)
    
    # Obtener archivos PDF
    pdf_files = list(books_dir.glob('*.pdf'))
    
    if not pdf_files:
        print(f"No se encontraron archivos PDF en {books_dir}")
        sys.exit(1)
    
    print(f"Encontrados {len(pdf_files)} archivos PDF")
    print("-" * 60)
    
    # Crear extractor
    extractor = PhraseExtractor(min_words=5, max_words=30)
    
    # Extraer frases de todos los PDFs
    all_phrases = []
    for pdf_path in pdf_files:
        phrases = extractor.extract_phrases_from_pdf(pdf_path)
        all_phrases.extend(phrases)
    
    print("-" * 60)
    print(f"Total de frases extraídas: {len(all_phrases)}")
    
    # Eliminar duplicados manteniendo el orden
    unique_phrases = []
    seen_texts = set()
    for phrase in all_phrases:
        if phrase[0] not in seen_texts:
            unique_phrases.append(phrase)
            seen_texts.add(phrase[0])
    
    print(f"Frases únicas: {len(unique_phrases)}")
    
    # Escribir a archivo
    output_path = Path(__file__).parent.parent.parent / 'frases_para_revision.txt'
    write_phrases_to_file(unique_phrases, output_path)
    
    print("-" * 60)
    print("Proceso completado exitosamente")
    print(f"\n📝 Revisa el archivo: {output_path}")
    print("   Después de revisar y corregir, puedes usar extract_phrases.py para insertar en BD")


if __name__ == '__main__':
    main()
