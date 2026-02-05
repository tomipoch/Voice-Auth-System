"""Clean up unused challenges for user."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from src.infrastructure.config.database import get_db_pool
from uuid import UUID

async def clean_challenges():
    pool = await get_db_pool()
    
    user_id = UUID('6d0d7c58-3fb8-4149-aa5e-d792ff15cfd2')
    
    async with pool.acquire() as conn:
        # Delete unused challenges
        result = await conn.execute(
            "DELETE FROM challenges WHERE user_id = $1 AND used_at IS NULL",
            user_id
        )
        
        print(f"✅ Deleted {result.split()[-1]} unused challenges for user {user_id}")
    
    await pool.close()

if __name__ == "__main__":
    asyncio.run(clean_challenges())
