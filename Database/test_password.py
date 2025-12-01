#!/usr/bin/env python3
"""Test password hashing to debug login issue."""

import bcrypt

# Test password
password = "admin123"

# Hash from migration script
stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OKi"

# Test verification
is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
print(f"Password: {password}")
print(f"Stored hash: {stored_hash}")
print(f"Is valid: {is_valid}")

# Generate new hash
new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"\nNew hash: {new_hash}")
print(f"New hash validates: {bcrypt.checkpw(password.encode('utf-8'), new_hash.encode('utf-8'))}")
