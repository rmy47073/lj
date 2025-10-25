#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Test Script
Test Flask application API endpoints
"""

import requests
import json
import time

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:5000"
    
    print("=== API Test Tool ===")
    
    # Test homepage
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print(" Homepage access normal")
        else:
            print(f"Homepage access failed: {response.status_code}")
    except Exception as e:
        print(f" Cannot connect to server: {e}")
        return False
    
    # Test file list API
    try:
        response = requests.get(f"{base_url}/api/fileList")
        if response.status_code == 200:
            data = response.json()
            print(f" File list API normal, found {len(data['file_list'])} video files")
        else:
            print(f" File list API failed: {response.status_code}")
    except Exception as e:
        print(f" File list API error: {e}")
    
    # Test camera single frame capture
    try:
        test_data = {
            "cap_type": "camera",
            "cap_path": "0"
        }
        response = requests.post(f"{base_url}/api/getOneFrame", 
                               json=test_data,
                               timeout=10)
        if response.status_code == 200:
            print(" Camera single frame capture normal")
        else:
            print(f" Camera single frame capture failed: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                error_data = response.json()
                print(f"Error message: {error_data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f" Camera single frame capture error: {e}")
    
    print("\n=== Test Complete ===")
    print("If all tests pass, you can:")
    print("1. Open browser and visit: http://localhost:5000")
    print("2. Select 'Computer Camera'")
    print("3. Set camera ID to 0")
    print("4. Click 'Start Detection'")

if __name__ == "__main__":
    test_api()
