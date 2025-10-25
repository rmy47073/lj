import queue
from app.model.YoloModel import YoloModel


class YoloService:
    """
    A service wrapper for the YoloModel, responsible for managing video capture,
    model inference, and returning various frame outputs to upstream consumers.
    """
    
    # 其余代码保持不变