import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
from app.model.YoloModel import YoloModel


def recognize_image(image_path):
    # 确保图片文件存在
    if not os.path.exists(image_path):
        print(f"错误: 找不到图片文件 '{image_path}'")
        return
    
    # 加载图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"错误: 无法读取图片 '{image_path}'")
        return
    
    # 初始化YoloModel
    # 注意：这里使用了与test文件类似的配置，但对于单张图片，有些参数可能需要调整
    model_path = '../models/yolo11n.pt'
    
    # 这里使用默认的透视变换点，实际使用时可能需要根据图片特点调整
    src_points = np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32)
    hot_zone = np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32)
    
    yolo_model = YoloModel(
        model_path=model_path,
        traffic_flow=True,
        src_points=src_points,
        hot_zone=hot_zone,
        stay_threshold=5,
        num_lanes=2
    )
    
    # 处理图片
    processed_frame, row_frame, birdView_frame = yolo_model.track(image)
    
    # 显示结果
    cv2.namedWindow("原始图片", cv2.WINDOW_NORMAL)
    cv2.namedWindow("识别结果", cv2.WINDOW_NORMAL)
    
    cv2.imshow("原始图片", row_frame)
    cv2.imshow("识别结果", processed_frame)
    
    # 保存结果
    result_path = image_path.replace('.', '_result.')
    cv2.imwrite(result_path, processed_frame)
    print(f"识别结果已保存到: {result_path}")
    
    # 获取统计信息
    statistics = yolo_model.get_statistics()
    print("识别统计信息:")
    print(f"总识别对象数: {statistics['total_count']}")
    print(f"长时间停留对象数: {statistics['long_stay_count']}")
    print(f"穿越计数线对象数: {statistics['crossing_count']}")
    print("按类别统计:")
    for category, count in statistics['category_count'].items():
        print(f"  {category}: {count}")
    
    # 等待用户按键
    print("按 'q' 键退出")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了图片路径参数
        image_path = sys.argv[1]
    else:
        # 默认图片路径
        image_path = "../test_image.jpg"
        print(f"未提供图片路径，使用默认路径: {image_path}")
        print("使用方法: python image_recognition.py 图片路径")
    
    recognize_image(image_path)