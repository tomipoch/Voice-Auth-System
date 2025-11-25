"""Handles encryption and decryption of sensitive data."""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import urlsafe_b64encode, urlsafe_b64decode

class DataEncryptor:
    """Service to encrypt and decrypt data using AES-GCM."""

    def __init__(self, secret_key: str):
        if not secret_key:
            raise ValueError("A secret key is required for encryption.")
        
        # The key must be 32 bytes long for AES-256
        key_bytes = urlsafe_b64decode(secret_key)
        if len(key_bytes) != 32:
            raise ValueError("Secret key must be a 32-byte, URL-safe base64-encoded string.")
            
        self._aesgcm = AESGCM(key_bytes)

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypts plaintext and returns ciphertext with nonce."""
        nonce = os.urandom(12)  # GCM recommended nonce size is 12 bytes
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypts data, extracting the nonce from the payload."""
        if len(encrypted_data) < 12:
            raise ValueError("Invalid encrypted data: too short to contain a nonce.")
            
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        try:
            return self._aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            # Consider logging the error for security monitoring
            raise ValueError("Decryption failed. Data may be tampered or corrupt.") from e

def get_encryptor() -> DataEncryptor:
    """Factory function to get a configured DataEncryptor instance."""
    secret_key = os.getenv("EMBEDDING_ENCRYPTION_KEY")
    if not secret_key:
        raise EnvironmentError("EMBEDDING_ENCRYPTION_KEY environment variable not set.")
    
    return DataEncryptor(secret_key)

def generate_key() -> str:
    """Generates a new URL-safe, base64-encoded 32-byte key."""
    return urlsafe_b64encode(os.urandom(32)).decode('utf-8')

# Example usage (for testing or key generation):
if __name__ == "__main__":
    # To generate a new key, run this file directly:
    # python -m src.infrastructure.security.encryption
    print("Generated new encryption key:")
    print(generate_key())
