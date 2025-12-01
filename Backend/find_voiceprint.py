"""Find which user has the voiceprint."""
import asyncio
import asyncpg

async def find_voiceprint_owner():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='voice_biometrics',
        user='voice_user',
        password='voice_password'
    )
    
    try:
        # Find the voiceprint
        voiceprint = await conn.fetchrow(
            'SELECT * FROM voiceprint WHERE user_id = $1',
            '89402942-6858-4abb-a45e-2dc2fc2e745d'
        )
        
        if voiceprint:
            print(f"\n✅ Found voiceprint:")
            print(f"   Voiceprint ID: {voiceprint['id']}")
            print(f"   User ID: {voiceprint['user_id']}")
            print(f"   Created: {voiceprint['created_at']}")
            
            # Find the user
            user = await conn.fetchrow(
                'SELECT * FROM "user" WHERE id = $1',
                voiceprint['user_id']
            )
            
            if user:
                print(f"\n👤 User details:")
                print(f"   Email: {user['email']}")
                print(f"   Name: {user.get('first_name')} {user.get('last_name')}")
                print(f"   Created: {user['created_at']}")
            else:
                print(f"\n❌ User not found in database!")
        else:
            print(f"\n❌ No voiceprint found for user 89402942-6858-4abb-a45e-2dc2fc2e745d")
            
        # Also check current user
        current_user = await conn.fetchrow(
            'SELECT * FROM "user" WHERE id = $1',
            '6d0d7c58-3fb8-4149-aa5e-d792ff15cfd2'
        )
        
        if current_user:
            print(f"\n📌 Current login user:")
            print(f"   ID: {current_user['id']}")
            print(f"   Email: {current_user['email']}")
            print(f"   Name: {current_user.get('first_name')} {current_user.get('last_name')}")
            
            # Check if current user has voiceprint
            current_voiceprint = await conn.fetchrow(
                'SELECT id FROM voiceprint WHERE user_id = $1',
                current_user['id']
            )
            print(f"   Has voiceprint: {'✅ YES' if current_voiceprint else '❌ NO'}")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(find_voiceprint_owner())
