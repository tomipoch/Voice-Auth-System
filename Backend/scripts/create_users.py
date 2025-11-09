"""Script para crear usuarios de prueba en el sistema."""

import bcrypt
from datetime import datetime
import json

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_test_users():
    """Create test users for the system."""
    
    # Usuario administrador
    admin_user = {
        "id": "admin-001",
        "name": "Administrador del Sistema",
        "email": "admin@voicebio.com",
        "hashed_password": hash_password("AdminVoice2024!"),
        "role": "admin",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-admin-001",
            "created_at": datetime.now(),
            "samples_count": 5,
            "quality_score": 0.96
        }
    }
    
    # Usuario normal 1
    user1 = {
        "id": "user-001",
        "name": "Juan Carlos Pérez",
        "email": "juan.perez@empresa.com",
        "hashed_password": hash_password("UserVoice2024!"),
        "role": "user",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-user-001",
            "created_at": datetime.now(),
            "samples_count": 3,
            "quality_score": 0.89
        }
    }
    
    # Usuario normal 2 (sin perfil de voz)
    user2 = {
        "id": "user-002",
        "name": "María Elena Rodríguez",
        "email": "maria.rodriguez@empresa.com",
        "hashed_password": hash_password("UserVoice2024!"),
        "role": "user",
        "created_at": datetime.now(),
        "voice_template": None
    }
    
    # Usuario de desarrollo (mantener compatibilidad)
    dev_user = {
        "id": "dev-user-1",
        "name": "Usuario Desarrollo",
        "email": "dev@test.com",
        "hashed_password": hash_password("123456"),
        "role": "user",
        "created_at": datetime.now(),
        "voice_template": None
    }
    
    # Admin de desarrollo (mantener compatibilidad)
    dev_admin = {
        "id": "admin-user-1",
        "name": "Admin Desarrollo",
        "email": "admin@test.com",
        "hashed_password": hash_password("123456"),
        "role": "admin",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-admin-dev",
            "created_at": datetime.now(),
            "samples_count": 5,
            "quality_score": 0.95
        }
    }
    
    users_data = {
        "admin@voicebio.com": admin_user,
        "juan.perez@empresa.com": user1,
        "maria.rodriguez@empresa.com": user2,
        "dev@test.com": dev_user,
        "admin@test.com": dev_admin
    }
    
    return users_data

if __name__ == "__main__":
    users = create_test_users()
    
    print("=== USUARIOS CREADOS ===\n")
    
    for email, user in users.items():
        print(f"📧 Email: {email}")
        print(f"👤 Nombre: {user['name']}")
        print(f"🔑 Rol: {user['role'].upper()}")
        print(f"🎤 Perfil de voz: {'✅ Configurado' if user['voice_template'] else '❌ Pendiente'}")
        
        # Mostrar contraseña original para usuarios de prueba
        if email in ["admin@voicebio.com", "juan.perez@empresa.com", "maria.rodriguez@empresa.com"]:
            print(f"🔐 Contraseña: UserVoice2024!" if user['role'] == 'user' else "🔐 Contraseña: AdminVoice2024!")
        elif email in ["dev@test.com", "admin@test.com"]:
            print(f"🔐 Contraseña: 123456")
            
        print("-" * 50)