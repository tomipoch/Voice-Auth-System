#!/usr/bin/env python3
"""
Pipeline de preprocesamiento de audio para datasets académicos.
Maneja VoxCeleb, ASVspoof y otros datasets con normalización estándar.
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """Procesador de audio para datasets biométricos."""
    
    def __init__(self, target_sr: int = 16000, segment_length: Optional[float] = None):
        self.target_sr = target_sr
        self.segment_length = segment_length  # seconds
        self.segment_samples = int(segment_length * target_sr) if segment_length else None
        
    def load_and_normalize(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Carga y normaliza archivo de audio."""
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)
            
            # Remove silence
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # Normalize
            audio = audio / (np.max(np.abs(audio)) + 1e-8)
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"Error processing {audio_path}: {e}")
            return None, None
    
    def segment_audio(self, audio: np.ndarray, sr: int) -> List[np.ndarray]:
        """Segmenta audio en chunks de longitud fija."""
        if not self.segment_samples:
            return [audio]
        
        segments = []
        audio_length = len(audio)
        
        if audio_length < self.segment_samples:
            # Pad if too short
            padded = np.pad(audio, (0, self.segment_samples - audio_length), mode='constant')
            segments.append(padded)
        else:
            # Split into segments
            num_segments = audio_length // self.segment_samples
            for i in range(num_segments):
                start = i * self.segment_samples
                end = start + self.segment_samples
                segments.append(audio[start:end])
            
            # Handle remainder
            remainder = audio_length % self.segment_samples
            if remainder > self.segment_samples // 2:  # Keep if > 50% of segment length
                last_segment = audio[-self.segment_samples:]
                segments.append(last_segment)
        
        return segments
    
    def extract_features(self, audio: np.ndarray, sr: int, feature_type: str = "raw") -> np.ndarray:
        """Extrae características del audio."""
        if feature_type == "raw":
            return audio
        elif feature_type == "mfcc":
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
            return mfcc.T  # [time, features]
        elif feature_type == "spectrogram":
            stft = librosa.stft(audio, n_fft=1024, hop_length=256)
            magnitude = np.abs(stft)
            return magnitude.T
        elif feature_type == "melspectrogram":
            mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80)
            log_mel = librosa.power_to_db(mel_spec)
            return log_mel.T
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")

