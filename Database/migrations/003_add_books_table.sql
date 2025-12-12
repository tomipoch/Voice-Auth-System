-- Migration 003: Add Books Table and Book References to Phrases
-- Created: 2025-12-11
-- Purpose: Add proper book metadata to phrases

-- =====================================================
-- 1. CREATE BOOKS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS books (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  author TEXT,
  filename TEXT NOT NULL UNIQUE,
  language TEXT NOT NULL DEFAULT 'es',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_books_filename ON books(filename);

-- =====================================================
-- 2. ADD BOOK_ID TO PHRASE TABLE
-- =====================================================

ALTER TABLE phrase ADD COLUMN IF NOT EXISTS book_id UUID REFERENCES books(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_phrase_book_id ON phrase(book_id);

-- =====================================================
-- 3. INSERT BOOK RECORDS
-- =====================================================

INSERT INTO books (title, author, filename, language) VALUES
  ('1984', 'George Orwell', '1984.pdf', 'es'),
  ('El Jardín Secreto', 'Frances Hodgson Burnett', 'EL_jardin_Secreto.pdf', 'es'),
  ('Edipo Rey', 'Sófocles', 'Edipo-Rey.pdf', 'es'),
  ('El Principito', 'Antoine de Saint-Exupéry', 'El-Principito.pdf', 'es'),
  ('El Diario de Ana Frank', 'Ana Frank', 'El-diario-de-ana-frank.pdf', 'es'),
  ('La Ilíada', 'Homero', 'La-Iliada-Homero.pdf', 'es'),
  ('La Odisea', 'Homero', 'La-Odisea-de-Homero.pdf', 'es'),
  ('La Guerra de los Mundos', 'H.G. Wells', 'La-guerra-de-los-mundos.pdf', 'es'),
  ('Sub Terra', 'Baldomero Lillo', 'Sub-terra.pdf', 'es'),
  ('Veinte Mil Leguas de Viaje Submarino', 'Julio Verne', 'Veinte mil leguas de viaje submarino.pdf', 'es'),
  ('Ben Quiere a Ana', 'Peter Härtling', 'ben-quiere-a-ana.pdf', 'es'),
  ('Charlie y la Fábrica de Chocolate', 'Roald Dahl', 'charly-y-la-fabrica-de-chocolate.pdf', 'es'),
  ('Dioses y Héroes de la Mitología', 'Anónimo', 'dioses-y-heroes-de-la-mitologia.pdf', 'es'),
  ('Don Quijote de la Mancha', 'Miguel de Cervantes', 'don-quijote-de-la-mancha.pdf', 'es'),
  ('El Caso del Futbolista Enmascarado', 'Alfredo Gómez Cerdá', 'el-caso-del-futbolista-enmascarado.pdf', 'es'),
  ('El Hombre Invisible', 'H.G. Wells', 'el-hombre-invisible.pdf', 'es'),
  ('El Niño del Pijama de Rayas', 'John Boyne', 'el-niño-del-pijama-de-rayas.pdf', 'es'),
  ('Frin', 'Luis María Pescetti', 'frin.pdf', 'es'),
  ('La Máquina del Tiempo', 'H.G. Wells', 'la-maquina-del-tiempo.pdf', 'es'),
  ('Las Aventuras de Tom Sawyer', 'Mark Twain', 'las-aventuras-de-tom-sawyer.pdf', 'es'),
  ('Lejos de Frin', 'Luis María Pescetti', 'lejos-de-frin.pdf', 'es'),
  ('Matilda', 'Roald Dahl', 'matilda.pdf', 'es'),
  ('Momo', 'Michael Ende', 'momo.pdf', 'es'),
  ('Sub Sole', 'Baldomero Lillo', 'sub-sole.pdf', 'es'),
  ('Viaje al Centro de la Tierra', 'Julio Verne', 'viaje_al_centro_de_la_tierra.pdf', 'es'),
  ('La Vuelta al Mundo en 80 Días', 'Julio Verne', 'vuelta-al-mundo-en-80-dias.pdf', 'es')
ON CONFLICT (filename) DO NOTHING;

-- =====================================================
-- 4. VERIFICATION QUERIES
-- =====================================================

-- Count books inserted
-- SELECT COUNT(*) as total_books FROM books;

-- Show all books
-- SELECT id, title, author, filename FROM books ORDER BY title;
