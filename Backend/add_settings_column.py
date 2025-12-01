
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def add_settings_column():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'voice_biometrics')
    db_user = os.getenv('DB_USER', 'voice_user')
    db_password = os.getenv('DB_PASSWORD', 'voice_password')

    print(f"Connecting to {db_host}:{db_port}/{db_name} as {db_user}...")

    try:
        conn = await asyncpg.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password
        )

        # Check if column exists
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name = 'settings'
            );
        """)

        if not column_exists:
            print("Adding 'settings' column to 'user' table...")
            await conn.execute("""
                ALTER TABLE "user"
                ADD COLUMN settings JSONB DEFAULT '{}'::jsonb;
            """)
            print("Column added successfully.")
        else:
            print("'settings' column already exists.")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(add_settings_column())
