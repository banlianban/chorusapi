"""
Audio processing utilities using pychorus for chorus extraction
"""

import os
import asyncio
from pathlib import Path
from pychorus import find_and_output_chorus
import librosa
import soundfile as sf
import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.min_duration = 10  # seconds
        self.max_duration = 120  # seconds
    
    async def extract_chorus(
        self, 
        input_path: str, 
        output_path: str, 
        duration: int = 30,
        quality: str = "high"
    ) -> Optional[float]:
        """
        Extract chorus section from audio file using pychorus
        
        Args:
            input_path: Path to input audio file
            output_path: Path to save extracted chorus
            duration: Duration of chorus to extract in seconds
            quality: Quality setting (low, medium, high)
        
        Returns:
            Start time of chorus in seconds, or None if extraction failed
        """
        try:
            # Validate input file
            if not self._validate_input_file(input_path):
                logger.error(f"Invalid input file: {input_path}")
                return None
            
            # Validate duration
            if not self._validate_duration(duration):
                logger.error(f"Invalid duration: {duration}")
                return None
            
            # Convert to WAV if necessary for better processing
            wav_path = await self._convert_to_wav(input_path)
            
            # Run chorus extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            chorus_start_sec = await loop.run_in_executor(
                None, 
                self._extract_chorus_sync, 
                wav_path, 
                output_path, 
                duration,
                quality
            )
            
            # Clean up temporary WAV file if it was created
            if wav_path != input_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return chorus_start_sec
            
        except Exception as e:
            logger.error(f"Error extracting chorus: {str(e)}")
            return None
    
    def _extract_chorus_sync(
        self, 
        input_path: str, 
        output_path: str, 
        duration: int,
        quality: str
    ) -> Optional[float]:
        """Synchronous chorus extraction using pychorus"""
        try:
            # Adjust parameters based on quality setting
            if quality == "low":
                # Faster processing, lower accuracy
                pass
            elif quality == "medium":
                # Balanced processing
                pass
            elif quality == "high":
                # Slower processing, higher accuracy
                pass
            
            # Use pychorus to find and extract chorus
            chorus_start_sec = find_and_output_chorus(
                input_path, 
                output_path, 
                duration
            )
            
            if chorus_start_sec is not None:
                logger.info(f"Chorus extracted successfully. Start time: {chorus_start_sec}s")
            else:
                logger.warning("No chorus found in the audio file")
            
            return chorus_start_sec
            
        except Exception as e:
            logger.error(f"Error in sync chorus extraction: {str(e)}")
            return None
    
    async def _convert_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format for better processing"""
        try:
            input_file = Path(input_path)
            
            # If already WAV, return original path
            if input_file.suffix.lower() == '.wav':
                return input_path
            
            # Convert to WAV
            wav_path = input_file.with_suffix('.wav')
            
            # Load audio with librosa
            y, sr = librosa.load(input_path, sr=None)
            
            # Save as WAV
            sf.write(str(wav_path), y, sr)
            
            logger.info(f"Converted {input_path} to {wav_path}")
            return str(wav_path)
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {str(e)}")
            return input_path  # Return original path if conversion fails
    
    def _validate_input_file(self, input_path: str) -> bool:
        """Validate input audio file"""
        try:
            if not os.path.exists(input_path):
                logger.error(f"File does not exist: {input_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(input_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes")
                return False
            
            # Check file extension
            file_ext = Path(input_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Unsupported file format: {file_ext}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating input file: {str(e)}")
            return False
    
    def _validate_duration(self, duration: int) -> bool:
        """Validate duration parameter"""
        return self.min_duration <= duration <= self.max_duration
    
    async def get_audio_info(self, input_path: str) -> Optional[dict]:
        """Get audio file information"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            duration = len(y) / sr
            
            return {
                "sample_rate": sr,
                "duration": duration,
                "channels": 1 if y.ndim == 1 else y.shape[0],
                "samples": len(y)
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return None
    
    def cleanup_temp_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up {file_path}: {str(e)}")

