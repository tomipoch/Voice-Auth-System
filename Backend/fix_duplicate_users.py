"""
Script to fix duplicate users and transfer voiceprints.
Run this script to consolidate duplicate users with the same email.
"""

import asyncio
import asyncpg
from uuid import UUID

async def fix_duplicate_users():
    """Fix duplicate users by transferring voiceprints to the correct user."""
    
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='voice_biometrics',
        user='voice_user',
        password='voice_password'
    )
    
    try:
        # Find duplicate users with email user@example.com
        users = await conn.fetch(
            'SELECT id, email, first_name, last_name, created_at FROM "user" WHERE email = $1 ORDER BY created_at',
            'user@example.com'
        )
        
        print(f"\nFound {len(users)} users with email user@example.com:")
        for i, user in enumerate(users):
            print(f"  {i+1}. ID: {user['id']}, Created: {user['created_at']}")
            
            # Check if this user has a voiceprint
            voiceprint = await conn.fetchrow(
                "SELECT id, created_at FROM voiceprint WHERE user_id = $1",
                user['id']
            )
            if voiceprint:
                print(f"     ✅ HAS VOICEPRINT: {voiceprint['id']} (created {voiceprint['created_at']})")
            else:
                print(f"     ❌ NO VOICEPRINT")
        
        if len(users) > 1:
            print(f"\n⚠️  Found {len(users)} duplicate users!")
            
            # Keep the most recent user (last in the list)
            keep_user = users[-1]
            old_users = users[:-1]
            
            print(f"\n📌 Will keep user: {keep_user['id']} (created {keep_user['created_at']})")
            print(f"🗑️  Will remove {len(old_users)} old user(s)")
            
            # Transfer voiceprints from old users to the kept user
            for old_user in old_users:
                print(f"\n  Processing old user {old_user['id']}...")
                
                # Check if old user has voiceprint
                old_voiceprint = await conn.fetchrow(
                    "SELECT * FROM voiceprint WHERE user_id = $1",
                    old_user['id']
                )
                
                if old_voiceprint:
                    # Check if keep_user already has a voiceprint
                    keep_voiceprint = await conn.fetchrow(
                        "SELECT id FROM voiceprint WHERE user_id = $1",
                        keep_user['id']
                    )
                    
                    if keep_voiceprint:
                        print(f"    ⚠️  Keep user already has voiceprint, deleting old voiceprint")
                        await conn.execute(
                            "DELETE FROM voiceprint WHERE user_id = $1",
                            old_user['id']
                        )
                    else:
                        print(f"    ✅ Transferring voiceprint to keep user")
                        await conn.execute(
                            "UPDATE voiceprint SET user_id = $1 WHERE user_id = $2",
                            keep_user['id'],
                            old_user['id']
                        )
                
                # Delete enrollment samples for old user
                deleted_samples = await conn.execute(
                    "DELETE FROM enrollment_sample WHERE user_id = $1",
                    old_user['id']
                )
                print(f"    🗑️  Deleted enrollment samples: {deleted_samples}")
                
                # Delete old user
                await conn.execute(
                    'DELETE FROM "user" WHERE id = $1',
                    old_user['id']
                )
                print(f"    ✅ Deleted old user {old_user['id']}")
            
            print(f"\n✅ Cleanup complete! Now only user {keep_user['id']} exists.")
        else:
            print("\n✅ No duplicate users found!")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_duplicate_users())
