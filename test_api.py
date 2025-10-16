"""
Simple test script for the Chorus API
"""

import requests
import os
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_supported_formats():
    """Test supported formats endpoint"""
    print("\nTesting supported formats...")
    try:
        response = requests.get(f"{BASE_URL}/supported-formats")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chorus_extraction(audio_file_path):
    """Test chorus extraction with a sample audio file"""
    print(f"\nTesting chorus extraction with {audio_file_path}...")
    
    if not os.path.exists(audio_file_path):
        print(f"Audio file not found: {audio_file_path}")
        return False
    
    try:
        print("Uploading file to API...")
        # Prepare file upload
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'duration': 30,
                'quality': 'high'
            }
            
            # Make request
            print("Sending request to extract-chorus endpoint...")
            response = requests.post(
                f"{BASE_URL}/extract-chorus",
                files=files,
                data=data,
                timeout=60  # 60 second timeout
            )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"API Response: {result}")
        
        if result.get('success'):
            file_id = result.get('file_id')
            chorus_start = result.get('chorus_start_sec')
            print(f"✓ Chorus extraction successful!")
            print(f"  - File ID: {file_id}")
            print(f"  - Chorus starts at: {chorus_start} seconds")
            
            # Test download
            if file_id:
                print("Testing download...")
                download_response = requests.get(f"{BASE_URL}/download/{file_id}", timeout=30)
                if download_response.status_code == 200:
                    print("✓ Download test successful")
                    # Save downloaded file
                    output_filename = f"downloaded_chorus_{file_id}.wav"
                    with open(output_filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"✓ Chorus saved as: {output_filename}")
                else:
                    print(f"✗ Download failed: {download_response.status_code}")
                    print(f"  Response: {download_response.text}")
            
            return True
        else:
            print("✗ Chorus extraction failed")
            print(f"  Error: {result.get('message', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out - the audio file might be too large or processing is taking too long")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - make sure the API server is running")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Chorus API Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        health_ok = test_health()
        
        # Test 2: Supported formats
        formats_ok = test_supported_formats()
        
        # Test 3: Chorus extraction (if audio file provided)
        print("\nEnter path to audio file for testing (or press Enter to skip):")
        try:
            audio_file = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled, skipping chorus extraction test")
            audio_file = ""
        
        extraction_ok = True
        
        if audio_file and os.path.exists(audio_file):
            print(f"Found audio file: {audio_file}")
            extraction_ok = test_chorus_extraction(audio_file)
        elif audio_file:
            print(f"Audio file not found: {audio_file}")
            print("Skipping chorus extraction test")
            extraction_ok = False
        else:
            print("Skipping chorus extraction test (no audio file provided)")
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Results:")
        print(f"Health Check: {'✓' if health_ok else '✗'}")
        print(f"Supported Formats: {'✓' if formats_ok else '✗'}")
        print(f"Chorus Extraction: {'✓' if extraction_ok else '✗'}")
        
        if all([health_ok, formats_ok, extraction_ok]):
            print("\nAll tests passed! 🎉")
        else:
            print("\nSome tests failed. Check the output above for details.")
            
    except Exception as e:
        print(f"\nUnexpected error in main: {e}")
        import traceback
        traceback.print_exc()
    
    # Keep the window open
    print("\nPress Enter to exit...")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
