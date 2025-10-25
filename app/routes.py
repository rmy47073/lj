import os
import cv2
import threading
import numpy as np
from functools import wraps
from app.util.Camera import Camera
from app.service.YoloService import YoloService
from flask import request, Blueprint, jsonify, Response
from flask import render_template


# Decorator for routes that require a running service
def with_service(func):
    @wraps(func)
    def wrapper(service_id, *args, **kwargs):
        try:
            service_info = yolo_services.get(service_id)
            if not service_info or 'service' not in service_info:
                return jsonify({"error": "Service not found"}), 400
            service = service_info['service']
            return func(service, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    return wrapper


# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Store multiple YoloService instances
yolo_services = {}

# Service ID management
current_service_id = 0
id_lock = threading.Lock()
thread_lock = threading.Lock()


# Utility: send frame as image/jpeg response
def send_frame_response(frame):
    if frame is None:
        return jsonify({"error": "No frame available"}), 400

    # Convert NumPy array to JPEG
    if isinstance(frame, np.ndarray):
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({"error": "Failed to encode frame"}), 500
        frame = jpeg.tobytes()

    # Ensure frame is in bytes
    if not isinstance(frame, bytes):
        return jsonify({"error": "Invalid frame format"}), 500

    return Response(frame, mimetype='image/jpeg')


# Route: Get list of video files in the ./videos directory
@api_bp.route('/fileList', methods=['GET'])
def fileList():
    folder_path = "./videos"
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return jsonify({"file_list": file_list}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to read video files: {str(e)}"}), 500


# Route: Capture and return a single frame from camera or video
@api_bp.route('/getOneFrame', methods=['POST'])
def get_one_frame():
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    cap = Camera()
    cap.setCap(cap_type, cap_path)

    ret, frame = cap.getCap().read()
    cap.getCap().release()

    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500

    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        return jsonify({"error": "Failed to encode frame"}), 500
    frame_bytes = jpeg.tobytes()

    return send_frame_response(frame_bytes)


# Route: Start a YoloService instance with specified source points and capture source
@api_bp.route('/start', methods=['POST'])
def start_service():
    print(request.json)
    src_points = request.json.get('src_points')
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')

    global current_service_id

    try:
        cap = Camera()
        cap.setCap(cap_type, cap_path)
        if not cap.getCap().isOpened():
            error_msg = f"Failed to open camera. Type: {cap_type}, Path: {cap_path}"
            print(f"[ERROR] {error_msg}")
            return jsonify({"error": error_msg}), 400

        model_path = f"yolov10n.pt"
        if not os.path.exists(model_path):
            return jsonify({"error": "Model not found"}), 400

        with id_lock:
            current_service_id += 1
            service_id = current_service_id

            # Initialize YoloService with source points
            # Keep reference to cap to prevent garbage collection
            service = YoloService(
                model_path,
                np.array([[point['x'], point['y']] for point in src_points], dtype=np.float32),
                cap.getCap()
            )
            # Store camera reference in service to prevent release
            service.camera_ref = cap

            # Start service in a background thread
            t = threading.Thread(target=service.start)
            t.daemon = True  # Set as daemon thread to allow app to exit without waiting for service to stop
            t.start()

            yolo_services[service_id] = {"service": service, "thread": t}
            return jsonify({"service_id": service_id}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


# Route: Get raw (unprocessed) frame from a running service
@api_bp.route('/getRowFrame/<int:service_id>', methods=['GET'])
@with_service
def get_row_frame(service):
    return send_frame_response(service.get_row_frame())


# Route: Get processed detection frame from a running service
@api_bp.route('/getProcessedFrame/<int:service_id>', methods=['GET'])
@with_service
def get_processed_frame(service):
    return send_frame_response(service.get_processed_frame())


# Route: Get bird's-eye view frame from a running service
@api_bp.route('/getBirdViewFrame/<int:service_id>', methods=['GET'])
@with_service
def get_bird_view_frame(service):
    return send_frame_response(service.get_birdView_frame())


# Route: Stop and release a YoloService instance
@api_bp.route('/release/<int:service_id>', methods=['GET'])
def release_service(service_id):
    with thread_lock:
        if service_id not in yolo_services:
            return jsonify({"error": "Service not found"}), 400
        service = yolo_services.pop(service_id)
        service['service'].release()
        service['thread'].join()

    return jsonify({"success": True}), 200


# Route: Get runtime statistics of a service
@api_bp.route('/getStatistics/<int:service_id>', methods=['POST'])
@with_service
def get_statistics(service):
    return jsonify({"statistics": service.get_statistics()}), 200


# Route: Serve the main HTML page
@api_bp.route('/')
def api_index():
    return render_template('index.html')
