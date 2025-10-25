import cv2
import time
import numpy as np
import cv2
from ultralytics import YOLO
from collections import defaultdict


class YoloModel:
    def __init__(self, model_path,
                 src_points,
                 hot_zone,
                 stay_threshold: int,
                 traffic_flow: bool,
                 num_lanes: int,
                 dst_points=np.array([[100, 0], [400, 0], [100, 800], [400, 800]], dtype=np.float32)):
        """
        Initialize the YoloModel class.

        Args:
            model_path (str): Path to the YOLO model.
            src_points (ndarray): 4 points for perspective transformation from original to bird's-eye view.
            hot_zone (ndarray, optional): Polygon coordinates for a special zone (e.g., no-parking zone).
            stay_threshold (int): Time (in seconds) after which a vehicle is considered as staying too long in hot zone.
            traffic_flow (bool): Whether to enable traffic flow counting (crossing middle line).
            num_lanes (int): Number of lanes to draw in the bird’s-eye view.
            dst_points (ndarray): Destination points for perspective transformation (bird’s-eye view).
        """
        self.model = YOLO(model_path)
        self.src_points = src_points
        self.dst_points = dst_points
        self.num_lanes = num_lanes
        self.M = cv2.getPerspectiveTransform(src_points, dst_points)

        # Track history for drawing paths
        self.track_history = defaultdict(list)

        # Vehicle counting
        self.vehicle_count = 0
        self.category_count = defaultdict(int)
        self.seen_track_ids = set()

        # Hot zone monitoring
        self.hot_zone = hot_zone
        self.stay_threshold = stay_threshold
        self.entry_time = {}
        self.long_stay_ids = set()

        # Traffic flow counting
        self.traffic_flow = traffic_flow
        self.crossed_ids = set()
        self.crossing_count = 0

    @staticmethod
    def draw_dashed_line(img, start, end, color, thickness, dash_length, gap_length):
        """
        Draw a dashed line between two points.

        Args:
            img: Image to draw on.
            start: Starting coordinate.
            end: Ending coordinate.
            color: Line color.
            thickness: Line thickness.
            dash_length: Length of each dash.
            gap_length: Length of gap between dashes.
        """
        total_length = int(np.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2))
        num_dashes = total_length // (dash_length + gap_length)

        for i in range(num_dashes):
            dash_start = (
                int(start[0] + (end[0] - start[0]) * (i * (dash_length + gap_length)) / total_length),
                int(start[1] + (end[1] - start[1]) * (i * (dash_length + gap_length)) / total_length)
            )
            dash_end = (
                int(start[0] + (end[0] - start[0]) * ((i * (dash_length + gap_length)) + dash_length) / total_length),
                int(start[1] + (end[1] - start[1]) * ((i * (dash_length + gap_length)) + dash_length) / total_length)
            )
            cv2.line(img, dash_start, dash_end, color, thickness)

    def draw_lane_lines(self, birdView_frame):
        """
        Draw lane lines (solid and dashed) on the bird’s-eye view image.

        Args:
            birdView_frame: Image to draw lane lines on.
        """
        left_line_start = tuple(map(int, self.dst_points[0]))
        left_line_end = tuple(map(int, self.dst_points[2]))
        right_line_start = tuple(map(int, self.dst_points[1]))
        right_line_end = tuple(map(int, self.dst_points[3]))

        # Draw solid boundary lines
        cv2.line(birdView_frame, left_line_start, left_line_end, (255, 255, 255), 2)
        cv2.line(birdView_frame, right_line_start, right_line_end, (255, 255, 255), 2)

        # Draw dashed centerlines for multiple lanes
        for i in range(1, self.num_lanes):
            alpha = i / self.num_lanes
            dashed_start = (
                int(left_line_start[0] + alpha * (right_line_start[0] - left_line_start[0])),
                int(left_line_start[1] + alpha * (right_line_start[1] - left_line_start[1]))
            )
            dashed_end = (
                int(left_line_end[0] + alpha * (right_line_end[0] - left_line_end[0])),
                int(left_line_end[1] + alpha * (right_line_end[1] - left_line_end[1]))
            )
            self.draw_dashed_line(birdView_frame, dashed_start, dashed_end, (255, 255, 255), 2, 20, 10)

    def track(self, frame):
        """
        Perform tracking and annotation on a single frame.

        Args:
            frame: Input video frame.

        Returns:
            annotated_frame: Frame with visual annotations.
            frame: Original frame (unchanged).
            birdView_frame: Bird’s-eye view frame with trajectory and lanes.
        """
        results = self.model.track(frame, persist=True, show=False, verbose=False)

        boxes = results[0].boxes.xywh.cpu()
        
        # 处理跟踪ID可能为None的情况
        if results[0].boxes.id is not None:
            track_ids = results[0].boxes.id.int().cpu().tolist()
        else:
            # 如果没有跟踪ID，生成临时ID
            track_ids = list(range(len(boxes)))
            
        cls_indices = results[0].boxes.cls.int().cpu().tolist()
        class_names = self.model.names

        annotated_frame = results[0].plot()
        birdView_frame = np.zeros((800, 500, 3), dtype=np.uint8)
        self.draw_lane_lines(birdView_frame)

        for box, track_id, cls_idx in zip(boxes, track_ids, cls_indices):
            class_name = class_names[cls_idx]

            # Count new vehicle appearances
            if track_id not in self.seen_track_ids:
                self.seen_track_ids.add(track_id)
                self.vehicle_count += 1
                self.category_count[class_name] += 1

            x, y, w, h = box
            track = self.track_history[track_id]
            track.append((float(x), float(y)))
            if len(track) > 30:
                track.pop(0)

            # Draw trajectory on original frame
            points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

            # Draw trajectory on bird’s-eye view
            for point in track:
                src_point = np.array([[[point[0], point[1]]]], dtype=np.float32)
                dst_point = cv2.perspectiveTransform(src_point, self.M)
                bx, by = dst_point[0][0]
                cv2.circle(birdView_frame, (int(bx), int(by)), 5, (0, 255, 0), -1)

            # Hot zone logic (for detecting long stay)
            if self.hot_zone is not None:
                dst_point = cv2.perspectiveTransform(np.array([[[x, y]]], dtype=np.float32), self.M)
                bx, by = dst_point[0][0]
                if cv2.pointPolygonTest(self.hot_zone, (int(bx), int(by)), False) >= 0:
                    if track_id not in self.entry_time:
                        self.entry_time[track_id] = time.time()
                    elif time.time() - self.entry_time[track_id] > self.stay_threshold:
                        self.long_stay_ids.add(track_id)
                elif track_id in self.entry_time:
                    del self.entry_time[track_id]

            # Traffic flow logic (count vehicles crossing middle line)
            if self.traffic_flow:
                center_y = y
                prev_positions = self.track_history[track_id][-2:] if len(self.track_history[track_id]) >= 2 else []
                frame_height = frame.shape[0]
                middle_line_y = frame_height // 2

                if len(prev_positions) == 2:
                    prev_y = prev_positions[0][1]
                    curr_y = center_y
                    if (prev_y < middle_line_y <= curr_y) or (prev_y > middle_line_y >= curr_y):
                        if track_id not in self.crossed_ids:
                            self.crossed_ids.add(track_id)
                            self.crossing_count += 1

            # Label the ID in bird’s-eye view
            if track:
                src_point = np.array([[[track[-1][0], track[-1][1]]]], dtype=np.float32)
                dst_point = cv2.perspectiveTransform(src_point, self.M)
                bx, by = dst_point[0][0]
                cv2.putText(birdView_frame, f"ID:{track_id}", (int(bx), int(by) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        return annotated_frame, frame, birdView_frame

    def get_statistics(self):
        """
        Get current statistics.

        Returns:
            dict: Total vehicles, category counts, long stays, and flow crossing count.
        """
        return {
            "total_count": self.vehicle_count,
            "category_count": self.category_count,
            "long_stay_count": len(self.long_stay_ids),
            "crossing_count": self.crossing_count,
        }

    def reset_statistics(self):
        """
        Reset all statistical counters and trackers.
        """
        self.vehicle_count = 0
        self.category_count = defaultdict(int)
        self.seen_track_ids = set()
        self.entry_time.clear()
        self.long_stay_ids = set()
        self.crossing_count = 0
        self.crossed_ids.clear()
