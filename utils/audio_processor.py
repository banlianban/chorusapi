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
from typing import Dict, Any, Tuple as TypingTuple

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.min_duration = 10  # seconds
        self.max_duration = 120  # seconds
        # Stores the latest human-readable failure reason for debugging/HTTP errors
        self.last_error_reason = None
    
    async def preflight_validate(
        self,
        input_path: str,
        *,
        min_seconds: int = 30,
        max_seconds: int = 15 * 60,
        long_audio_mode: bool = False,
        mono_required: bool = False,
        allow_downmix: bool = True,
        allow_resample: bool = True,
        min_sample_rate: int = 16_000,
        max_sample_rate: int = 192_000,
        silence_rms_dbfs_threshold: float = -45.0,
    ) -> TypingTuple[bool, Dict[str, Any], Optional[Dict[str, Any]]]:
        """Analyze audio and enforce pre-pychorus constraints.

        Returns (ok, info, error). If ok is False, error contains structured details.
        info always includes measured metrics when available.
        """
        self.last_error_reason = None
        info: Dict[str, Any] = {}
        try:
            if not os.path.exists(input_path):
                err = {
                    "type": "File.NotFound",
                    "message": "Uploaded file does not exist on server",
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # Probe via soundfile (fast, metadata) and librosa (signal)
            sf_info = sf.info(input_path)
            samplerate = int(sf_info.samplerate) if sf_info.samplerate else None
            channels = int(sf_info.channels) if sf_info.channels else None
            sf_format = sf_info.format or None
            sf_subtype = sf_info.subtype or None

            # Load small header of audio to compute metrics; for accuracy, load full
            y, sr = librosa.load(input_path, sr=None, mono=False)
            if y.ndim == 1:
                num_channels = 1
                y_mono = y
            else:
                num_channels = y.shape[0]
                # default librosa multi-channel loads as (channels, samples)
                y_mono = librosa.to_mono(y)

            duration_sec = float(y_mono.shape[-1]) / float(sr) if sr else None
            # RMS in linear, convert to dBFS; guard zero
            rms = float(np.sqrt(np.mean(np.square(y_mono)))) if y_mono.size > 0 else 0.0
            rms_dbfs = float(20.0 * np.log10(max(rms, 1e-12)))

            # codec best-effort mapping
            codec = sf_subtype or None

            info.update({
                "duration_sec": duration_sec,
                "samplerate": samplerate or sr,
                "channels": channels or num_channels,
                "rms_dbfs": rms_dbfs,
                "format": sf_format,
                "codec": codec,
            })

            # Too short
            if duration_sec is not None and duration_sec < float(min_seconds):
                err = {
                    "type": "Audio.TooShort",
                    "message": "Audio duration is shorter than required minimum",
                    "min_seconds": float(min_seconds),
                    "actual": float(duration_sec),
                    "metrics": info,
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # Too long (when long_audio_mode is False)
            if not long_audio_mode and duration_sec is not None and duration_sec > float(max_seconds):
                err = {
                    "type": "Audio.TooLong",
                    "message": "Audio duration exceeds maximum allowed; enable long_audio_mode or segment",
                    "max_seconds": float(max_seconds),
                    "actual": float(duration_sec),
                    "metrics": info,
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # Silent or low RMS
            if rms_dbfs < float(silence_rms_dbfs_threshold):
                err = {
                    "type": "Audio.SilentOrLowRMS",
                    "message": "Audio loudness below threshold",
                    "threshold_dbfs": float(silence_rms_dbfs_threshold),
                    "actual_dbfs": float(rms_dbfs),
                    "metrics": info,
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # Mono required but input multi-channel and downmix not allowed
            if mono_required and (channels or num_channels) and (channels or num_channels) > 1 and not allow_downmix:
                err = {
                    "type": "Audio.MonoRequired",
                    "message": "Mono required but multi-channel provided and downmix disabled",
                    "metrics": info,
                    "hints": {"allow_downmix": True}
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # Sample rate unsupported and resample not allowed
            effective_sr = samplerate or sr
            if effective_sr and (effective_sr < min_sample_rate or effective_sr > max_sample_rate) and not allow_resample:
                err = {
                    "type": "Audio.SampleRateUnsupported",
                    "message": "Sample rate out of supported range and resampling disabled",
                    "supported_range": [int(min_sample_rate), int(max_sample_rate)],
                    "actual": int(effective_sr),
                    "metrics": info,
                    "hints": {"allow_resample": True, "suggested": 44100},
                }
                self.last_error_reason = err["message"]
                return False, info, err

            # VBR timestamp skew check - not implemented (needs deeper parsing). Provide info only.
            # If later implemented, return type: Audio.VBRTimestampSkew

            return True, info, None

        except Exception as e:
            logger.error(f"Error during preflight validation: {str(e)}")
            self.last_error_reason = f"Preflight validation error: {str(e)}"
            return False, info, {
                "type": "Audio.PreflightError",
                "message": str(e),
                "metrics": info
            }

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
            # reset previous error state
            self.last_error_reason = None
            # Validate input file
            if not self._validate_input_file(input_path):
                logger.error(f"Invalid input file: {input_path}")
                if self.last_error_reason is None:
                    self.last_error_reason = "Invalid input file"
                return None
            
            # Validate duration
            if not self._validate_duration(duration):
                logger.error(f"Invalid duration: {duration}")
                self.last_error_reason = (
                    f"Invalid duration: {duration}. Must be between {self.min_duration} and {self.max_duration} seconds"
                )
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
            self.last_error_reason = f"Unexpected error during extraction: {str(e)}"
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
                self.last_error_reason = "No chorus found in the audio file"
            
            return chorus_start_sec
            
        except Exception as e:
            logger.error(f"Error in sync chorus extraction: {str(e)}")
            self.last_error_reason = f"Chorus extraction failed: {str(e)}"
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
            # Preserve the reason so API can surface it
            self.last_error_reason = f"Error converting to WAV: {str(e)}"
            return input_path  # Return original path if conversion fails
    
    def _validate_input_file(self, input_path: str) -> bool:
        """Validate input audio file"""
        try:
            if not os.path.exists(input_path):
                logger.error(f"File does not exist: {input_path}")
                self.last_error_reason = "Uploaded file does not exist on server"
                return False
            
            # Check file size
            file_size = os.path.getsize(input_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes")
                self.last_error_reason = (
                    f"File too large: {file_size} bytes. Max allowed is {self.max_file_size} bytes"
                )
                return False
            
            # Check file extension
            file_ext = Path(input_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Unsupported file format: {file_ext}")
                self.last_error_reason = f"Unsupported file format: {file_ext}. Supported: {sorted(self.supported_formats)}"
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating input file: {str(e)}")
            self.last_error_reason = f"Error validating input file: {str(e)}"
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


