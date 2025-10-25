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
            cap_type(str): "ip_camera", "camera" or "file"
            cap_path(str): the path of the video file or the camera ID/url
        """
        if cap_type == "ip_camera":
            self.ip_camera_url = cap_path
            self.cap = cv2.VideoCapture(self.ip_camera_url)
        elif cap_type == "camera":
            # 对于电脑摄像头，将cap_path转换为整数
            try:
                camera_id = int(cap_path)
                self.cap = cv2.VideoCapture(camera_id)
                # 设置摄像头参数以提高兼容性
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                print(f"Camera initialized with ID: {camera_id}")
            except ValueError:
                print(f"Invalid camera ID: {cap_path}")
                self.cap = None
        elif cap_type == "file":
            # 构建完整的视频文件路径
            import os
            video_path = os.path.join("./videos", cap_path)
            self.cap = cv2.VideoCapture(video_path)
            print(f"Video file initialized: {video_path}")
        else:
            print("Invalid cap_type")
