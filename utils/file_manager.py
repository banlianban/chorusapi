"""
File management utilities for handling audio file uploads and storage
"""

import os
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from typing import List
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.output_dir = Path("outputs")
        self.temp_dir = Path("temp")
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
    
    def is_valid_audio_file(self, filename: str) -> bool:
        """Check if the uploaded file is a valid audio format"""
        if not filename:
            return False
        
        valid_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        file_extension = Path(filename).suffix.lower()
        return file_extension in valid_extensions
    
    async def save_uploaded_file(self, file: UploadFile, file_id: str) -> str:
        """Save uploaded file to the uploads directory"""
        try:
            # Get file extension
            file_extension = Path(file.filename).suffix.lower()
            input_filename = f"{file_id}{file_extension}"
            input_path = self.upload_dir / input_filename
            
            # Save file asynchronously
            async with aiofiles.open(input_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved: {input_path}")
            return str(input_path)
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise
    
    def get_output_path(self, filename: str) -> str:
        """Get the full path for output file"""
        return str(self.output_dir / filename)
    
    def get_upload_path(self, filename: str) -> str:
        """Get the full path for uploaded file"""
        return str(self.upload_dir / filename)
    
    async def cleanup_files(self, file_id: str):
        """Clean up temporary files for a specific file ID"""
        try:
            # Find and delete files with the file_id
            for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
                for file_path in directory.glob(f"{file_id}*"):
                    if file_path.is_file():
                        file_path.unlink()
                        logger.info(f"Deleted file: {file_path}")
            
            logger.info(f"Cleanup completed for file_id: {file_id}")
            
        except Exception as e:
            logger.error(f"Error during cleanup for {file_id}: {str(e)}")
            raise
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path)
    
    def list_files_by_id(self, file_id: str) -> List[str]:
        """List all files associated with a file_id"""
        files = []
        for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
            for file_path in directory.glob(f"{file_id}*"):
                if file_path.is_file():
                    files.append(str(file_path))
        return files

