#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera test script
Test if camera works properly
"""

import cv2
import sys

def test_camera(camera_id=0):
    """
    Test camera with specified ID
    
    Args:
        camera_id (int): Camera ID, default is 0
    """
    print(f"Testing camera ID: {camera_id}")
    
    # Try to open camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"? Cannot open camera ID: {camera_id}")
        print("Possible reasons:")
        print("1. Camera is being used by another program")
        print("2. Incorrect camera ID")
        print("3. Camera driver issues")
        print("4. Permission issues")
        return False
    
    print(f"? Successfully opened camera ID: {camera_id}")
    
    # Get camera info
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera resolution: {int(width)}x{int(height)}")
    print(f"Camera FPS: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print("? Successfully read camera frame")
        print(f"Frame shape: {frame.shape}")
    else:
        print("? Cannot read camera frame")
        cap.release()
        return False
    
    # Release camera
    cap.release()
    print("? Camera test completed")
    return True

def test_all_cameras():
    """
    Test all available cameras
    """
    print("Scanning for available cameras...")
    available_cameras = []
    
    for i in range(10):  # Test first 10 camera IDs
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
                print(f"? Found camera ID: {i}")
            cap.release()
    
    if available_cameras:
        print(f"\nFound {len(available_cameras)} available cameras: {available_cameras}")
    else:
        print("? No available cameras found")
    
    return available_cameras

if __name__ == "__main__":
    print("=== Camera Test Tool ===")
    
    if len(sys.argv) > 1:
        # Test specified camera
        try:
            camera_id = int(sys.argv[1])
            test_camera(camera_id)
        except ValueError:
            print("? Invalid camera ID, please enter a number")
    else:
        # Scan all cameras
        available = test_all_cameras()
        if available:
            print(f"\nRecommended camera ID: {available[0]}")
