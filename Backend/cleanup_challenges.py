#!/usr/bin/env python3
"""Script to cleanup unused challenges for a specific user."""

import asyncio
import asyncpg
import sys
from uuid import UUID

async def cleanup_user_challenges(user_id: str):
    """Delete unused challenges for a user."""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='voiceauth_user',
            password='voiceauth_pass',
            database='voiceauth_db'
        )
        
        # Delete unused challenges
        result = await conn.execute(
            """
            DELETE FROM challenge
            WHERE user_id = $1 AND used_at IS NULL
            """,
            UUID(user_id)
        )
        
        count = int(result.split()[-1]) if result.startswith("DELETE") else 0
        print(f"✅ Deleted {count} unused challenges for user {user_id}")
        
        await conn.close()
        return count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    user_id = "fa64f420-c36a-4abf-b8ea-c9aad297fe47"
    asyncio.run(cleanup_user_challenges(user_id))
