import cv2
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
from app.model.YoloModel import YoloModel

OUTPUT = True
SAVE = False
model_path = '../models/yolo11n.pt'

if OUTPUT:
    cv2.namedWindow("birdView", cv2.WINDOW_NORMAL)
    cv2.namedWindow("row", cv2.WINDOW_NORMAL)
    cv2.namedWindow("processed", cv2.WINDOW_NORMAL)


yoloModel = YoloModel(model_path=model_path, traffic_flow=True,
                      src_points=np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32),
                      hot_zone=np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32),
                      stay_threshold=5,
                      num_lanes=2)

# 尝试打开视频文件，如果失败则使用网络摄像头
cap = cv2.VideoCapture("../videos/test.mp4")
if not cap.isOpened():
    print("警告: 无法打开视频文件 ../videos/test.mp4，将使用网络摄像头作为备选")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误: 无法打开网络摄像头，请检查摄像头连接或创建测试视频文件")
        exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("视频流已结束或无法读取帧")
        break

    processed_frame, row_frame, birdView_frame = yoloModel.track(frame)
    if OUTPUT:
        cv2.imshow("processed", processed_frame)
        cv2.imshow("row", row_frame)
        cv2.imshow("birdView", birdView_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(yoloModel.get_statistics())
        break

cv2.destroyAllWindows()
