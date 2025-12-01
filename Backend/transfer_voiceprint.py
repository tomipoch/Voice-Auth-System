"""Transfer voiceprint from anonymous user to user@example.com"""
import asyncio
import asyncpg

async def transfer_voiceprint():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='voice_biometrics',
        user='voice_user',
        password='voice_password'
    )
    
    try:
        from_user = '89402942-6858-4abb-a45e-2dc2fc2e745d'
        to_user = '6d0d7c58-3fb8-4149-aa5e-d792ff15cfd2'
        
        print(f"\n🔄 Transferring voiceprint...")
        print(f"   From: {from_user}")
        print(f"   To:   {to_user}")
        
        # Transfer voiceprint
        result = await conn.execute(
            'UPDATE voiceprint SET user_id = $1 WHERE user_id = $2',
            to_user,
            from_user
        )
        print(f"\n✅ Voiceprint transferred! ({result})")
        
        # Delete anonymous user
        await conn.execute(
            'DELETE FROM "user" WHERE id = $1',
            from_user
        )
        print(f"✅ Deleted anonymous user")
        
        # Verify
        voiceprint = await conn.fetchrow(
            'SELECT id, user_id FROM voiceprint WHERE user_id = $1',
            to_user
        )
        
        if voiceprint:
            print(f"\n✅ Verification successful!")
            print(f"   User {to_user} now has voiceprint {voiceprint['id']}")
        else:
            print(f"\n❌ Transfer failed!")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(transfer_voiceprint())
