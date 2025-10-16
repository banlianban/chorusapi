"""
Configuration settings for the Chorus API
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""
    
    def __init__(self):
        # API Settings
        self.API_TITLE = "Chorus API"
        self.API_VERSION = "1.0.0"
        self.API_DESCRIPTION = "A powerful API for extracting music chorus sections using pychorus"
        
        # Server Settings
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", 8000))
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # File Settings
        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
        self.TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
        self.FILE_RETENTION_HOURS = int(os.getenv("FILE_RETENTION_HOURS", 24))
        
        # Audio Processing Settings
        self.MIN_DURATION = int(os.getenv("MIN_DURATION", 10))  # seconds
        self.MAX_DURATION = int(os.getenv("MAX_DURATION", 120))  # seconds
        self.DEFAULT_DURATION = int(os.getenv("DEFAULT_DURATION", 30))  # seconds
        
        # Supported audio formats
        self.SUPPORTED_FORMATS = {
            '.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'
        }
        
        # Quality settings
        self.QUALITY_SETTINGS = {
            "low": {"sample_rate": 22050, "bit_depth": 16},
            "medium": {"sample_rate": 44100, "bit_depth": 16},
            "high": {"sample_rate": 44100, "bit_depth": 24}
        }
        
        # CORS Settings
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
        self.CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        
        # Logging Settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Security Settings
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        for directory in [self.UPLOAD_DIR, self.OUTPUT_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_upload_path(self, filename: str) -> Path:
        """Get full path for uploaded file"""
        return self.UPLOAD_DIR / filename
    
    def get_output_path(self, filename: str) -> Path:
        """Get full path for output file"""
        return self.OUTPUT_DIR / filename
    
    def get_temp_path(self, filename: str) -> Path:
        """Get full path for temporary file"""
        return self.TEMP_DIR / filename
    
    def is_valid_audio_format(self, filename: str) -> bool:
        """Check if file has valid audio format"""
        if not filename:
            return False
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.SUPPORTED_FORMATS
    
    def get_quality_settings(self, quality: str) -> dict:
        """Get quality settings for specified quality level"""
        return self.QUALITY_SETTINGS.get(quality, self.QUALITY_SETTINGS["high"])


