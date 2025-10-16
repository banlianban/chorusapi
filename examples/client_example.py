"""
Example client for Chorus API
Demonstrates how to use the API from Python
"""

import requests
import os
import time
from pathlib import Path

class ChorusAPIClient:
    """Client for interacting with the Chorus API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_supported_formats(self):
        """Get supported audio formats"""
        try:
            response = self.session.get(f"{self.base_url}/supported-formats")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"error": str(e)}
    
    def extract_chorus(self, audio_file_path, duration=30, quality="high"):
        """
        Extract chorus from audio file
        
        Args:
            audio_file_path: Path to audio file
            duration: Duration of chorus to extract (10-120 seconds)
            quality: Quality setting ("low", "medium", "high")
        
        Returns:
            tuple: (success, result_data)
        """
        if not os.path.exists(audio_file_path):
            return False, {"error": "Audio file not found"}
        
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'duration': duration,
                    'quality': quality
                }
                
                response = self.session.post(
                    f"{self.base_url}/extract-chorus",
                    files=files,
                    data=data
                )
            
            return response.status_code == 200, response.json()
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def download_chorus(self, file_id, output_path=None):
        """
        Download extracted chorus file
        
        Args:
            file_id: File ID returned from extract_chorus
            output_path: Path to save the file (optional)
        
        Returns:
            tuple: (success, file_path_or_error)
        """
        try:
            response = self.session.get(f"{self.base_url}/download/{file_id}")
            
            if response.status_code == 200:
                if output_path is None:
                    output_path = f"chorus_{file_id}.wav"
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return True, output_path
            else:
                return False, f"Download failed: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def cleanup_files(self, file_id):
        """Clean up files associated with file_id"""
        try:
            response = self.session.delete(f"{self.base_url}/cleanup/{file_id}")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"error": str(e)}

def main():
    """Example usage of the Chorus API client"""
    
    # Initialize client
    client = ChorusAPIClient()
    
    print("🎵 Chorus API Client Example")
    print("=" * 40)
    
    # Check API health
    print("1. Checking API health...")
    success, result = client.health_check()
    if success:
        print(f"   ✓ API is healthy: {result}")
    else:
        print(f"   ✗ API health check failed: {result}")
        return
    
    # Get supported formats
    print("\n2. Getting supported formats...")
    success, result = client.get_supported_formats()
    if success:
        print(f"   ✓ Supported formats: {result['supported_formats']}")
    else:
        print(f"   ✗ Failed to get formats: {result}")
    
    # Get audio file path from user
    audio_file = input("\n3. Enter path to audio file (or press Enter to skip): ").strip()
    
    if audio_file and os.path.exists(audio_file):
        print(f"   Processing: {audio_file}")
        
        # Extract chorus
        print("   Extracting chorus...")
        success, result = client.extract_chorus(audio_file, duration=30, quality="high")
        
        if success and result.get('success'):
            print(f"   ✓ Chorus extracted successfully!")
            print(f"   - Start time: {result['chorus_start_sec']} seconds")
            print(f"   - File ID: {result['file_id']}")
            
            # Download the chorus
            print("   Downloading chorus...")
            file_id = result['file_id']
            success, output_path = client.download_chorus(file_id)
            
            if success:
                print(f"   ✓ Chorus saved to: {output_path}")
                
                # Ask if user wants to cleanup
                cleanup = input("   Clean up temporary files? (y/n): ").strip().lower()
                if cleanup == 'y':
                    success, result = client.cleanup_files(file_id)
                    if success:
                        print("   ✓ Files cleaned up")
                    else:
                        print(f"   ✗ Cleanup failed: {result}")
            else:
                print(f"   ✗ Download failed: {output_path}")
        else:
            print(f"   ✗ Chorus extraction failed: {result}")
    else:
        print("   Skipping chorus extraction (no valid file provided)")
    
    print("\n" + "=" * 40)
    print("Example completed!")

if __name__ == "__main__":
    main()

