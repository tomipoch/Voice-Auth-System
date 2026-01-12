#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from infrastructure.database import get_session
from sqlalchemy import text

def check_user(email):
    with get_session() as session:
        # Buscar usuario por email
        result = session.execute(
            text('SELECT id, email, username, role, created_at FROM users WHERE email = :email'),
            {'email': email}
        )
        user = result.fetchone()
        
        if user:
            print('✅ Usuario encontrado en la API biométrica:')
            print(f'   ID: {user[0]}')
            print(f'   Email: {user[1]}')
            print(f'   Username: {user[2]}')
            print(f'   Role: {user[3]}')
            print(f'   Creado: {user[4]}')
            
            # Verificar voiceprint
            voiceprint_result = session.execute(
                text('SELECT id, created_at, updated_at, is_active FROM voiceprints WHERE user_id = :user_id'),
                {'user_id': user[0]}
            )
            voiceprint = voiceprint_result.fetchone()
            
            if voiceprint:
                print('')
                print('✅ Voiceprint (Enrollment completado):')
                print(f'   Voiceprint ID: {voiceprint[0]}')
                print(f'   Creado: {voiceprint[1]}')
                print(f'   Actualizado: {voiceprint[2]}')
                print(f'   Activo: {voiceprint[3]}')
                
                # Contar voice samples
                samples_result = session.execute(
                    text('SELECT COUNT(*) FROM voice_samples WHERE voiceprint_id = :voiceprint_id'),
                    {'voiceprint_id': voiceprint[0]}
                )
                sample_count = samples_result.scalar()
                print(f'   Voice Samples: {sample_count}')
            else:
                print('')
                print('❌ No tiene voiceprint - No está enrollado')
        else:
            print('❌ Usuario NO encontrado en la API biométrica')
            print('')
            print('Usuarios existentes con @banco:')
            all_users = session.execute(
                text("SELECT id, email, username FROM users WHERE email LIKE '%@banco%'")
            )
            for u in all_users:
                print(f'   - {u[1]} (username: {u[2]})')

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else 'juan@banco.cl'
    check_user(email)
