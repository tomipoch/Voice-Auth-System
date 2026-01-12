"""
Audio Converter Utility
Converts audio from various formats (WebM, MP3, etc.) to WAV format
for processing with SpeechBrain ECAPA-TDNN model.
"""

import io
import logging
import subprocess
import tempfile
import os
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
            
            logger.info(f"Converting audio from {format_lower} to WAV ({len(audio_bytes)} bytes)")
            
            # Try pydub first
            try:
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
                
                logger.info(f"Pydub conversion successful: {len(audio_bytes)} -> {len(wav_bytes)} bytes")
                return wav_bytes
                
            except Exception as pydub_error:
                logger.warning(f"Pydub failed: {pydub_error}, trying ffmpeg directly...")
                return AudioConverter._convert_with_ffmpeg(audio_bytes, format_lower)
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise RuntimeError(f"Audio conversion failed: {e}")
    
    @staticmethod
    def _convert_with_ffmpeg(audio_bytes: bytes, source_format: str) -> bytes:
        """
        Convert audio using ffmpeg directly via subprocess.
        This is a fallback when pydub fails with certain codecs.
        """
        input_file = None
        output_file = None
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=f'.{source_format}', delete=False) as f:
                f.write(audio_bytes)
                input_file = f.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                output_file = f.name
            
            # Run ffmpeg
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', input_file,  # Input file
                '-ar', '16000',  # Sample rate 16kHz
                '-ac', '1',  # Mono
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-f', 'wav',  # Output format
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"ffmpeg error: {stderr[:200]}")
            
            # Read output file
            with open(output_file, 'rb') as f:
                wav_bytes = f.read()
            
            logger.info(f"FFmpeg conversion successful: {len(audio_bytes)} -> {len(wav_bytes)} bytes")
            return wav_bytes
            
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffmpeg conversion timed out")
        finally:
            # Clean up temp files
            if input_file and os.path.exists(input_file):
                os.unlink(input_file)
            if output_file and os.path.exists(output_file):
                os.unlink(output_file)
    
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
        logger.debug(f"Converting audio to WAV format (input size: {len(audio_bytes)} bytes)")
        return convert_to_wav(audio_bytes, "webm")
    except Exception as e:
        logger.error(f"Failed to ensure WAV format: {type(e).__name__}: {e}")
        # Try with 'ogg' format as fallback (webm sometimes contains ogg codec)
        try:
            logger.debug("Trying ogg format as fallback...")
            return convert_to_wav(audio_bytes, "ogg")
        except Exception as e2:
            logger.error(f"Fallback to ogg also failed: {type(e2).__name__}: {e2}")
            return None
