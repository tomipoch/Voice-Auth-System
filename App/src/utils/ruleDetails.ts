/**
 * Rule Details Helper
 * Provides detailed information about each phrase quality rule
 */

export interface RuleDetail {
  name: string;
  category: string;
  description: string;
  impact: string;
  recommendedRange: string;
  examples: string[];
  unit: string;
}

export const RULE_DETAILS: Record<string, RuleDetail> = {
  // Threshold Rules
  min_success_rate: {
    name: 'Tasa Mínima de Éxito',
    category: 'Calidad de Frases',
    description:
      'Define el porcentaje mínimo de verificaciones exitosas que debe tener una frase para mantenerse activa en el sistema.',
    impact:
      'Si una frase tiene una tasa de éxito menor a este valor, podría ser marcada como problemática y desactivada automáticamente.',
    recommendedRange: '0.60 - 0.80 (60% - 80%)',
    examples: [
      '0.70 = La frase debe tener al menos 70% de verificaciones exitosas',
      '0.80 = Más estricto, requiere 80% de éxito',
    ],
    unit: '%',
  },
  min_asr_score: {
    name: 'Score Mínimo de ASR',
    category: 'Reconocimiento de Voz',
    description:
      'Score mínimo de ASR (Automatic Speech Recognition) requerido para considerar que el audio fue reconocido correctamente.',
    impact:
      'Valores más altos aseguran mejor calidad de reconocimiento pero pueden rechazar audios válidos con ruido ambiental.',
    recommendedRange: '0.70 - 0.90 (70% - 90%)',
    examples: [
      '0.80 = Requiere 80% de confianza en el reconocimiento',
      '0.90 = Muy estricto, solo acepta audio muy claro',
    ],
    unit: 'Score',
  },
  min_phrase_ok_rate: {
    name: 'Tasa Mínima de Transcripción Correcta',
    category: 'Calidad de Frases',
    description:
      'Porcentaje mínimo de veces que la frase debe ser transcrita correctamente por el sistema ASR.',
    impact:
      'Frases con baja tasa de transcripción correcta pueden ser difíciles de pronunciar o ambiguas.',
    recommendedRange: '0.70 - 0.85 (70% - 85%)',
    examples: [
      '0.75 = La frase debe transcribirse correctamente al menos 75% de las veces',
      '0.85 = Más estricto, requiere frases muy claras',
    ],
    unit: '%',
  },
  min_attempts_for_analysis: {
    name: 'Intentos Mínimos para Análisis',
    category: 'Análisis de Datos',
    description:
      'Número mínimo de intentos de verificación necesarios antes de que el sistema analice la calidad de una frase.',
    impact:
      'Valores muy bajos pueden dar resultados no confiables. Valores muy altos retrasan la detección de frases problemáticas.',
    recommendedRange: '5 - 20 intentos',
    examples: [
      '10 = Analiza la frase después de 10 usos',
      '20 = Espera más datos antes de analizar',
    ],
    unit: 'intentos',
  },
  exclude_recent_phrases: {
    name: 'Excluir Frases Recientes',
    category: 'Seguridad',
    description:
      'Número de frases usadas recientemente por el usuario que se excluyen al generar nuevos challenges.',
    impact:
      'Previene que un usuario reciba la misma frase repetidamente, mejorando la seguridad contra ataques de replay.',
    recommendedRange: '30 - 100 frases',
    examples: [
      '50 = No repetir las últimas 50 frases usadas',
      '100 = Mayor variedad, no repetir las últimas 100',
    ],
    unit: 'frases',
  },

  // Rate Limit Rules
  max_challenges_per_user: {
    name: 'Máximo de Challenges Simultáneos',
    category: 'Límites de Tasa',
    description:
      'Número máximo de challenges activos que un usuario puede tener al mismo tiempo.',
    impact:
      'Previene abuso del sistema y limita el uso de recursos. Valores muy bajos pueden afectar la experiencia de usuario.',
    recommendedRange: '1 - 5 challenges',
    examples: [
      '3 = Usuario puede tener máximo 3 challenges activos',
      '5 = Más permisivo, permite hasta 5 challenges',
    ],
    unit: 'challenges',
  },
  max_challenges_per_hour: {
    name: 'Máximo de Challenges por Hora',
    category: 'Límites de Tasa',
    description:
      'Número máximo de challenges que un usuario puede crear en una hora.',
    impact:
      'Protege contra ataques de fuerza bruta y uso excesivo del sistema.',
    recommendedRange: '10 - 30 challenges/hora',
    examples: [
      '20 = Usuario puede crear máximo 20 challenges por hora',
      '30 = Más permisivo para usuarios legítimos',
    ],
    unit: 'challenges/hora',
  },

  // Cleanup Rules
  challenge_expiry_minutes: {
    name: 'Tiempo de Expiración de Challenge',
    category: 'Mantenimiento',
    description:
      'Minutos después de los cuales un challenge no usado expira automáticamente.',
    impact:
      'Valores muy cortos pueden frustrar a usuarios lentos. Valores muy largos acumulan challenges inactivos.',
    recommendedRange: '3 - 10 minutos',
    examples: [
      '5 = Challenge expira después de 5 minutos sin uso',
      '10 = Más tiempo para completar el challenge',
    ],
    unit: 'minutos',
  },
  cleanup_expired_after_hours: {
    name: 'Limpieza de Challenges Expirados',
    category: 'Mantenimiento',
    description:
      'Horas después de expirar que un challenge es eliminado permanentemente de la base de datos.',
    impact:
      'Mantiene la base de datos limpia. Valores muy cortos pueden dificultar auditorías.',
    recommendedRange: '1 - 24 horas',
    examples: [
      '1 = Elimina challenges expirados después de 1 hora',
      '24 = Mantiene por un día para auditoría',
    ],
    unit: 'horas',
  },
  cleanup_used_after_hours: {
    name: 'Limpieza de Challenges Usados',
    category: 'Mantenimiento',
    description:
      'Horas después de ser usado que un challenge es eliminado de la base de datos.',
    impact:
      'Balancea entre mantener historial y optimizar almacenamiento.',
    recommendedRange: '12 - 72 horas',
    examples: [
      '24 = Elimina challenges usados después de 24 horas',
      '72 = Mantiene por 3 días para análisis',
    ],
    unit: 'horas',
  },
};

/**
 * Get detailed information for a rule
 */
export const getRuleDetail = (ruleName: string): RuleDetail | null => {
  return RULE_DETAILS[ruleName] || null;
};

/**
 * Get category color for UI
 */
export const getCategoryColor = (category: string): string => {
  switch (category) {
    case 'Calidad de Frases':
      return 'text-blue-600 bg-blue-50';
    case 'Reconocimiento de Voz':
      return 'text-purple-600 bg-purple-50';
    case 'Análisis de Datos':
      return 'text-green-600 bg-green-50';
    case 'Seguridad':
      return 'text-red-600 bg-red-50';
    case 'Límites de Tasa':
      return 'text-yellow-600 bg-yellow-50';
    case 'Mantenimiento':
      return 'text-gray-600 bg-gray-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};
