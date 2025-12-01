#!/usr/bin/env python3
"""
Script para generar frases de calidad para verificación biométrica.

Genera frases coherentes de 20-40 palabras en español.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import asyncpg
from dotenv import load_dotenv

# Templates de frases para generar contenido coherente
PHRASE_TEMPLATES = [
    # Tecnología y ciencia
    "La inteligencia artificial y el aprendizaje automático están revolucionando la forma en que las empresas analizan grandes cantidades de datos para tomar decisiones más informadas y eficientes en tiempo real",
    "Los avances en biotecnología permiten desarrollar tratamientos personalizados basados en el perfil genético de cada paciente, lo que representa un cambio paradigmático en la medicina moderna y preventiva",
    "La computación cuántica promete resolver problemas matemáticos complejos que las computadoras tradicionales tardarían miles de años en procesar, abriendo nuevas fronteras en la investigación científica y el desarrollo tecnológico",
    "Las energías renovables como la solar y la eólica se están convirtiendo en alternativas cada vez más viables y económicas frente a los combustibles fósiles tradicionales",
    "Los vehículos autónomos utilizan sensores avanzados y algoritmos de inteligencia artificial para navegar de forma segura por las calles sin intervención humana directa",
    
    # Negocios y economía
    "El comercio electrónico ha transformado radicalmente la manera en que los consumidores compran productos y servicios, permitiendo transacciones globales instantáneas desde cualquier dispositivo conectado a internet",
    "La economía colaborativa está cambiando los modelos tradicionales de negocio al permitir que las personas compartan recursos como vehículos, hogares y herramientas de trabajo",
    "Las criptomonedas y la tecnología blockchain están redefiniendo los sistemas financieros tradicionales al ofrecer alternativas descentralizadas para realizar transacciones seguras sin intermediarios bancarios",
    "El análisis de datos masivos permite a las empresas comprender mejor el comportamiento de sus clientes y personalizar sus estrategias de marketing de manera más efectiva",
    "La globalización económica ha creado mercados interconectados donde las decisiones financieras en un país pueden tener repercusiones inmediatas en economías de todo el mundo",
    
    # Cultura y sociedad
    "Las redes sociales han revolucionado la comunicación interpersonal y se han convertido en plataformas fundamentales para el intercambio de información, opiniones y contenidos multimedia",
    "La diversidad cultural enriquece las sociedades modernas al permitir el intercambio de tradiciones, gastronomía, arte y perspectivas únicas que fomentan la comprensión y el respeto mutuo",
    "El cambio climático representa uno de los desafíos más urgentes para la humanidad, requiriendo acción coordinada a nivel global para reducir las emisiones y proteger los ecosistemas",
    "La educación en línea ha democratizado el acceso al conocimiento al permitir que personas de cualquier parte del mundo puedan tomar cursos y obtener títulos",
    "Las ciudades inteligentes utilizan sensores y  tecnología de internet de las cosas para optimizar el uso de recursos, mejorar servicios públicos y reducir el impacto ambiental",
    
    # Salud y bienestar  
    "El ejercicio regular y una alimentación balanceada son fundamentales para mantener un estilo de vida saludable y prevenir enfermedades crónicas como la diabetes y las afecciones cardiovasculares",
    "La telemedicina permite que los pacientes reciban consultas médicas y seguimiento de tratamientos sin necesidad de desplazarse a instalaciones hospitalarias, mejorando el acceso a servicios de salud",
    "La meditación y las técnicas de mindfulness han demostrado ser efectivas para reducir el estrés, mejorar la concentración y promover el bienestar mental en la vida cotidiana",
    "Los avances en medicina regenerativa permiten cultivar tejidos y órganos en laboratorio, abriendo nuevas posibilidades para trasplantes y tratamientos de enfermedades degenerativas",
    "La salud mental es tan importante como la salud física y requiere atención profesional cuando se presentan síntomas de ansiedad, depresión u otros trastornos psicológicos",
    
    # Historia y geografía
    "Las antiguas civilizaciones de América Latina, como los mayas y los incas, desarrollaron complejos sistemas astronómicos, arquitectónicos y agrícolas que siguen asombrando a los investigadores modernos",
    "La revolución industrial del siglo diecinueve transformó radicalmente las sociedades agrarias en economías industrializadas, cambiando para siempre la forma en que las personas trabajaban y vivían",
    "Los océanos cubren aproximadamente el setenta por ciento de la superficie terrestre y albergan una biodiversidad increíble que incluye millones de especies aún por descubrir por la ciencia",
    "Las montañas más altas del mundo se encuentran en la cordillera del Himalaya, donde el monte Everest alcanza una altitud de más de ocho mil metros",
    "El bosque amazónico es conocido como el pulmón del planeta debido a su capacidad para producir oxígeno y absorber grandes cantidades de dióxido de carbono",
    
    # Arte y literatura
    "La literatura latinoamericana del siglo veinte produjo obras maestras del realismo mágico que combinaron elementos fantásticos con narrativas profundamente arraigadas en la realidad social y política",
    "La pintura impresionista del siglo diecinueve revolucionó el arte al capturar la luz y el color de manera innovadora, alejándose de las técnicas académicas tradicionales",
    "El cine ha evolucionado desde sus inicios en blanco y negro hasta convertirse en una forma de arte compleja que combina narrativa visual, actuación y efectos especiales",
    "La música clásica de compositores como Beethoven y Mozart continúa siendo interpretada y apreciada en salas de concierto alrededor del mundo después de siglos",
    "La arquitectura moderna busca equilibrar la funcionalidad con la estética, creando espacios que sean tanto prácticos como visualmente impactantes para sus ocupantes",
    
    # Medio ambiente
    "La deforestación de los bosques tropicales no solo destruye hábitats naturales sino que también contribuye significativamente al cambio climático global al liberar grandes cantidades de carbono",
    "Los océanos están enfrentando graves amenazas debido a la contaminación por plásticos, la acidificación y el aumento de temperaturas causado por el calentamiento global",
    "La conservación de especies en peligro de extinción requiere esfuerzos coordinados internacionales que incluyan la protección de hábitats y la regulación de la caza ilegal",
    "El reciclaje y la reducción del consumo de recursos son prácticas esenciales para minimizar el impacto ambiental y promover la sostenibilidad a largo plazo",
    "Las energías limpias como la solar y la eólica son cada vez más competitivas económicamente frente a los combustibles fósiles tradicionales y contaminantes",
    
    # Filosofía y pensamiento
    "La ética profesional implica actuar con integridad, honestidad y responsabilidad en todas las decisiones que afectan a colegas, clientes y la sociedad en general",
    "El pensamiento crítico es una habilidad fundamental que permite analizar información de manera objetiva, evaluar argumentos y tomar decisiones informadas basadas en evidencia sólida",
    "La empatía nos permite comprender las experiencias y emociones de otras personas, facilitando la construcción de relaciones interpersonales más profundas y significativas",
    "La libertad de expresión es un derecho fundamental en las sociedades democráticas, pero debe ejercerse con responsabilidad y respeto hacia los demás individuos",
    "El aprendizaje continuo a lo largo de la vida es esencial en un mundo que cambia rápidamente, donde nuevas tecnologías y conocimientos emergen constantemente",
]

def count_words(text: str) -> int:
    """Cuenta las palabras en un texto."""
    return len(text.split())

def calculate_difficulty(word_count: int) -> str:
    """Calcula la dificultad basándose en el número de palabras."""
    if word_count >= 30:
        return 'hard'
    else:
        return 'medium'

async def store_phrases_in_db(phrases: List[Tuple[str, int, int, str]], conn: asyncpg.Connection):
    """Almacena las frases en la base de datos."""
    
    insert_query = """
        INSERT INTO phrase (text, source, word_count, char_count, difficulty, language, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT DO NOTHING
    """
    
    inserted_count = 0
    for text, word_count, char_count, difficulty in phrases:
        try:
            await conn.execute(
                insert_query,
                text,
                'generated',  # source
                word_count,
                char_count,
                difficulty,
                'es',
                True
            )
            inserted_count += 1
        except Exception as e:
            print(f"Error al insertar frase: {e}")
            continue
    
    return inserted_count

async def main():
    """Función principal."""
    # Cargar variables de entorno
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    
    # Configurar base de datos
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'voice_biometrics')
    db_user = os.getenv('DB_USER', 'voice_user')
    db_password = os.getenv('DB_PASSWORD', 'voice_password')
    
    print("=" * 60)
    print("GENERADOR DE FRASES DE CALIDAD PARA VERIFICACIÓN BIOMÉTRICA")
    print("=" * 60)
    
    # Procesar frases
    phrases = []
    for text in PHRASE_TEMPLATES:
        word_count = count_words(text)
        char_count = len(text)
        difficulty = calculate_difficulty(word_count)
        
        # Validar que esté en el rango correcto
        if 20 <= word_count <= 40:
            phrases.append((text, word_count, char_count, difficulty))
            print(f"✓ {difficulty.upper():6} ({word_count:2} palabras): {text[:60]}...")
        else:
            print(f"✗ RECHAZADA ({word_count} palabras - fuera de rango 20-40)")
    
    print("-" * 60)
    print(f"Frases válidas: {len(phrases)}")
    
    # Conectar a la base de datos
    print("-" * 60)
    print("Conectando a la base de datos...")
    
    try:
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        print("Conexión exitosa. Insertando frases...")
        
        # Almacenar frases
        inserted = await store_phrases_in_db(phrases, conn)
        
        print(f"✓ Insertadas {inserted} frases en la base de datos")
        
        # Mostrar estadísticas
        stats = await conn.fetch("""
            SELECT difficulty, COUNT(*) as count, AVG(word_count) as avg_words
            FROM phrase
            WHERE language = 'es'
            GROUP BY difficulty
            ORDER BY difficulty
        """)
        
        print("-" * 60)
        print("ESTADÍSTICAS FINALES:")
        for row in stats:
            print(f"  {row['difficulty'].upper():6}: {row['count']:3} frases (promedio: {row['avg_words']:.1f} palabras)")
        
        # Cerrar conexión
        await conn.close()
        
        print("=" * 60)
        print("✓ Proceso completado exitosamente")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error de base de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
