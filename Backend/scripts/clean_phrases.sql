-- Script SQL para limpiar y mejorar frases
--  Elimina frases con problemas y limpia caracteres especiales

BEGIN;

-- 1. Eliminar frases con años (2001, 1944, etc.)
DELETE FROM phrase 
WHERE language = 'es' 
AND text ~ '\b(19|20)\d{2}\b';

-- 2. Eliminar frases con paréntesis y números
DELETE FROM phrase
WHERE language = 'es'
AND text ~ '\(\d+\)';

-- 3. Eliminar frases muy largas (más de 15 palabras)
DELETE FROM phrase
WHERE language = 'es'
AND word_count > 15;

-- 4. Eliminar frases con múltiples caracteres especiales corruptos
DELETE FROM phrase
WHERE language = 'es'
AND (
    text ~ 'Ø.*Ø.*Ø'  -- 3 o más Ø
    OR text ~ 'Æ.*Æ.*Æ'  -- 3 o más Æ
    OR LENGTH(text) - LENGTH(REPLACE(REPLACE(REPLACE(text, 'Ø', ''), 'Æ', ''), 'æ', '')) > 5
);

-- 5. Limpiar caracteres especiales en frases restantes
UPDATE phrase
SET text = (
    SELECT 
        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(text,
                'Ø', 'é'),  -- Ø → é
                'Æ', 'á'),  -- Æ → á
                'æ', 'ñ'),  -- æ → ñ
                'œ', 'ú'),  -- œ → ú
                '«', '"'),  -- « → "
                '»', '"'),  -- » → "
                E'\u2019', ''''),  -- ' → '
                '  ', ' ')  -- doble espacio → simple
)
WHERE language = 'es'
AND (text LIKE '%Ø%' OR text LIKE '%Æ%' OR text LIKE '%æ%' OR text LIKE '%œ%' OR text LIKE '%«%' OR text LIKE '%»%');

-- 6. Eliminar espacios extra al inicio y final
UPDATE phrase
SET text = TRIM(text)
WHERE language = 'es';

-- Mostrar estadísticas finales
SELECT 
    difficulty,
    COUNT(*) as total,
    AVG(word_count) as avg_words
FROM phrase
WHERE language = 'es'
GROUP BY difficulty
ORDER BY difficulty;

COMMIT;
