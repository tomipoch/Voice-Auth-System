"""PostgreSQL implementation of VoiceTemplateRepositoryPort."""

import asyncpg
import numpy as np
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from ..domain.model.VoiceSignature import VoiceSignature
from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ...shared.types.common_types import UserId, VoiceEmbedding
from ..security.encryption import DataEncryptor, get_encryptor


class PostgresVoiceSignatureRepository(VoiceSignatureRepositoryPort):
    """PostgreSQL implementation of voice signature repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
        self._encryptor: DataEncryptor = get_encryptor()
    
    async def save_voiceprint(self, voiceprint: VoiceSignature) -> None:
        """Save a user's voiceprint, encrypting the embedding."""
        async with self._pool.acquire() as conn:
            encrypted_embedding = self._encryptor.encrypt(voiceprint.embedding.tobytes())
            
            await conn.execute(
                """
                INSERT INTO voiceprint (id, user_id, embedding, created_at, speaker_model_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                voiceprint.id,
                voiceprint.user_id,
                encrypted_embedding,
                voiceprint.created_at,
                voiceprint.speaker_model_id
            )
    
    async def get_voiceprint_by_user(self, user_id: UserId) -> Optional[VoiceSignature]:
        """Get the current voiceprint for a user, decrypting the embedding."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, embedding, created_at, speaker_model_id
                FROM voiceprint
                WHERE user_id = $1
                """,
                user_id
            )
            
            if row:
                decrypted_embedding_bytes = self._encryptor.decrypt(row['embedding'])
                embedding = np.frombuffer(decrypted_embedding_bytes, dtype=np.float32)
                
                return VoiceSignature(
                    id=row['id'],
                    user_id=row['user_id'],
                    embedding=embedding,
                    created_at=row['created_at'],
                    speaker_model_id=row['speaker_model_id']
                )
            return None
    
    async def update_voiceprint(self, voiceprint: VoiceSignature) -> None:
        """Update an existing voiceprint, encrypting the new embedding."""
        async with self._pool.acquire() as conn:
            encrypted_embedding = self._encryptor.encrypt(voiceprint.embedding.tobytes())
            
            await conn.execute(
                """
                UPDATE voiceprint
                SET embedding = $1, created_at = $2, speaker_model_id = $3
                WHERE user_id = $4
                """,
                encrypted_embedding,
                voiceprint.created_at,
                voiceprint.speaker_model_id,
                voiceprint.user_id
            )
    
    async def delete_voiceprint(self, user_id: UserId) -> None:
        """Delete a user's voiceprint."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM voiceprint WHERE user_id = $1
                """,
                user_id
            )
    
    async def save_enrollment_sample(
        self,
        user_id: UserId,
        embedding: VoiceEmbedding,
        snr_db: Optional[float] = None,
        duration_sec: Optional[float] = None
    ) -> UUID:
        """Save an individual enrollment sample, encrypting the embedding."""
        sample_id = uuid4()
        encrypted_embedding = self._encryptor.encrypt(embedding.tobytes())
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO enrollment_sample (id, user_id, embedding, snr_db, duration_sec, created_at)
                VALUES ($1, $2, $3, $4, $5, now())
                """,
                sample_id, user_id, encrypted_embedding, snr_db, duration_sec
            )
        
        return sample_id
    
    async def get_enrollment_samples(self, user_id: UserId) -> List[Dict[str, Any]]:
        """Get all enrollment samples for a user, decrypting embeddings."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, embedding, snr_db, duration_sec, created_at
                FROM enrollment_sample
                WHERE user_id = $1
                ORDER BY created_at ASC
                """,
                user_id
            )
            
            samples = []
            for row in rows:
                sample = dict(row)
                decrypted_embedding_bytes = self._encryptor.decrypt(row['embedding'])
                sample['embedding'] = np.frombuffer(decrypted_embedding_bytes, dtype=np.float32)
                samples.append(sample)
            
            return samples
    
    async def save_voiceprint_history(self, voiceprint: VoiceSignature) -> None:
        """Save voiceprint to history, encrypting the embedding."""
        async with self._pool.acquire() as conn:
            encrypted_embedding = self._encryptor.encrypt(voiceprint.embedding.tobytes())
            
            await conn.execute(
                """
                INSERT INTO voiceprint_history (id, user_id, embedding, created_at, speaker_model_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid4(),
                voiceprint.user_id,
                encrypted_embedding,
                voiceprint.created_at,
                voiceprint.speaker_model_id
            )
    
    async def get_voiceprint_history(self, user_id: UserId) -> List[VoiceSignature]:
        """Get voiceprint history for a user, decrypting embeddings."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, embedding, created_at, speaker_model_id
                FROM voiceprint_history
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )
            
            history = []
            for row in rows:
                decrypted_embedding_bytes = self._encryptor.decrypt(row['embedding'])
                embedding = np.frombuffer(decrypted_embedding_bytes, dtype=np.float32)
                
                signature = VoiceSignature(
                    id=row['id'],
                    user_id=row['user_id'],
                    embedding=embedding,
                    created_at=row['created_at'],
                    speaker_model_id=row['speaker_model_id']
                )
                history.append(signature)
            
            return history