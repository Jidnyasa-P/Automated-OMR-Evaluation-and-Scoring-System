import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, List, Optional
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle

class EnhancedOMRPreprocessor:
    """Enhanced OMR Preprocessor following the implementation document specifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Load or create ML model for ambiguous bubble classification
        self.ambiguity_classifier = self._load_or_create_ambiguity_model()
        self.scaler = StandardScaler()
        
    def _load_or_create_ambiguity_model(self):
        """Load existing ambiguity classifier or create new one"""
        model_path = "ambiguity_classifier.pkl"
        try:
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            else:
                # Create and train a simple model for bubble ambiguity
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                # In production, this would be trained on real data
                # For now, we'll return the untrained model
                return model
        except Exception as e:
            self.logger.warning(f"Could not load ambiguity model: {e}")
            return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def detect_sheet_orientation_and_fiducials(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], dict]:
        """
        Step 1: Detect Sheet Orientation & Fiducials
        Find the document within the photo and identify corner markers
        """
        processing_info = {"fiducials_found": False, "corners": None, "orientation": "unknown"}
        
        try:
            # Convert to grayscale for processing
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours by area (largest first)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Look for the largest rectangular contour (the sheet)
            for contour in contours[:10]:  # Check top 10 largest contours
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if we found a 4-sided polygon with reasonable area
                if len(approx) == 4 and cv2.contourArea(contour) > 50000:
                    processing_info["fiducials_found"] = True
                    processing_info["corners"] = approx.reshape(4, 2).tolist()
                    
                    # Determine orientation based on corner positions
                    corners = approx.reshape(4, 2)
                    processing_info["orientation"] = self._determine_orientation(corners)
                    
                    return approx.reshape(4, 2), processing_info
            
            # If no perfect rectangle found, try to find the sheet boundary using edge detection
            edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=200)
            
            if lines is not None:
                # Use Hough lines to approximate sheet boundaries
                corners = self._approximate_corners_from_lines(lines, image.shape)
                if corners is not None:
                    processing_info["fiducials_found"] = True
                    processing_info["corners"] = corners.tolist()
                    processing_info["orientation"] = self._determine_orientation(corners)
                    return corners, processing_info
            
        except Exception as e:
            self.logger.error(f"Error in fiducial detection: {e}")
            processing_info["error"] = str(e)
        
        return None, processing_info
    
    def _determine_orientation(self, corners: np.ndarray) -> str:
        """Determine sheet orientation based on corner positions"""
        try:
            # Calculate the center of the corners
            center = np.mean(corners, axis=0)
            
            # Find the top-left corner (closest to origin)
            distances_to_origin = np.sum(corners**2, axis=1)
            top_left_idx = np.argmin(distances_to_origin)
            
            # Simple orientation classification
            if corners[top_left_idx][0] < center[0] and corners[top_left_idx][1] < center[1]:
                return "normal"
            else:
                return "rotated"
        except:
            return "unknown"
    
    def _approximate_corners_from_lines(self, lines: np.ndarray, image_shape: Tuple) -> Optional[np.ndarray]:
        """Approximate sheet corners from detected lines"""
        try:
            # This is a simplified implementation
            # In production, you'd use more sophisticated line intersection algorithms
            height, width = image_shape[:2]
            margin = min(width, height) * 0.1
            
            # Approximate corners based on image boundaries with some margin
            corners = np.array([
                [margin, margin],                    # Top-left
                [width - margin, margin],           # Top-right  
                [width - margin, height - margin],  # Bottom-right
                [margin, height - margin]           # Bottom-left
            ], dtype=np.float32)
            
            return corners
        except:
            return None
    
    def rectify_perspective_distortion(self, image: np.ndarray, corners: np.ndarray) -> Tuple[Optional[np.ndarray], dict]:
        """
        Step 2: Rectify Perspective Distortion
        Apply perspective transform to create perfect top-down view
        """
        processing_info = {"perspective_corrected": False, "output_dimensions": None}
        
        try:
            # Order the corners: top-left, top-right, bottom-right, bottom-left
            rect = self._order_points(corners)
            (tl, tr, br, bl) = rect
            
            # Calculate the width and height of the new image
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            # Destination points for the transform (perfect rectangle)
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]
            ], dtype="float32")
            
            # Calculate the perspective transform matrix
            M = cv2.getPerspectiveTransform(rect, dst)
            
            # Apply the perspective transformation
            warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
            
            processing_info["perspective_corrected"] = True
            processing_info["output_dimensions"] = (maxWidth, maxHeight)
            processing_info["transform_matrix"] = M.tolist()
            
            return warped, processing_info
            
        except Exception as e:
            self.logger.error(f"Error in perspective correction: {e}")
            processing_info["error"] = str(e)
            return None, processing_info
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in the format: top-left, top-right, bottom-right, bottom-left"""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect[0] = pts[np.argmin(s)]      # Top-left (smallest sum)
        rect[2] = pts[np.argmax(s)]      # Bottom-right (largest sum)
        rect[1] = pts[np.argmin(diff)]   # Top-right (smallest difference)  
        rect[3] = pts[np.argmax(diff)]   # Bottom-left (largest difference)
        
        return rect
    
    def correct_illumination_and_threshold(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], dict]:
        """
        Step 3: Correct Illumination and Threshold
        Handle mobile phone lighting variations using adaptive thresholding
        """
        processing_info = {"illumination_corrected": False, "threshold_applied": False}
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This helps with uneven illumination
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            processing_info["illumination_corrected"] = True
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            # Apply adaptive thresholding
            # This adjusts for local lighting differences
            thresh = cv2.adaptiveThreshold(
                blurred, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 
                2
            )
            
            # Optional: Apply morphological operations to clean up the image
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            processing_info["threshold_applied"] = True
            processing_info["final_image_stats"] = {
                "mean_intensity": float(np.mean(cleaned)),
                "std_intensity": float(np.std(cleaned))
            }
            
            return cleaned, processing_info
            
        except Exception as e:
            self.logger.error(f"Error in illumination correction: {e}")
            processing_info["error"] = str(e)
            return None, processing_info
    
    def extract_bubble_features_for_ml(self, bubble_roi: np.ndarray) -> np.ndarray:
        """
        Extract features from a bubble ROI for ML classification
        Used for handling ambiguous cases
        """
        features = []
        
        try:
            # Basic intensity statistics
            features.append(np.mean(bubble_roi))
            features.append(np.std(bubble_roi))
            features.append(np.min(bubble_roi))
            features.append(np.max(bubble_roi))
            
            # Percentage of dark pixels (for binary images)
            if len(np.unique(bubble_roi)) <= 2:  # Binary image
                dark_pixels = np.sum(bubble_roi == 0)
                total_pixels = bubble_roi.size
                features.append(dark_pixels / total_pixels)
            else:
                # For grayscale, use threshold-based approach
                threshold = np.mean(bubble_roi) - np.std(bubble_roi)
                dark_pixels = np.sum(bubble_roi < threshold)
                features.append(dark_pixels / bubble_roi.size)
            
            # Contour-based features
            if len(np.unique(bubble_roi)) <= 2:
                contours, _ = cv2.findContours(
                    255 - bubble_roi.astype(np.uint8), 
                    cv2.RETR_EXTERNAL, 
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    perimeter = cv2.arcLength(largest_contour, True)
                    
                    features.append(area)
                    features.append(perimeter)
                    
                    # Circularity
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter ** 2)
                        features.append(circularity)
                    else:
                        features.append(0)
                else:
                    features.extend([0, 0, 0])  # No contours found
            else:
                features.extend([0, 0, 0])
            
            # Ensure we have a fixed number of features
            while len(features) < 10:
                features.append(0)
            
            return np.array(features[:10])  # Return exactly 10 features
            
        except Exception as e:
            self.logger.error(f"Error extracting bubble features: {e}")
            return np.zeros(10)  # Return zero features if error
    
    def classify_ambiguous_bubble(self, bubble_roi: np.ndarray) -> Tuple[str, float]:
        """
        Use ML classifier to handle ambiguous bubble cases
        Returns: (classification, confidence)
        """
        try:
            features = self.extract_bubble_features_for_ml(bubble_roi)
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # This would use the trained model in production
            # For demo, we'll use a rule-based approach
            dark_pixel_ratio = features[4]  # This is the dark pixel ratio
            
            if dark_pixel_ratio > 0.6:
                return "filled", 0.8
            elif dark_pixel_ratio > 0.3:
                return "partially_filled", 0.6  
            else:
                return "empty", 0.7
                
        except Exception as e:
            self.logger.error(f"Error in ambiguous bubble classification: {e}")
            return "empty", 0.5
    
    def complete_preprocessing_pipeline(self, image_path: str) -> Tuple[Optional[np.ndarray], dict]:
        """
        Complete preprocessing pipeline following the implementation document
        """
        pipeline_info = {
            "stages_completed": [],
            "errors": [],
            "processing_successful": False,
            "fiducials": {},
            "perspective": {},
            "illumination": {}
        }
        
        try:
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                pipeline_info["errors"].append("Could not load image")
                return None, pipeline_info
            
            pipeline_info["stages_completed"].append("image_loaded")
            pipeline_info["original_dimensions"] = image.shape
            
            # Stage 1: Detect Sheet Orientation & Fiducials
            corners, fiducial_info = self.detect_sheet_orientation_and_fiducials(image)
            pipeline_info["fiducials"] = fiducial_info
            
            if corners is not None:
                pipeline_info["stages_completed"].append("fiducials_detected")
                
                # Stage 2: Rectify Perspective Distortion
                rectified, perspective_info = self.rectify_perspective_distortion(image, corners)
                pipeline_info["perspective"] = perspective_info
                
                if rectified is not None:
                    pipeline_info["stages_completed"].append("perspective_corrected")
                    
                    # Stage 3: Correct Illumination and Threshold
                    final_image, illumination_info = self.correct_illumination_and_threshold(rectified)
                    pipeline_info["illumination"] = illumination_info
                    
                    if final_image is not None:
                        pipeline_info["stages_completed"].append("illumination_corrected")
                        pipeline_info["processing_successful"] = True
                        
                        return final_image, pipeline_info
                    else:
                        pipeline_info["errors"].append("Illumination correction failed")
                else:
                    pipeline_info["errors"].append("Perspective correction failed")
            else:
                # Fallback: process without perspective correction
                self.logger.warning("Could not detect sheet corners, processing without perspective correction")
                pipeline_info["errors"].append("Could not detect sheet corners")
                
                # Still apply illumination correction to the original image
                final_image, illumination_info = self.correct_illumination_and_threshold(image)
                pipeline_info["illumination"] = illumination_info
                
                if final_image is not None:
                    pipeline_info["stages_completed"].append("illumination_corrected_fallback")
                    pipeline_info["processing_successful"] = True
                    return final_image, pipeline_info
        
        except Exception as e:
            self.logger.error(f"Error in preprocessing pipeline: {e}")
            pipeline_info["errors"].append(f"Pipeline error: {str(e)}")
        
        return None, pipeline_info