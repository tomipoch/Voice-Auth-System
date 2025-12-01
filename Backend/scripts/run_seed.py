import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_seed():
    # Database config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "voice_biometrics")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    print(f"Connecting to {DB_NAME} at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Read SQL file
        with open("scripts/seed_phrases.sql", "r") as f:
            sql = f.read()
            
        print("Executing seed_phrases.sql...")
        await conn.execute(sql)
        print("Seed data inserted successfully!")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_seed())
