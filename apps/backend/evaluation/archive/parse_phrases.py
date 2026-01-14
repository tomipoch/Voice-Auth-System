"""
Parser para extraer las frases del reporte de verificación del dataset.
"""
from pathlib import Path
from typing import Dict
import re


def parse_phrases_from_report(report_file: Path) -> Dict[str, str]:
    """
    Parse el archivo dataset_verification_report.txt y extrae las frases asociadas a cada archivo.
    
    Returns:
        Dict[filename, expected_phrase]
    """
    phrases = {}
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar secciones de DETALLE DE RECORDINGS y ATAQUES DE CLONING
    # Patrón: nombre_archivo.wav\n  -> "frase"
    pattern = r'([a-z_0-9]+\.wav)\n\s+-> "(.+?)"'
    
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    
    for filename, phrase in matches:
        # Limpiar la frase (remover saltos de línea internos)
        phrase_cleaned = phrase.replace('\n', ' ').strip()
        phrases[filename] = phrase_cleaned
    
    return phrases


def normalize_text(text: str) -> str:
    """
    Normaliza texto para comparación (lowercase, sin puntuación extra).
    """
    import string
    
    # Lowercase
    text = text.lower()
    
    # Remover puntuación excesiva pero mantener espacios
    text = text.replace(',', ' ')
    text = text.replace('.', ' ')
    text = text.replace('¿', ' ')
    text = text.replace('?', ' ')
    text = text.replace(':', ' ')
    text = text.replace(';', ' ')
    
    # Normalizar espacios múltiples
    text = ' '.join(text.split())
    
    return text


if __name__ == "__main__":
    # Test
    report_file = Path("evaluation/results/dataset_verification_report.txt")
    phrases = parse_phrases_from_report(report_file)
    
    print(f"Total frases extraídas: {len(phrases)}")
    print("\nEjemplos:")
    for i, (filename, phrase) in enumerate(list(phrases.items())[:5]):
        print(f"\n{filename}")
        print(f"  -> {phrase[:100]}...")
