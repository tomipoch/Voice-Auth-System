-- Migration 005: Add Phoneme Score and Style to Phrases
-- Created: 2026-01-02
-- Purpose: Add phonemic diversity scoring and style classification for voice biometrics

-- =====================================================
-- 1. ADD NEW COLUMNS TO PHRASE TABLE
-- =====================================================

ALTER TABLE phrase ADD COLUMN IF NOT EXISTS phoneme_score INTEGER DEFAULT 0;
ALTER TABLE phrase ADD COLUMN IF NOT EXISTS style TEXT CHECK (style IN ('narrative', 'descriptive', 'dialogue', 'poetic'));

-- =====================================================
-- 2. CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_phrase_phoneme_score ON phrase(phoneme_score);
CREATE INDEX IF NOT EXISTS idx_phrase_style ON phrase(style);

-- =====================================================
-- 3. COMMENTS
-- =====================================================

COMMENT ON COLUMN phrase.phoneme_score IS 'Phonemic diversity score (0-100). Higher = more varied phonemes for better voice biometric capture.';
COMMENT ON COLUMN phrase.style IS 'Text style classification: narrative (story-telling), descriptive (descriptions), dialogue (conversations), poetic (literary/rhythmic).';
