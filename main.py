"""
Chorus API - A FastAPI-based service for extracting music chorus sections
Based on the pychorus library by vivjay30
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import uuid
import shutil
from pathlib import Path
import logging

from utils.audio_processor import AudioProcessor
from utils.file_manager import FileManager
from config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Chorus API",
    description="A powerful API for extracting music chorus sections using pychorus",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_manager = FileManager()
audio_processor = AudioProcessor()

# Pydantic models
class ChorusExtractionRequest(BaseModel):
    duration: Optional[int] = 30
    quality: Optional[str] = "high"

class ChorusExtractionResponse(BaseModel):
    success: bool
    chorus_start_sec: Optional[float] = None
    output_file_path: Optional[str] = None
    message: str
    file_id: str

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime="running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime="running"
    )

@app.post("/extract-chorus", response_model=ChorusExtractionResponse)
async def extract_chorus(
    file: UploadFile = File(..., description="Audio file to process"),
    duration: int = Form(30, description="Duration of chorus to extract in seconds"),
    quality: str = Form("high", description="Quality setting: low, medium, high")
):
    """
    Extract chorus section from uploaded audio file
    
    - **file**: Audio file (supports mp3, wav, m4a, flac)
    - **duration**: Duration of chorus to extract (default: 30 seconds)
    - **quality**: Quality setting for processing (low, medium, high)
    """
    try:
        # Validate file type
        if not file_manager.is_valid_audio_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Supported formats: mp3, wav, m4a, flac"
            )
        
        # Validate duration
        if duration < 10 or duration > 120:
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 10 and 120 seconds"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save uploaded file
        input_path = await file_manager.save_uploaded_file(file, file_id)
        
        # Generate output path
        output_filename = f"{file_id}_chorus.wav"
        output_path = file_manager.get_output_path(output_filename)
        
        # Process audio
        logger.info(f"Processing file {file.filename} with duration {duration}s")
        chorus_start_sec = await audio_processor.extract_chorus(
            input_path, 
            output_path, 
            duration, 
            quality
        )
        
        if chorus_start_sec is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract chorus from audio file"
            )
        
        logger.info(f"Chorus extracted successfully. Start time: {chorus_start_sec}s")
        
        return ChorusExtractionResponse(
            success=True,
            chorus_start_sec=chorus_start_sec,
            output_file_path=output_path,
            message="Chorus extracted successfully",
            file_id=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/download/{file_id}")
async def download_chorus(file_id: str):
    """
    Download the extracted chorus file
    
    - **file_id**: The file ID returned from the extract-chorus endpoint
    """
    try:
        output_filename = f"{file_id}_chorus.wav"
        output_path = file_manager.get_output_path(output_filename)
        
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=404,
                detail="File not found. It may have expired or been deleted."
            )
        
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="audio/wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error downloading file"
        )

@app.delete("/cleanup/{file_id}")
async def cleanup_files(file_id: str):
    """
    Clean up temporary files for a specific file ID
    
    - **file_id**: The file ID to clean up
    """
    try:
        await file_manager.cleanup_files(file_id)
        return {"message": "Files cleaned up successfully", "file_id": file_id}
        
    except Exception as e:
        logger.error(f"Error cleaning up files for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up files"
        )

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported audio formats"""
    return {
        "supported_formats": [".mp3", ".wav", ".m4a", ".flac"],
        "max_file_size": "50MB",
        "max_duration": "120 seconds"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

