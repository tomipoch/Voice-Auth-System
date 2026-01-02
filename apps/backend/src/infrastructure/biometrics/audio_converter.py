"""
Audio Converter Utility
Converts audio from various formats (WebM, MP3, etc.) to WAV format
for processing with SpeechBrain ECAPA-TDNN model.
"""

import io
import logging
from typing import Optional
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioConverter:
    """Utility class for audio format conversion."""
    
    @staticmethod
    def convert_to_wav(
        audio_bytes: bytes,
        source_format: str = "webm"
    ) -> bytes:
        """
        Convert audio from any format to WAV format.
        
        Args:
            audio_bytes: Raw audio data in bytes
            source_format: Source audio format (webm, mp3, ogg, etc.)
                          Can be MIME type (audio/webm) or extension (webm)
        
        Returns:
            WAV audio data as bytes (16kHz, mono, 16-bit PCM)
        
        Raises:
            Exception: If conversion fails
        """
        try:
            # Extract format from MIME type if needed
            format_lower = source_format.lower()
            if '/' in format_lower:
                # It's a MIME type like "audio/webm" or "audio/webm;codecs=opus"
                format_lower = format_lower.split('/')[1].split(';')[0]
            
            logger.info(f"Converting audio from {format_lower} to WAV")
            
            # Load audio from bytes
            audio_io = io.BytesIO(audio_bytes)
            audio = AudioSegment.from_file(audio_io, format=format_lower)
            
            # Convert to WAV with optimal settings for speech recognition
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16 bits
            
            # Export to WAV format
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_bytes = wav_io.getvalue()
            
            logger.info(f"Converted audio: {len(audio_bytes)} -> {len(wav_bytes)} bytes")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise Exception(f"Audio conversion failed: {e}")
    
    @staticmethod
    def is_wav_format(audio_bytes: bytes) -> bool:
        """Check if audio data is already in WAV format."""
        if len(audio_bytes) < 12:
            return False
        return audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE'


# Convenience functions for direct use
def convert_to_wav(audio_bytes: bytes, source_format: str = "webm") -> bytes:
    """Convert audio to WAV format."""
    return AudioConverter.convert_to_wav(audio_bytes, source_format)


def is_wav_format(audio_bytes: bytes) -> bool:
    """Check if audio bytes are in WAV format."""
    return AudioConverter.is_wav_format(audio_bytes)


def ensure_wav_format(
    audio_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1
) -> Optional[bytes]:
    """
    Ensure audio is in WAV format, converting if necessary.
    
    Args:
        audio_bytes: Audio data (any format)
        sample_rate: Target sample rate (default: 16000)
        channels: Target number of channels (default: 1)
        
    Returns:
        WAV audio bytes or None if conversion fails
    """
    if is_wav_format(audio_bytes):
        logger.debug("Audio already in WAV format")
        return audio_bytes
    
    try:
        logger.debug("Converting audio to WAV format")
        return convert_to_wav(audio_bytes, "webm")
    except Exception as e:
        logger.error(f"Failed to ensure WAV format: {e}")
        return None
