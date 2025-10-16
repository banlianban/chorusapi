#!/usr/bin/env python3
"""
Startup script for Chorus API
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Start the Chorus API server"""
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Check if required directories exist
    for directory in ['uploads', 'outputs', 'temp']:
        Path(directory).mkdir(exist_ok=True)
    
    print("🎵 Starting Chorus API...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc Documentation: http://localhost:8000/redoc")
    print("🏥 Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()