class VoxCelebPreprocessor:
    """Preprocesador específico para VoxCeleb datasets."""
    
    def __init__(self, dataset_path: str, output_path: str, target_sr: int = 16000):
        self.dataset_path = Path(dataset_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.preprocessor = AudioPreprocessor(target_sr=target_sr)
        
    def create_manifest(self) -> pd.DataFrame:
        """Crea manifest con metadatos del dataset."""
        data = []
        
        # Find all audio files
        for audio_file in self.dataset_path.rglob("*.wav"):
            parts = audio_file.parts
            
            # Extract speaker ID from path structure
            # VoxCeleb structure: .../id*/*/filename.wav
            speaker_id = None
            for part in parts:
                if part.startswith('id'):
                    speaker_id = part
                    break
            
            if speaker_id:
                data.append({
                    'file_path': str(audio_file),
                    'speaker_id': speaker_id,
                    'duration': self._get_duration(audio_file),
                    'split': self._determine_split(audio_file)
                })
        
        return pd.DataFrame(data)
    
    def _get_duration(self, audio_path: Path) -> float:
        """Obtiene duración del archivo de audio."""
        try:
            info = sf.info(str(audio_path))
            return info.duration
        except:
            return 0.0
    
    def _determine_split(self, audio_path: Path) -> str:
        """Determina si el archivo pertenece a train/dev/test."""
        path_str = str(audio_path)
        if 'dev' in path_str or 'train' in path_str:
            return 'train'
        elif 'test' in path_str:
            return 'test'
        else:
            return 'train'  # default
    
    def process_dataset(self, num_workers: int = 4) -> None:
        """Procesa todo el dataset."""
        logger.info("Creating VoxCeleb manifest...")
        manifest = self.create_manifest()
        
        # Save manifest
        manifest_path = self.output_path / "manifest.csv"
        manifest.to_csv(manifest_path, index=False)
        logger.info(f"Manifest saved to {manifest_path}")
        
        # Process audio files
        logger.info("Processing audio files...")
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for _, row in manifest.iterrows():
                future = executor.submit(self._process_single_file, row)
                futures.append(future)
            
            for future in tqdm(as_completed(futures), total=len(futures)):
                try:
                    result = future.result()
                    if result:
                        logger.debug(f"Processed: {result}")
                except Exception as e:
                    logger.error(f"Processing error: {e}")
    
    def _process_single_file(self, row: pd.Series) -> Optional[str]:
        """Procesa un archivo individual."""
        input_path = row['file_path']
        relative_path = Path(input_path).relative_to(self.dataset_path)
        output_path = self.output_path / "processed" / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load and process
        audio, sr = self.preprocessor.load_and_normalize(input_path)
        if audio is None:
            return None
        
        # Save processed audio
        sf.write(str(output_path), audio, sr)
        return str(output_path)

class ASVspoofPreprocessor:
    """Preprocesador específico para ASVspoof datasets."""
    
    def __init__(self, dataset_path: str, output_path: str, protocol: str = "LA"):
        self.dataset_path = Path(dataset_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.protocol = protocol  # LA (Logical Access) or PA (Physical Access)
        self.preprocessor = AudioPreprocessor(target_sr=16000, segment_length=4.0)
    
    def load_protocol_file(self, split: str = "train") -> pd.DataFrame:
        """Carga archivo de protocolo ASVspoof."""
        protocol_file = self.dataset_path / f"ASVspoof2019_{self.protocol}_{split}/ASVspoof2019_{self.protocol}_{split}.txt"
        
        if not protocol_file.exists():
            logger.warning(f"Protocol file not found: {protocol_file}")
            return pd.DataFrame()
        
        # Load protocol: speaker_id, filename, env_id, attack_id, label
        data = []
        with open(protocol_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    data.append({
                        'speaker_id': parts[0],
                        'filename': parts[1],
                        'env_id': parts[2],
                        'attack_id': parts[3],
                        'label': parts[4],  # 'bonafide' or 'spoof'
                        'split': split
                    })
        
        return pd.DataFrame(data)
    
    def create_manifest(self) -> pd.DataFrame:
        """Crea manifest completo del dataset."""
        all_data = []
        
        for split in ['train', 'dev', 'eval']:
            split_data = self.load_protocol_file(split)
            if not split_data.empty:
                all_data.append(split_data)
        
        if all_data:
            manifest = pd.concat(all_data, ignore_index=True)
            
            # Add full file paths
            manifest['file_path'] = manifest.apply(
                lambda row: str(self.dataset_path / f"ASVspoof2019_{self.protocol}_{row['split']}" / "flac" / f"{row['filename']}.flac"),
                axis=1
            )
            
            return manifest
        
        return pd.DataFrame()
    
    def process_dataset(self, num_workers: int = 4) -> None:
        """Procesa dataset ASVspoof."""
        logger.info(f"Processing ASVspoof 2019 {self.protocol} protocol...")
        
        manifest = self.create_manifest()
        if manifest.empty:
            logger.error("No data found in manifest")
            return
        
        # Save manifest
        manifest_path = self.output_path / f"asvspoof2019_{self.protocol.lower()}_manifest.csv"
        manifest.to_csv(manifest_path, index=False)
        
        # Process files
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for _, row in manifest.iterrows():
                future = executor.submit(self._process_single_file, row)
                futures.append(future)
            
            for future in tqdm(as_completed(futures), total=len(futures)):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Processing error: {e}")
    
    def _process_single_file(self, row: pd.Series) -> Optional[str]:
        """Procesa archivo individual de ASVspoof."""
        input_path = row['file_path']
        if not Path(input_path).exists():
            return None
        
        # Create output path
        output_dir = self.output_path / "processed" / row['split']
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{row['filename']}.wav"
        
        # Load and process
        audio, sr = self.preprocessor.load_and_normalize(input_path)
        if audio is None:
            return None
        
        # Segment audio
        segments = self.preprocessor.segment_audio(audio, sr)
        
        # Save first segment (or concatenate if multiple)
        if segments:
            sf.write(str(output_path), segments[0], sr)
        
        return str(output_path)

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Preprocesamiento de datasets de audio")
    parser.add_argument("--dataset", required=True, 
                       choices=["voxceleb1", "voxceleb2", "asvspoof2019", "asvspoof2021"],
                       help="Dataset a procesar")
    parser.add_argument("--input-path", required=True, help="Ruta del dataset original")
    parser.add_argument("--output-path", required=True, help="Ruta de salida procesada")
    parser.add_argument("--protocol", default="LA", choices=["LA", "PA"], 
                       help="Protocolo para ASVspoof (LA o PA)")
    parser.add_argument("--workers", type=int, default=4, help="Número de workers paralelos")
    parser.add_argument("--target-sr", type=int, default=16000, help="Sample rate objetivo")
    
    args = parser.parse_args()
    
    print(f"🎵 **PREPROCESANDO DATASET: {args.dataset.upper()}**")
    print("=" * 60)
    print(f"📁 Input: {args.input_path}")
    print(f"📁 Output: {args.output_path}")
    print(f"⚙️ Workers: {args.workers}")
    print(f"🎚️ Target SR: {args.target_sr} Hz")
    
    if args.dataset.startswith("voxceleb"):
        preprocessor = VoxCelebPreprocessor(
            dataset_path=args.input_path,
            output_path=args.output_path,
            target_sr=args.target_sr
        )
        preprocessor.process_dataset(num_workers=args.workers)
        
    elif args.dataset.startswith("asvspoof"):
        preprocessor = ASVspoofPreprocessor(
            dataset_path=args.input_path,
            output_path=args.output_path,
            protocol=args.protocol
        )
        preprocessor.process_dataset(num_workers=args.workers)
    
    print("✅ Preprocesamiento completado!")

if __name__ == "__main__":
    main()