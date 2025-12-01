#!/usr/bin/env python3
"""Update test user passwords with correct bcrypt hashes."""

import asyncio
import asyncpg
import bcrypt


async def update_passwords():
    """Update test user passwords."""
    # Generate correct hashes
    admin_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    user_hash = bcrypt.hashpw(b'user123', bcrypt.gensalt()).decode('utf-8')
    
    print(f"Admin hash: {admin_hash}")
    print(f"User hash: {user_hash}")
    
    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="voice_user",
        password="voice_password",
        database="voice_biometrics"
    )
    
    try:
        # Update admin password
        await conn.execute(
            'UPDATE "user" SET password = $1 WHERE email = $2',
            admin_hash, 'admin@example.com'
        )
        print("✓ Updated admin password")
        
        # Update user password
        await conn.execute(
            'UPDATE "user" SET password = $1 WHERE email = $2',
            user_hash, 'user@example.com'
        )
        print("✓ Updated user password")
        
        # Verify
        admin = await conn.fetchrow('SELECT email, password FROM "user" WHERE email = $1', 'admin@example.com')
        print(f"\nAdmin user: {admin['email']}")
        print(f"Password verifies: {bcrypt.checkpw(b'admin123', admin['password'].encode('utf-8'))}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(update_passwords())
