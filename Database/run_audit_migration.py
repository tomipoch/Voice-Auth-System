#!/usr/bin/env python3
"""Run migration to fix audit_log table schema."""

import asyncio
import asyncpg
import sys
from pathlib import Path


async def run_migration():
    """Execute the migration script."""
    migration_file = Path(__file__).parent / "migrations" / "002_fix_audit_log.sql"
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    migration_sql = migration_file.read_text()
    
    print("Connecting to database...")
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="voice_user",
        password="voice_password",
        database="voice_biometrics"
    )
    
    try:
        print("Running audit_log table migration...")
        
        # Execute migration (split by semicolon for individual statements)
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for stmt in statements:
            if stmt and not stmt.startswith('SELECT'):
                await conn.execute(stmt)
        
        print("✓ Migration completed successfully!")
        
        # Verify the changes
        print("\nVerifying changes...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'audit_log'
            ORDER BY ordinal_position
        """)
        
        print("\nAudit_log table columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
