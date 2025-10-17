"""
Chorus API - A FastAPI-based service for extracting music chorus sections
Based on the pychorus library by vivjay30
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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

# Optionally mount a static directory in the future (e.g., for assets)
# app.mount("/static", StaticFiles(directory="static"), name="static")

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


@app.get("/index.html")
async def serve_index_html():
    """Serve the static homepage HTML file"""
    index_path = Path(__file__).parent / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(path=str(index_path), media_type="text/html")

@app.post("/extract-chorus", response_model=ChorusExtractionResponse)
async def extract_chorus(
    file: UploadFile = File(..., description="Audio file to process"),
    duration: int = Form(30, description="Duration of chorus to extract in seconds"),
    quality: str = Form("high", description="Quality setting: low, medium, high"),
    long_audio_mode: bool = Form(False, description="Allow very long audio without 413"),
    downmix: bool = Form(True, description="Allow downmix to mono if required"),
    resample: bool = Form(True, description="Allow resample if sample rate unsupported")
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
        
        # Optional: preflight validation before heavy processing
        ok, metrics, preflight_err = await audio_processor.preflight_validate(
            input_path,
            min_seconds=30,
            max_seconds=15*60,
            long_audio_mode=long_audio_mode,
            mono_required=False,           # set True if your pipeline strictly requires mono
            allow_downmix=downmix,
            allow_resample=resample,
            min_sample_rate=16_000,
            max_sample_rate=192_000,
            silence_rms_dbfs_threshold=-45.0,
        )

        if not ok and preflight_err is not None:
            err_type = preflight_err.get("type", "")
            # map structured errors to status codes
            if err_type == "Audio.TooShort":
                status_code = 422
            elif err_type == "Audio.TooLong":
                status_code = 413
            elif err_type == "Audio.SilentOrLowRMS":
                status_code = 422
            elif err_type == "Audio.MonoRequired":
                status_code = 422
            elif err_type == "Audio.SampleRateUnsupported":
                status_code = 422
            else:
                status_code = 422
            raise HTTPException(status_code=status_code, detail=preflight_err)

        # Process audio
        logger.info(f"Processing file {file.filename} with duration {duration}s")
        chorus_start_sec = await audio_processor.extract_chorus(
            input_path, 
            output_path, 
            duration, 
            quality
        )
        
        if chorus_start_sec is None:
            # Map known reasons to suitable HTTP status codes
            reason = getattr(audio_processor, "last_error_reason", None) or "Failed to extract chorus from audio file"
            reason_lower = reason.lower()
            if "unsupported file format" in reason_lower or "invalid file type" in reason_lower:
                status_code = 400
            elif "file too large" in reason_lower:
                status_code = 413  # Payload Too Large
            elif "does not exist" in reason_lower:
                status_code = 400
            elif "invalid duration" in reason_lower:
                status_code = 400
            elif "no chorus found" in reason_lower:
                status_code = 422  # Unprocessable Entity
            else:
                # Default to client-unprocessable rather than server error to surface reason
                status_code = 422

            # Include any preflight metrics we computed earlier for transparency
            detail = {
                "type": "Extraction.Failed",
                "message": reason,
                "metrics": metrics if 'metrics' in locals() and isinstance(metrics, dict) else None,
            }
            raise HTTPException(status_code=status_code, detail=detail)
        
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


