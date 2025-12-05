"""Check user enrollment status in database."""
import asyncio
import asyncpg

async def check_user_status():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='voice_biometrics'
    )
    
    try:
        # Check user@example.com
        user = await conn.fetchrow(
            "SELECT id, email, has_voiceprint, is_active FROM users WHERE email = 'user@example.com'"
        )
        
        if user:
            print(f"\n=== User: {user['email']} ===")
            print(f"ID: {user['id']}")
            print(f"Has Voiceprint: {user['has_voiceprint']}")
            print(f"Is Active: {user['is_active']}")
            
            # Check if there's a voiceprint for this user
            voiceprints = await conn.fetch(
                "SELECT id, user_id, created_at FROM voiceprints WHERE user_id = $1",
                user['id']
            )
            
            print(f"\nVoiceprints found: {len(voiceprints)}")
            for vp in voiceprints:
                print(f"  - Voiceprint ID: {vp['id']}")
                print(f"    User ID: {vp['user_id']}")
                print(f"    Created: {vp['created_at']}")
            
            # Check all voiceprints to see if any belong to a different user
            all_voiceprints = await conn.fetch(
                "SELECT v.id, v.user_id, u.email FROM voiceprints v LEFT JOIN users u ON v.user_id = u.id ORDER BY v.created_at DESC LIMIT 5"
            )
            
            print(f"\n=== Recent Voiceprints (last 5) ===")
            for vp in all_voiceprints:
                print(f"Voiceprint ID: {vp['id']}")
                print(f"  User ID: {vp['user_id']}")
                print(f"  Email: {vp['email']}")
                print()
        else:
            print("User not found!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_user_status())
