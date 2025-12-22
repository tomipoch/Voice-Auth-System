"""
Audio Converter Utility

Converts WebM audio from frontend to WAV format for dataset storage.
Uses pydub with ffmpeg backend for reliable conversion.
"""

import io
import logging
from typing import Optional
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def webm_to_wav(
    webm_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1
) -> Optional[bytes]:
    """
    Convert WebM audio to WAV format.
    
    Args:
        webm_bytes: WebM audio data
        sample_rate: Target sample rate (default: 16000 Hz)
        channels: Number of audio channels (default: 1 for mono)
        
    Returns:
        WAV audio bytes or None if conversion fails
    """
    try:
        # Load WebM audio
        audio = AudioSegment.from_file(
            io.BytesIO(webm_bytes),
            format="webm"
        )
        
        # Convert to mono if needed
        if channels == 1 and audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Resample if needed
        if audio.frame_rate != sample_rate:
            audio = audio.set_frame_rate(sample_rate)
        
        # Export to WAV
        wav_buffer = io.BytesIO()
        audio.export(
            wav_buffer,
            format="wav",
            parameters=[
                "-ar", str(sample_rate),
                "-ac", str(channels)
            ]
        )
        
        wav_bytes = wav_buffer.getvalue()
        logger.debug(f"Converted WebM ({len(webm_bytes)} bytes) to WAV ({len(wav_bytes)} bytes)")
        
        return wav_bytes
        
    except Exception as e:
        logger.error(f"Failed to convert WebM to WAV: {e}")
        return None


def is_wav_format(audio_bytes: bytes) -> bool:
    """
    Check if audio bytes are in WAV format.
    
    Args:
        audio_bytes: Audio data to check
        
    Returns:
        True if WAV format, False otherwise
    """
    if len(audio_bytes) < 12:
        return False
    
    # Check for RIFF header
    return (
        audio_bytes[0:4] == b'RIFF' and
        audio_bytes[8:12] == b'WAVE'
    )


def ensure_wav_format(
    audio_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1
) -> Optional[bytes]:
    """
    Ensure audio is in WAV format, converting if necessary.
    
    Args:
        audio_bytes: Audio data (any format)
        sample_rate: Target sample rate
        channels: Target number of channels
        
    Returns:
        WAV audio bytes or None if conversion fails
    """
    # Check if already WAV
    if is_wav_format(audio_bytes):
        logger.debug("Audio already in WAV format")
        return audio_bytes
    
    # Assume WebM and convert
    logger.debug("Converting audio to WAV format")
    return webm_to_wav(audio_bytes, sample_rate, channels)


if __name__ == "__main__":
    # Example usage
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        # Test with file
        input_file = sys.argv[1]
        output_file = input_file.rsplit('.', 1)[0] + '.wav'
        
        with open(input_file, 'rb') as f:
            audio_bytes = f.read()
        
        print(f"Input: {len(audio_bytes)} bytes")
        
        wav_bytes = ensure_wav_format(audio_bytes)
        
        if wav_bytes:
            with open(output_file, 'wb') as f:
                f.write(wav_bytes)
            print(f"Output: {len(wav_bytes)} bytes → {output_file}")
        else:
            print("Conversion failed")
    else:
        print("Usage: python audio_converter.py <input_file>")
