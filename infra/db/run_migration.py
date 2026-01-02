#!/usr/bin/env python3
"""Run database migration to add user authentication columns."""

import asyncio
import asyncpg
import sys
from pathlib import Path


async def run_migration():
    """Execute the migration script."""
    # Read migration SQL
    migration_file = Path(__file__).parent / "migrations" / "001_add_user_auth_columns.sql"
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    migration_sql = migration_file.read_text()
    
    # Connect to database
    print("Connecting to database...")
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="voice_user",
        password="voice_password",
        database="voice_biometrics"
    )
    
    try:
        print("Running migration...")
        await conn.execute(migration_sql)
        print("✓ Migration completed successfully!")
        
        # Verify the changes
        print("\nVerifying changes...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user'
            ORDER BY ordinal_position
        """)
        
        print("\nUser table columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check test users
        users = await conn.fetch('SELECT email, role, first_name, last_name FROM "user" WHERE email IS NOT NULL')
        print(f"\nTest users created: {len(users)}")
        for user in users:
            print(f"  - {user['email']} ({user['role']}): {user['first_name']} {user['last_name']}")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
