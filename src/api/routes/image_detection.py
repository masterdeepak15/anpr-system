"""Image upload and detection API route"""

from flask import request, jsonify
import numpy as np
import cv2
import time
from werkzeug.utils import secure_filename
import os

def create_image_detection_route(app, pipeline):
    """Create image detection endpoint"""
    
    @app.route('/api/v1/detect/image', methods=['POST'])
    def detect_from_image():
        """
        Detect vehicles and plates from uploaded image
        
        Returns JSON with:
        - List of vehicles with coordinates
        - Each vehicle's plate (if detected) with coordinates and text
        - Confidence scores
        """
        
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        try:
            # Read image
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                return jsonify({"error": "Invalid image file"}), 400
            
            # Process image through pipeline
            results = process_image(image, pipeline)
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500


def process_image(image, pipeline):
    """
    Process image through detection pipeline
    
    Args:
        image: Input image (BGR format)
        pipeline: Pipeline controller instance
        
    Returns:
        dict: Detection results
    """
    results = {
        "timestamp": time.time(),
        "image_shape": image.shape,
        "vehicles": []
    }
    
    # 1. Preprocess
    processed = pipeline.preprocessor.process(image)
    
    # 2. Detect vehicles
    vehicle_detections = pipeline.vehicle_detector.detect(processed)
    
    # 3. For each vehicle, detect plate
    for vehicle_det in vehicle_detections:
        vehicle_result = {
            "bbox": vehicle_det.bbox,
            "confidence": float(vehicle_det.confidence),
            "class_id": vehicle_det.class_id,
            "class_name": vehicle_det.class_name,
            "plate": None
        }
        
        # Extract vehicle ROI
        vehicle_roi = pipeline.preprocessor.extract_roi(
            image,
            vehicle_det.bbox
        )
        
        # Detect plate in vehicle
        plate_detections = pipeline.plate_detector.detect(vehicle_roi)
        
        if plate_detections:
            # Get best plate
            best_plate = max(plate_detections, key=lambda p: p.confidence)
            
            # Extract plate ROI
            x1, y1, x2, y2 = best_plate.bbox
            plate_roi = vehicle_roi[int(y1):int(y2), int(x1):int(x2)]
            
            if plate_roi.size > 0:
                # Enhance plate
                enhanced_plate = pipeline.plate_enhancer.process(plate_roi)
                
                # OCR
                ocr_result = pipeline.ocr_engine.recognize(enhanced_plate)
                
                # Validate
                is_valid = pipeline.validation_engine.validate(ocr_result.plate_text)
                
                # Calculate absolute plate coordinates
                vx1, vy1, vx2, vy2 = vehicle_det.bbox
                abs_plate_bbox = (
                    vx1 + x1,
                    vy1 + y1,
                    vx1 + x2,
                    vy1 + y2
                )
                
                vehicle_result["plate"] = {
                    "text": ocr_result.plate_text,
                    "confidence": float(ocr_result.confidence),
                    "bbox": abs_plate_bbox,
                    "character_confidences": [float(c) for c in ocr_result.character_confidences],
                    "valid": is_valid
                }
        
        results["vehicles"].append(vehicle_result)
    
    return results