"""
Audio Feature Extraction for Anti-Spoofing

This module provides feature extraction functions specifically designed
to detect voice cloning attacks. Features focus on characteristics that
differentiate genuine recordings from synthetic audio.

Key Features:
- SNR (Signal-to-Noise Ratio): Cloned audio is often too clean
- Spectral Artifacts: Synthetic audio has frequency domain artifacts
- Background Noise: Genuine recordings have natural ambient noise
- Pitch Stability: Cloned audio has overly stable pitch
"""

import numpy as np
import librosa
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class AudioFeatureExtractor:
    """
    Extracts audio features for enhanced anti-spoofing detection.
    
    Focuses on features that are most effective for detecting
    voice cloning attacks.
    """
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize feature extractor.
        
        Args:
            sample_rate: Audio sample rate (default: 16000 Hz)
        """
        self.sample_rate = sample_rate
        
    def calculate_snr(self, audio: np.ndarray) -> float:
        """
        Calculate Signal-to-Noise Ratio (SNR).
        
        Voice cloning typically produces very clean audio (SNR > 40 dB),
        while genuine recordings have natural noise (SNR 20-35 dB).
        
        Args:
            audio: Audio signal as numpy array
            
        Returns:
            SNR in decibels (dB)
        """
        try:
            # Estimate signal power (using RMS of voiced segments)
            # Use top 50% energy frames as signal
            frame_length = int(0.025 * self.sample_rate)  # 25ms frames
            hop_length = int(0.010 * self.sample_rate)    # 10ms hop
            
            # Calculate frame energies
            frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
            frame_energies = np.sum(frames ** 2, axis=0)
            
            # Signal: top 50% energy frames
            threshold = np.percentile(frame_energies, 50)
            signal_frames = frames[:, frame_energies >= threshold]
            signal_power = np.mean(signal_frames ** 2) if signal_frames.size > 0 else np.mean(audio ** 2)
            
            # Noise: bottom 20% energy frames (likely silence/noise)
            noise_threshold = np.percentile(frame_energies, 20)
            noise_frames = frames[:, frame_energies <= noise_threshold]
            noise_power = np.mean(noise_frames ** 2) if noise_frames.size > 0 else 1e-10
            
            # Avoid division by zero
            if noise_power < 1e-10:
                noise_power = 1e-10
            
            # Calculate SNR in dB
            snr = 10 * np.log10(signal_power / noise_power)
            
            # Clip to reasonable range
            snr = np.clip(snr, 0, 100)
            
            return float(snr)
            
        except Exception as e:
            logger.warning(f"SNR calculation failed: {e}")
            return 30.0  # Default moderate SNR
    
    def detect_spectral_artifacts(self, audio: np.ndarray) -> float:
        """
        Detect spectral artifacts typical of synthetic audio.
        
        Voice cloning models often create:
        - Abrupt frequency cutoffs
        - Unnatural harmonic patterns
        - Spectral discontinuities
        
        Args:
            audio: Audio signal as numpy array
            
        Returns:
            Artifact score (0.0 = clean, 1.0 = many artifacts)
        """
        try:
            # Compute spectrogram
            D = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(D)
            
            # 1. Check for abrupt high-frequency cutoff
            # Genuine speech has energy up to ~8kHz, synthetic often cuts off earlier
            freq_bins = magnitude.shape[0]
            nyquist = self.sample_rate / 2
            
            # Energy in high frequencies (6-8 kHz)
            high_freq_start = int((6000 / nyquist) * freq_bins)
            high_freq_end = int((8000 / nyquist) * freq_bins)
            high_freq_energy = np.mean(magnitude[high_freq_start:high_freq_end, :])
            
            # Energy in mid frequencies (2-4 kHz)
            mid_freq_start = int((2000 / nyquist) * freq_bins)
            mid_freq_end = int((4000 / nyquist) * freq_bins)
            mid_freq_energy = np.mean(magnitude[mid_freq_start:mid_freq_end, :])
            
            # Ratio should be reasonable for genuine speech
            if mid_freq_energy > 0:
                freq_ratio = high_freq_energy / mid_freq_energy
                cutoff_score = 1.0 - np.clip(freq_ratio * 10, 0, 1)  # Low ratio = high score
            else:
                cutoff_score = 0.5
            
            # 2. Check spectral flatness (how "noisy" vs "tonal")
            # Synthetic audio tends to be more tonal (lower flatness)
            spectral_flatness = librosa.feature.spectral_flatness(y=audio, n_fft=2048, hop_length=512)
            avg_flatness = np.mean(spectral_flatness)
            
            # Genuine speech: 0.05-0.15, Synthetic: often < 0.05
            flatness_score = 1.0 - np.clip(avg_flatness / 0.15, 0, 1)
            
            # 3. Check for spectral discontinuities
            # Compute spectral flux (change between consecutive frames)
            spectral_flux = np.sqrt(np.sum(np.diff(magnitude, axis=1) ** 2, axis=0))
            flux_variance = np.var(spectral_flux)
            
            # Synthetic audio often has lower variance (more consistent)
            # Normalize by typical range
            flux_score = 1.0 - np.clip(flux_variance / 1000, 0, 1)
            
            # Combine scores (weighted average)
            artifact_score = (
                0.4 * cutoff_score +      # Frequency cutoff (most important)
                0.3 * flatness_score +     # Spectral flatness
                0.3 * flux_score           # Spectral consistency
            )
            
            return float(np.clip(artifact_score, 0, 1))
            
        except Exception as e:
            logger.warning(f"Spectral artifact detection failed: {e}")
            return 0.0  # Default: no artifacts detected
    
    def analyze_background_noise(self, audio: np.ndarray) -> float:
        """
        Analyze background noise characteristics.
        
        Genuine recordings have consistent low-level ambient noise.
        Cloned audio often has no background noise or artificial noise patterns.
        
        Args:
            audio: Audio signal as numpy array
            
        Returns:
            Background noise level (0.0 = no noise, 1.0 = high noise)
        """
        try:
            # Detect silence/low-energy segments
            frame_length = int(0.025 * self.sample_rate)
            hop_length = int(0.010 * self.sample_rate)
            
            # Calculate RMS energy per frame
            rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Find low-energy frames (likely silence/background)
            threshold = np.percentile(rms, 20)  # Bottom 20%
            silence_frames_idx = rms < threshold
            
            if np.sum(silence_frames_idx) == 0:
                return 0.0  # No silence detected
            
            # Extract audio from silence frames
            silence_audio = []
            for i, is_silence in enumerate(silence_frames_idx):
                if is_silence:
                    start = i * hop_length
                    end = start + frame_length
                    if end <= len(audio):
                        silence_audio.append(audio[start:end])
            
            if not silence_audio:
                return 0.0
            
            silence_audio = np.concatenate(silence_audio)
            
            # Measure noise characteristics
            noise_std = np.std(silence_audio)
            
            # Normalize to typical range (0.001 - 0.01 for genuine)
            # Synthetic often < 0.0005
            noise_level = np.clip(noise_std / 0.01, 0, 1)
            
            return float(noise_level)
            
        except Exception as e:
            logger.warning(f"Background noise analysis failed: {e}")
            return 0.5  # Default moderate noise
    
    def calculate_pitch_stability(self, audio: np.ndarray) -> float:
        """
        Calculate pitch stability/variance.
        
        Genuine speech has natural micro-variations in pitch.
        Cloned audio often has overly stable pitch.
        
        Args:
            audio: Audio signal as numpy array
            
        Returns:
            Pitch variance score (0.0 = very stable/synthetic, 1.0 = natural variation)
        """
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(
                y=audio,
                sr=self.sample_rate,
                fmin=80,   # Minimum pitch (Hz)
                fmax=400   # Maximum pitch (Hz)
            )
            
            # Get pitch values for frames with sufficient magnitude
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Valid pitch
                    pitch_values.append(pitch)
            
            if len(pitch_values) < 10:
                return 0.5  # Not enough data
            
            pitch_values = np.array(pitch_values)
            
            # Calculate variance
            pitch_variance = np.var(pitch_values)
            
            # Also calculate local variance (frame-to-frame changes)
            pitch_diff = np.abs(np.diff(pitch_values))
            local_variance = np.mean(pitch_diff)
            
            # Normalize variances
            # Genuine speech: variance ~100-500, local ~5-20
            # Synthetic: variance ~20-100, local ~1-5
            global_score = np.clip(pitch_variance / 500, 0, 1)
            local_score = np.clip(local_variance / 20, 0, 1)
            
            # Combine scores
            stability_score = 0.6 * global_score + 0.4 * local_score
            
            return float(stability_score)
            
        except Exception as e:
            logger.warning(f"Pitch stability calculation failed: {e}")
            return 0.5  # Default moderate stability
    
    def extract_all_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract all anti-spoofing features from audio.
        
        Args:
            audio: Audio signal as numpy array
            
        Returns:
            Dictionary with all extracted features
        """
        features = {
            'snr': self.calculate_snr(audio),
            'spectral_artifacts': self.detect_spectral_artifacts(audio),
            'background_noise': self.analyze_background_noise(audio),
            'pitch_stability': self.calculate_pitch_stability(audio)
        }
        
        logger.debug(f"Extracted features: {features}")
        return features
    
    def is_likely_cloning(self, features: Dict[str, float]) -> Tuple[bool, float, str]:
        """
        Determine if features indicate voice cloning.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Tuple of (is_cloning, confidence, reason)
        """
        indicators = []
        confidence = 0.0
        
        # Check SNR (too clean)
        if features['snr'] > 40:
            indicators.append("SNR too high (overly clean audio)")
            confidence += 0.3
        
        # Check spectral artifacts
        if features['spectral_artifacts'] > 0.3:
            indicators.append("Spectral artifacts detected")
            confidence += 0.3
        
        # Check background noise (too clean)
        if features['background_noise'] < 0.1:
            indicators.append("Insufficient background noise")
            confidence += 0.2
        
        # Check pitch stability (too stable)
        if features['pitch_stability'] < 0.2:
            indicators.append("Pitch too stable")
            confidence += 0.2
        
        is_cloning = len(indicators) >= 2  # Need at least 2 indicators
        reason = "; ".join(indicators) if indicators else "No cloning indicators"
        
        return is_cloning, confidence, reason


# Convenience function for quick feature extraction
def extract_features(audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
    """
    Quick feature extraction function.
    
    Args:
        audio: Audio signal as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary of extracted features
    """
    extractor = AudioFeatureExtractor(sample_rate=sample_rate)
    return extractor.extract_all_features(audio)
