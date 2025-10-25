import queue
from app.model.YoloModel import YoloModel


class YoloService:
    """
    A service wrapper for the YoloModel, responsible for managing video capture,
    model inference, and returning various frame outputs to upstream consumers.
    """

    def __init__(self, model_path, src_points, cap, hot_zone=None, stay_threshold=5, traffic_flow=False, num_lanes=2):
        """
        Initialize the YoloService.

        Args:
            model_path (str): Path to the YOLO model file.
            src_points (np.array): Source points for perspective transform.
            cap (cv2.VideoCapture): OpenCV video capture object.
            hot_zone (ndarray, optional): Polygon coordinates for a special zone (e.g., no-parking zone).
            stay_threshold (int): Time (in seconds) after which a vehicle is considered as staying too long in hot zone.
            traffic_flow (bool): Whether to enable traffic flow counting (crossing middle line).
            num_lanes (int): Number of lanes to draw in the bird's-eye view.
        """
        self.model = YoloModel(model_path, src_points, hot_zone, stay_threshold, traffic_flow, num_lanes)
        self.rowQueue = queue.Queue(maxsize=5)  # Stores original frames
        self.processedQueue = queue.Queue(maxsize=5)  # Stores annotated frames with tracking results
        self.birdViewQueue = queue.Queue(maxsize=5)  # Stores bird's-eye view output
        self.cap = cap
        
        # Cache for last frames to prevent flickering
        self.last_row_frame = None
        self.last_processed_frame = None
        self.last_birdview_frame = None

    @staticmethod
    def try_put(q, item):
        """
        Try to put an item into a queue without blocking.
        If queue is full, clear it and put the new item to ensure latest frame is always available.

        Args:
            q (queue.Queue): The queue to put the item into.
            item (any): The item to put into the queue.
        """
        try:
            q.put_nowait(item)
        except queue.Full:
            # Clear the queue and put the latest frame
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
            q.put_nowait(item)

    def start(self):
        """
        Start reading frames from video stream and processing them with the model.
        Processed frames are placed in their respective queues.
        """
        import time
        try:
            frame_count = 0
            while True:
                ret, frame = self.cap.read()
                if ret:
                    frame_count += 1
                    processed, row, birdView = self.model.track(frame)

                    # Update cache with latest frames
                    self.last_row_frame = row.copy()
                    self.last_processed_frame = processed.copy()
                    self.last_birdview_frame = birdView.copy()

                    # Queue the results
                    self.try_put(self.processedQueue, processed)
                    self.try_put(self.rowQueue, row)
                    self.try_put(self.birdViewQueue, birdView)
                    
                    # Small delay to prevent overwhelming the system
                    if frame_count % 10 == 0:  # Every 10 frames
                        time.sleep(0.01)  # 10ms delay
                else:
                    break
        except Exception as e:
            print(f"[YoloService] Error during processing: {e}")
        finally:
            self.release()

    def get_statistics(self):
        """
        Retrieve the current vehicle tracking statistics.

        Returns:
            dict: Includes total count, category breakdown, long stays, and crossings.
        """
        return self.model.get_statistics()

    def get_row_frame(self):
        """
        Get the latest original (unprocessed) frame from the queue.
        If queue is empty, return the last cached frame.

        Returns:
            np.ndarray or None: The raw frame if available, otherwise None.
        """
        if not self.rowQueue.empty():
            frame = self.rowQueue.get()
            self.last_row_frame = frame.copy()
            return frame
        return self.last_row_frame

    def get_processed_frame(self):
        """
        Get the latest annotated frame (with detection and tracking info).
        If queue is empty, return the last cached frame.

        Returns:
            np.ndarray or None: The processed frame if available, otherwise None.
        """
        if not self.processedQueue.empty():
            frame = self.processedQueue.get()
            self.last_processed_frame = frame.copy()
            return frame
        return self.last_processed_frame

    def get_birdView_frame(self):
        """
        Get the latest bird's-eye view frame showing vehicle trajectories.
        If queue is empty, return the last cached frame.

        Returns:
            np.ndarray or None: The bird's-eye view frame if available, otherwise None.
        """
        if not self.birdViewQueue.empty():
            frame = self.birdViewQueue.get()
            self.last_birdview_frame = frame.copy()
            return frame
        return self.last_birdview_frame

    def release(self):
        """
        Release resources including the video capture and reset tracking statistics.
        """
        self.cap.release()
        self.model.reset_statistics()
