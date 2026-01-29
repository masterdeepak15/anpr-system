"""Image utility functions"""

import cv2
import numpy as np
from typing import Tuple, Optional

def calculate_iou(box1: Tuple, box2: Tuple) -> float:
    """
    Calculate Intersection over Union (IoU) between two boxes
    
    Args:
        box1: (x1, y1, x2, y2)
        box2: (x1, y1, x2, y2)
        
    Returns:
        float: IoU score
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Calculate intersection area
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    
    # Calculate union area
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - intersection_area
    
    return intersection_area / union_area if union_area > 0 else 0.0


def draw_bbox(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    label: str = "",
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> np.ndarray:
    """
    Draw bounding box on image
    
    Args:
        image: Input image
        bbox: (x1, y1, x2, y2)
        label: Optional label text
        color: Box color in BGR
        thickness: Line thickness
        
    Returns:
        np.ndarray: Image with bbox drawn
    """
    img_copy = image.copy()
    x1, y1, x2, y2 = map(int, bbox)
    
    # Draw rectangle
    cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label if provided
    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Get text size
        (text_width, text_height), _ = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Draw background rectangle for text
        cv2.rectangle(
            img_copy,
            (x1, y1 - text_height - 10),
            (x1 + text_width, y1),
            color,
            -1
        )
        
        # Draw text
        cv2.putText(
            img_copy,
            label,
            (x1, y1 - 5),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness
        )
    
    return img_copy


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization
    
    Args:
        image: Input grayscale image
        clip_limit: Threshold for contrast limiting
        
    Returns:
        np.ndarray: Enhanced image
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    return clahe.apply(image)


def median_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Apply median blur for noise reduction
    
    Args:
        image: Input image
        kernel_size: Blur kernel size (must be odd)
        
    Returns:
        np.ndarray: Blurred image
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    return cv2.medianBlur(image, kernel_size)


def gaussian_blur(
    image: np.ndarray,
    kernel_size: Tuple[int, int] = (5, 5),
    sigma: float = 0
) -> np.ndarray:
    """
    Apply Gaussian blur
    
    Args:
        image: Input image
        kernel_size: Blur kernel size
        sigma: Gaussian kernel standard deviation
        
    Returns:
        np.ndarray: Blurred image
    """
    return cv2.GaussianBlur(image, kernel_size, sigma)


def adaptive_threshold(
    image: np.ndarray,
    max_value: int = 255,
    block_size: int = 11,
    c: int = 2
) -> np.ndarray:
    """
    Apply adaptive thresholding
    
    Args:
        image: Input grayscale image
        max_value: Maximum value for thresholded pixels
        block_size: Size of pixel neighborhood
        c: Constant subtracted from mean
        
    Returns:
        np.ndarray: Binary image
    """
    return cv2.adaptiveThreshold(
        image,
        max_value,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c
    )


def resize_with_aspect_ratio(
    image: np.ndarray,
    target_size: Tuple[int, int],
    padding_color: Tuple[int, int, int] = (0, 0, 0)
) -> Tuple[np.ndarray, dict]:
    """
    Resize image while maintaining aspect ratio with padding
    
    Args:
        image: Input image
        target_size: (width, height)
        padding_color: Color for padding
        
    Returns:
        Tuple of (resized_image, transform_info)
    """
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    # Calculate scaling
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Calculate padding
    top = (target_h - new_h) // 2
    bottom = target_h - new_h - top
    left = (target_w - new_w) // 2
    right = target_w - new_w - left
    
    # Apply padding
    padded = cv2.copyMakeBorder(
        resized,
        top, bottom, left, right,
        cv2.BORDER_CONSTANT,
        value=padding_color
    )
    
    transform_info = {
        'scale': scale,
        'padding': (top, bottom, left, right),
        'original_size': (w, h),
        'resized_size': (new_w, new_h)
    }
    
    return padded, transform_info


def transform_bbox(
    bbox: Tuple[int, int, int, int],
    transform_info: dict
) -> Tuple[int, int, int, int]:
    """
    Transform bounding box coordinates based on image transformation
    
    Args:
        bbox: (x1, y1, x2, y2) in transformed image
        transform_info: Transformation information
        
    Returns:
        Tuple: Transformed bbox in original image coordinates
    """
    x1, y1, x2, y2 = bbox
    scale = transform_info['scale']
    top, _, left, _ = transform_info['padding']
    
    # Remove padding offset
    x1 = x1 - left
    y1 = y1 - top
    x2 = x2 - left
    y2 = y2 - top
    
    # Scale back to original
    x1 = int(x1 / scale)
    y1 = int(y1 / scale)
    x2 = int(x2 / scale)
    y2 = int(y2 / scale)
    
    return (x1, y1, x2, y2)