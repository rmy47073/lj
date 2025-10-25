import cv2
from app.config.config import *


class Camera:
    """
    Camera class to get the video stream from the camera or file
    """
    def __init__(self):
        """
        Initialize the camera class
        """
        self.ip_camera_url = IP_CAMERA_URL
        self.cap = None

    def getCap(self):
        """
        Get the video capture object
        """
        if self.cap is None:
            raise Exception("Camera not initialized")
        return self.cap

    def setCap(self, cap_type, cap_path):
        """
        Set the video capture object
        Args:
            cap_type(str): "ip_camera" or "file"
            cap_path(str): the path of the video file or the ip camera url
        """
        if cap_type == "ip_camera":
            self.ip_camera_url = cap_path
            self.cap = cv2.VideoCapture(self.ip_camera_url)
        elif cap_type == "file":
            self.cap = cv2.VideoCapture(cap_path)
        else:
            print("Invalid cap_type")