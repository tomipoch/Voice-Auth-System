-- Seed data for phrases (Spanish)
INSERT INTO phrase (id, text, source, word_count, char_count, language, difficulty, is_active, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440101', 'La lluvia en Sevilla es una pura maravilla', 'Proverbio', 8, 42, 'es', 'easy', true, now()),
('550e8400-e29b-41d4-a716-446655440102', 'Tres tristes tigres comían trigo en un trigal', 'Trabalenguas', 9, 45, 'es', 'hard', true, now()),
('550e8400-e29b-41d4-a716-446655440103', 'El rápido zorro marrón salta sobre el perro perezoso', 'Pangrama', 9, 52, 'es', 'medium', true, now()),
('550e8400-e29b-41d4-a716-446655440104', 'Mi voz es mi identidad y me permite acceder a mi cuenta', 'Frase de seguridad', 12, 55, 'es', 'medium', true, now()),
('550e8400-e29b-41d4-a716-446655440105', 'Hoy es un buen día para verificar mi identidad', 'Frase común', 9, 46, 'es', 'easy', true, now()),
('550e8400-e29b-41d4-a716-446655440106', 'La seguridad biométrica es el futuro de la autenticación', 'Tecnología', 9, 56, 'es', 'medium', true, now()),
('550e8400-e29b-41d4-a716-446655440107', 'Por favor verifique mi voz para continuar con el proceso', 'Instrucción', 10, 56, 'es', 'medium', true, now()),
('550e8400-e29b-41d4-a716-446655440108', 'El cielo está despejado y brilla el sol', 'Clima', 8, 39, 'es', 'easy', true, now()),
('550e8400-e29b-41d4-a716-446655440109', 'Caminante no hay camino se hace camino al andar', 'Poesía', 9, 47, 'es', 'medium', true, now()),
('550e8400-e29b-41d4-a716-446655440110', 'En un lugar de la Mancha de cuyo nombre no quiero acordarme', 'Literatura', 12, 59, 'es', 'hard', true, now())
ON CONFLICT (id) DO NOTHING;
