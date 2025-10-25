import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
from app.model.YoloModel import YoloModel

# 设置参数
OUTPUT = True  # 是否显示窗口
SAVE = False   # 是否保存结果
model_path = '../models/yolov10n.pt'  # 使用yolov10模型

# 摄像头ID，0通常是默认摄像头，多个摄像头时可以尝试1,2等
CAMERA_ID = 0

# 如果要显示窗口，创建窗口
if OUTPUT:
    cv2.namedWindow("birdView", cv2.WINDOW_NORMAL)
    cv2.namedWindow("row", cv2.WINDOW_NORMAL)
    cv2.namedWindow("processed", cv2.WINDOW_NORMAL)

# 初始化YOLO模型
yoloModel = YoloModel(model_path=model_path, 
                      traffic_flow=True,  # 启用交通流计数
                      src_points=np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32),
                      hot_zone=None,  # 可以设置热区，格式与src_points类似
                      stay_threshold=5,  # 物体在热区停留多少秒会被认为是长时间停留
                      num_lanes=2)  # 车道数量

# 尝试打开电脑摄像头
print(f"正在尝试连接电脑摄像头(ID: {CAMERA_ID})...")
cap = cv2.VideoCapture(CAMERA_ID)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print(f"错误: 无法打开电脑摄像头(ID: {CAMERA_ID})。请检查:")
    print("1. 摄像头是否正确连接")
    print("2. 摄像头是否被其他程序占用")
    print("3. 尝试修改CAMERA_ID参数(0,1,2等)")
    exit(1)

print("摄像头连接成功！开始进行目标检测和跟踪...")
print("按 'q' 键退出程序")

# 主循环
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头帧，程序结束")
        break

    # 使用YOLO模型进行跟踪和检测
    processed_frame, row_frame, birdView_frame = yoloModel.track(frame)
    
    # 显示结果
    if OUTPUT:
        cv2.imshow("processed", processed_frame)  # 显示处理后的画面(带检测框和轨迹)
        cv2.imshow("row", row_frame)  # 显示原始画面
        cv2.imshow("birdView", birdView_frame)  # 显示鸟瞰图
    
    # 检查按键
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        # 退出时显示统计信息
        statistics = yoloModel.get_statistics()
        print("\n统计信息:")
        print(f"总检测对象数: {statistics['total_count']}")
        print(f"各类别对象数: {dict(statistics['category_count'])}")
        print(f"长时间停留对象数: {statistics['long_stay_count']}")
        print(f"穿越计数线对象数: {statistics['crossing_count']}")
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
print("程序已退出，资源已释放")