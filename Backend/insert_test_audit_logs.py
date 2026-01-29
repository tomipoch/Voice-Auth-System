"""Script to insert test audit logs for testing admin dashboard."""
import asyncio
import asyncpg
from datetime import datetime, timedelta, timezone
import json

async def insert_test_logs():
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='voice_biometrics'
    )
    
    try:
        # Get user@example.com user_id
        user = await conn.fetchrow(
            "SELECT id, email, company FROM users WHERE email = 'user@example.com'"
        )
        
        if not user:
            print("User not found!")
            return
        
        user_id = str(user['id'])
        print(f"Found user: {user['email']}, ID: {user_id}, Company: {user['company']}")
        
        # Create test audit logs
        now = datetime.now(timezone.utc)
        
        logs = [
            # Login
            {
                'actor': user_id,
                'action': 'LOGIN',
                'entity_type': 'user',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'User logged in successfully', 'ip': '127.0.0.1'}),
                'timestamp': now - timedelta(minutes=30)
            },
            # Enrollment start
            {
                'actor': user_id,
                'action': 'ENROLLMENT_START',
                'entity_type': 'enrollment',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'Started voice enrollment'}),
                'timestamp': now - timedelta(minutes=25)
            },
            # Enrollment complete
            {
                'actor': user_id,
                'action': 'ENROLLMENT_COMPLETE',
                'entity_type': 'enrollment',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'Voice enrollment completed successfully', 'samples': 3}),
                'timestamp': now - timedelta(minutes=20)
            },
            # Verification success
            {
                'actor': user_id,
                'action': 'VERIFICATION',
                'entity_type': 'verification',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'Voice verification successful', 'score': 0.95, 'difficulty': 'medium'}),
                'timestamp': now - timedelta(minutes=10)
            },
            # Another verification
            {
                'actor': user_id,
                'action': 'VERIFICATION',
                'entity_type': 'verification',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'Voice verification successful', 'score': 0.92, 'difficulty': 'medium'}),
                'timestamp': now - timedelta(minutes=5)
            },
            # Logout
            {
                'actor': user_id,
                'action': 'LOGOUT',
                'entity_type': 'user',
                'entity_id': user_id,
                'success': True,
                'metadata': json.dumps({'message': 'User logged out'}),
                'timestamp': now - timedelta(minutes=2)
            },
        ]
        
        # Insert logs
        for log in logs:
            await conn.execute(
                """
                INSERT INTO audit_log (actor, action, entity_type, entity_id, success, metadata, error_message, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                log['actor'],
                log['action'],
                log['entity_type'],
                log['entity_id'],
                log['success'],
                log['metadata'],
                None,
                log['timestamp']
            )
        
        print(f"✅ Inserted {len(logs)} test audit logs for user {user['email']}")
        
        # Verify
        count = await conn.fetchval("SELECT COUNT(*) FROM audit_log WHERE actor = $1", user_id)
        print(f"Total logs for this user: {count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(insert_test_logs())
