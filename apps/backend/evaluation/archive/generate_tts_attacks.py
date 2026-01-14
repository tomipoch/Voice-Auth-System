"""
Generador de Ataques TTS

Este script genera ataques TTS usando las frases identificadas en los recordings genuinos.
Cada usuario tendrá 15 ataques TTS que dicen las mismas frases que sus recordings.

Uso:
    python generate_tts_attacks.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List
import json

logger = logging.getLogger(__name__)


# FRASES POR USUARIO (corregidas manualmente)
PHRASES_PER_USER = {
    "anachamorromunoz": [
        "Un radio de sol poniente caía sobre el pie de la cama y daba sobre la chimenea, donde el agua hervía por botones.",
        "Súbitamente se vio un resplandor de luz y del pozo salió una cantidad de humo verde y luminoso entre bocanadas claramente visibles.",
        "El señor Cols tardaba en entender las cosas, pero ahora se daba cuenta de que allí pasaba algo.",
        "Nada de todo cuanto ha sido puesto y repuesto sobre el tapete en el anexo, puede mantenerse joven y fresco.",
        "Aunque ya había luz sobre la tierra, los ocultó Atenea con una oscura nube y raudamente lo sacó de la ciudad.",
        "No es decoroso que decaiga vuestro impetuoso valor, siendo como sois los más valientes del ejército.",
        "El obrero dirigió a lo alto una mirada despavorida y vio con espanto desprenderse pedazos de las paredes.",
        "Y tú, aunque sea poderoso, permanece tranquilo en la tercia parte que te pertenece.",
        "Mas el fugitivo no había contado con la frialdad del agua ni con la engañosa proximidad de la costa.",
        "Más adelante en el camino hacia Weybridge y el otro lado del puente, había un número de reclutas que estaban haciendo un largo terraplén.",
        "En la puerta de la cueva apareció una penosa escena a la opaca luz del crepúsculo que iluminaba aquel lugar.",
        "Se discutía, se diputaba, se negociaba la cotización de Philip Wood como uno de los fondos ingleses.",
        "En el fondo, sentado delante de una mesa, un hombre pequeño, ya entrado en años, hacía anotaciones en un enorme registro.",
    ],
    "ft_fernandotomas": [
        "y yo al verlos, no se irrito, porque habían obedecido con pesteza a las órdenes de Juno.",
        "La señora Hall abrió la puerta de Warenmpart para que entrara Mas luz ibara poder ver visitante con Claridad.",
        "La relación del calado encarga con la cabida ha sido mal calculada, y por consiguiente ofrecen al mar muy debil Resistencia.",
        "La.",
        "empecé a revolver entre aquella ropa , olvidándome de la agudeza de oído de aquel hombre",
        "Entonces Tom se ajustó al cinturón, por decirlo así, y se lanzó a la terea de aprender sus vestículos.",
        "En medio del dédalo pedregoso, que surcaba al fondo del Atlántico, el capitán Nemo avanzaba sin vacilaciones.",
        "Entretanto, Peter se había mudado para ir a vivir con un compañero mucho mayor que el.",
        "Entonces escuchó el astuto Odiseo unos pasos afuera, que advirtió que los perros no ladraban.",
        "La viuda, muy desesperada, lo buscó por todas partes durante cuarenta y ocho horas.",
        "pues si eres tu , en verdad, quien el asegura ,sabes que has nacido con funesto destino",
        "A pesar de esta carga que soportamos, muchos de nosotros siguen sobreviviendo: hay que creer que como proscritos los judíos se transformarán en un día en ejemplo.",
    ],
    "piapobletech": [
        "Ayudadme a todos, pues la obra de muchos siempre resulta mejor, cuatrocientos trece tales fueron sus palabras.",
        "Mi vecino opinaba que las tropas podrían capturar o destruir a los marcianos durante el transcurso del día.",
        "manifestado, Sirse se me preguntó que me ocurria, ¿Porque estás así mudo odiseo y no quieres probar estos manjares?",
        "el le hizo sufrir mucho hasta que halló un caño de agua corriente que estaba roto y del cual salía líquido como un manantial.",
        "Si lo veía a ella al asomarse la ventana en la mañana alegre y entonces.",
        "Para vengar a sus hijos, los titanes cuidaba y alimentaba desde hacia siglos a tifón el horror absoluto.",
        "A los lejos se elevaban las azuladas colinas de su rey y las torres del cristal Palace relucían como dos baras de plata.",
        "pero como no sabía a que quería el llegar espere nuevas preguntas , reservándome el responder de acuerdo con las circunstancias.",
        "vamos al comedor donde estaba servido al desayuno, señor Aronax, me dijo el capitán , le ruego que comparta desayuno sin cumplidos.",
        "A diez millas del nautilus hacia el sur se alzaba un islote solitario a una altura de doscientos metros.",
        "En ese instante siete tripulantes, mudos e impacibles como siempre, ascendieron a la plataforma.",
        "La haca marina, que se conoce también con el nombre Alicore, recordaba mucho al manati.",
    ],
    "rapomo3": [
        "Durante este tiempo, yo había reflexionado y una cierta esperanza vaga aún renacía mi corazón.",
        "Cada uno de los muchachos persibía una renta prodigiosa, Un dolar cada día laborable del año y medio Dolar los Domingos.",
        "Cada uno de estos mounstros tiene hocico de Marsopa, cabeza de lagarto, dientes de cocodrilo y por esto nos ha engañado.",
        "Sus casas eran pequeñas, y en ella solían vivir muchos hermanos, como en el caso de Marta, que eran doce.",
        "En ese momento, el capitán, sin preocuparse por mi presencia abrió el mueble semejante a una caja de caudales que encerraba gran número de lingotes.",
        "Escoge por compañero al que quieras, al mejor de los presentes, pues son muchos los que se ofrecen.",
        "Un Dia se lo mostró, a Él se estaba fuera de sí, pues no fue ninguno de los hombres que estábamos cerca.",
        "en cuanto a mí, distraído hasta entonces por los incidentes del viaje, habíame olvidado algo del porvenir, pero ahora sentí que la zosobra se apodera de mi nuevamente.",
        "No podía hacer otra cosa que esperar en la mayor inactividad durante esas cuarenta y ocho horas.",
        "Tanto en nuestra casa como en la escuela, se hablaba de temas sexuales, a veces con misterio, a veces con verguenza.",
        "La preplejidad y el desagrado del auditorio se manifestó en murmullos y provocó una reprimenda del tribunal.",
        "Entonces uno de ellos avanzó riendo hacia mí, llevando una guirnalda de bella flores que me eran desconocidas por completo y me la puso al cuello.",
    ],
}


class TTSAttackGenerator:
    """Generador de ataques TTS."""
    
    def __init__(self, dataset_base: Path):
        self.dataset_base = dataset_base
        self.attacks_dir = dataset_base / "attacks"
        
        # Configuración TTS
        self.tts_model = None
        self._load_tts_model()
    
    def _load_tts_model(self):
        """Cargar modelo TTS."""
        try:
            from gtts import gTTS
            from pydub import AudioSegment
            
            logger.info("Usando gTTS (Google Text-to-Speech) para español...")
            
            # gTTS no necesita cargar un modelo, se usa directamente
            self.tts_model = gTTS
            self.AudioSegment = AudioSegment
            
            logger.info("TTS listo para generar audios")
            
        except Exception as e:
            logger.error(f"Error inicializando TTS: {e}")
            raise
    
    def generate_attack(self, text: str, output_path: Path) -> bool:
        """
        Generar un archivo de ataque TTS.
        
        Args:
            text: Texto a sintetizar
            output_path: Ruta donde guardar el audio generado
        
        Returns:
            True si se generó exitosamente
        """
        try:
            logger.info(f"Generando: {output_path.name}")
            logger.debug(f"  Texto: {text[:50]}...")
            
            # Generar audio TTS con gTTS
            tts = self.tts_model(text=text, lang='es', slow=False)
            
            # Guardar como mp3 temporal
            temp_mp3 = output_path.with_suffix('.mp3')
            tts.save(str(temp_mp3))
            
            # Convertir a WAV 16kHz mono (formato requerido)
            audio = self.AudioSegment.from_mp3(str(temp_mp3))
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(str(output_path), format='wav')
            
            # Limpiar archivo temporal
            temp_mp3.unlink()
            
            logger.info(f"  ✓ Generado: {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error generando {output_path.name}: {e}")
            return False
    
    def distribute_phrases(self, phrases: List[str], num_attacks: int) -> List[str]:
        """
        Distribuir frases para generar num_attacks ataques de manera balanceada.
        
        Args:
            phrases: Lista de frases únicas
            num_attacks: Número total de ataques a generar
        
        Returns:
            Lista de frases repetidas para cubrir num_attacks
        """
        if not phrases:
            return []
        
        distributed = []
        phrases_per_attack = num_attacks // len(phrases)
        remaining = num_attacks % len(phrases)
        
        # Distribuir de manera balanceada
        for i, phrase in enumerate(phrases):
            count = phrases_per_attack + (1 if i < remaining else 0)
            distributed.extend([phrase] * count)
        
        return distributed
    
    def generate_user_attacks(self, user: str, phrases: List[str], num_attacks: int = 15) -> int:
        """
        Generar ataques TTS para un usuario.
        
        Args:
            user: Nombre del usuario
            phrases: Lista de frases a usar
            num_attacks: Número de ataques a generar (default: 15)
        
        Returns:
            Número de ataques generados exitosamente
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"Generando ataques TTS para: {user}")
        logger.info(f"{'='*100}")
        
        if not phrases:
            logger.warning(f"No hay frases para {user}")
            return 0
        
        # Crear directorio de usuario
        user_dir = self.attacks_dir / user
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Renombrar ataques TTS antiguos en lugar de eliminarlos
        old_attacks = list(user_dir.glob(f"{user}_tts_attack_*.wav"))
        if old_attacks:
            # Crear carpeta de backup
            backup_dir = user_dir / "old_tts_attacks"
            backup_dir.mkdir(exist_ok=True)
            
            logger.info(f"Moviendo {len(old_attacks)} ataques TTS antiguos a {backup_dir.name}/...")
            for attack in old_attacks:
                new_path = backup_dir / attack.name
                attack.rename(new_path)
        
        # Distribuir frases
        distributed_phrases = self.distribute_phrases(phrases, num_attacks)
        
        logger.info(f"Generando {num_attacks} ataques usando {len(phrases)} frases únicas...")
        
        # Generar ataques
        success_count = 0
        for i, text in enumerate(distributed_phrases, 1):
            output_path = user_dir / f"{user}_tts_attack_{i:02d}.wav"
            if self.generate_attack(text, output_path):
                success_count += 1
        
        logger.info(f"\n✅ Generados {success_count}/{num_attacks} ataques para {user}")
        return success_count
    
    def generate_all_attacks(self) -> Dict[str, int]:
        """
        Generar ataques TTS para todos los usuarios.
        
        Returns:
            Dict con número de ataques generados por usuario
        """
        results = {}
        
        for user, phrases in PHRASES_PER_USER.items():
            if not phrases:
                logger.warning(f"Saltando {user}: no hay frases definidas")
                continue
            
            success_count = self.generate_user_attacks(user, phrases, num_attacks=15)
            results[user] = success_count
        
        return results


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 100)
    print("GENERACIÓN DE ATAQUES TTS")
    print("=" * 100)
    print()
    
    # Configuración
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_base = project_root / "infra" / "evaluation" / "dataset"
    
    if not dataset_base.exists():
        print(f"❌ Error: Dataset no encontrado en {dataset_base}")
        sys.exit(1)
    
    # Verificar que hay frases definidas
    total_users_with_phrases = sum(1 for phrases in PHRASES_PER_USER.values() if phrases)
    if total_users_with_phrases == 0:
        print("❌ Error: No hay frases definidas para ningún usuario")
        print("\nEdita el archivo y agrega las frases corregidas en PHRASES_PER_USER")
        sys.exit(1)
    
    print(f"Usuarios con frases definidas: {total_users_with_phrases}/4")
    print()
    
    # Generar ataques
    generator = TTSAttackGenerator(dataset_base)
    results = generator.generate_all_attacks()
    
    # Resumen
    print(f"\n{'='*100}")
    print("RESUMEN DE GENERACIÓN")
    print(f"{'='*100}")
    
    total_generated = sum(results.values())
    total_expected = len([p for p in PHRASES_PER_USER.values() if p]) * 15
    
    for user, count in results.items():
        status = "✅" if count == 15 else "⚠️"
        print(f"{status} {user}: {count}/15 ataques generados")
    
    print(f"\nTotal: {total_generated}/{total_expected} ataques TTS generados")
    
    if total_generated == total_expected:
        print("\n✅ ¡Todos los ataques TTS generados exitosamente!")
    else:
        print(f"\n⚠️  Algunos ataques no se generaron correctamente")


if __name__ == "__main__":
    main()
