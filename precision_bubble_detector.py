import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import json
import os
from enhanced_preprocessor import EnhancedOMRPreprocessor

class PrecisionBubbleDetector:
    """
    Enhanced Bubble Detection and Answer Extraction following implementation document
    Implements precise ROI-based bubble grid detection and ML-assisted classification
    """
    
    def __init__(self, questions_per_subject: int = 20, subjects_count: int = 5):
        self.questions_per_subject = questions_per_subject
        self.subjects_count = subjects_count
        self.total_questions = questions_per_subject * subjects_count
        self.logger = logging.getLogger(__name__)
        
        # Initialize the enhanced preprocessor for ML classification
        self.preprocessor = EnhancedOMRPreprocessor()
        
        # Standard OMR sheet template dimensions (adjust based on your actual sheet)
        self.template_config = {
            "sheet_width": 800,
            "sheet_height": 1200,
            "bubble_radius": 8,
            "questions_per_row": 1,
            "options_per_question": 4,
            "question_spacing_y": 24,
            "option_spacing_x": 30,
            "start_offset_x": 100,
            "start_offset_y": 200,
            "subject_spacing": 200
        }
    
    def identify_bubble_grid(self, processed_image: np.ndarray) -> Dict[str, any]:
        """
        Step 1: Identify the Bubble Grid
        Since the sheet is now a perfect rectangle, define exact coordinates of every bubble
        """
        grid_info = {
            "grid_identified": False,
            "total_rois": 0,
            "rois_by_question": {},
            "template_used": self.template_config.copy()
        }
        
        try:
            height, width = processed_image.shape[:2]
            
            # Scale template to actual image size if needed
            scale_x = width / self.template_config["sheet_width"]
            scale_y = height / self.template_config["sheet_height"]
            
            # Apply scaling to template dimensions
            scaled_config = {}
            for key, value in self.template_config.items():
                if key in ["sheet_width", "sheet_height"]:
                    scaled_config[key] = value  # Keep original for reference
                elif "x" in key:
                    scaled_config[key] = int(value * scale_x)
                elif "y" in key:
                    scaled_config[key] = int(value * scale_y)
                else:
                    scaled_config[key] = value
            
            # Generate ROI coordinates for all 100 questions
            question_number = 1
            
            for subject_idx in range(self.subjects_count):
                # Calculate starting position for this subject
                subject_start_y = (scaled_config["start_offset_y"] + 
                                 subject_idx * scaled_config["subject_spacing"])
                
                for q_in_subject in range(self.questions_per_subject):
                    # Calculate question position
                    question_y = (subject_start_y + 
                                q_in_subject * scaled_config["question_spacing_y"])
                    
                    # Generate ROIs for each option (A, B, C, D)
                    question_rois = {}
                    
                    for option_idx in range(scaled_config["options_per_question"]):
                        option_letter = chr(ord('A') + option_idx)
                        
                        # Calculate bubble center
                        bubble_x = (scaled_config["start_offset_x"] + 
                                  option_idx * scaled_config["option_spacing_x"])
                        bubble_y = question_y
                        
                        # Define ROI rectangle around bubble
                        roi_size = scaled_config["bubble_radius"] * 2
                        roi_x1 = max(0, bubble_x - roi_size)
                        roi_y1 = max(0, bubble_y - roi_size)
                        roi_x2 = min(width, bubble_x + roi_size)
                        roi_y2 = min(height, bubble_y + roi_size)
                        
                        question_rois[option_letter] = {
                            "center": (bubble_x, bubble_y),
                            "roi_bounds": (roi_x1, roi_y1, roi_x2, roi_y2),
                            "roi_size": roi_size
                        }
                    
                    grid_info["rois_by_question"][question_number] = question_rois
                    question_number += 1
            
            grid_info["grid_identified"] = True
            grid_info["total_rois"] = len(grid_info["rois_by_question"]) * 4
            grid_info["scaling_applied"] = {"scale_x": scale_x, "scale_y": scale_y}
            
            return grid_info
            
        except Exception as e:
            self.logger.error(f"Error identifying bubble grid: {e}")
            grid_info["error"] = str(e)
            return grid_info
    
    def classify_bubble_advanced(self, bubble_roi: np.ndarray, roi_info: dict) -> Tuple[str, float, dict]:
        """
        Step 2: Advanced Bubble Classification
        Uses pixel counting + ML for ambiguous cases
        """
        classification_info = {
            "method_used": "pixel_counting",
            "pixel_stats": {},
            "ml_used": False
        }
        
        try:
            # Extract the bubble region
            roi_x1, roi_y1, roi_x2, roi_y2 = roi_info["roi_bounds"]
            bubble_region = bubble_roi[roi_y1:roi_y2, roi_x1:roi_x2]
            
            if bubble_region.size == 0:
                return "empty", 0.0, classification_info
            
            # Step 2a: Count non-white pixels (basic method)
            if len(np.unique(bubble_region)) <= 2:  # Binary image
                dark_pixels = np.sum(bubble_region == 0)
                total_pixels = bubble_region.size
            else:  # Grayscale image
                # Use adaptive threshold for counting
                threshold = np.mean(bubble_region) - 0.5 * np.std(bubble_region)
                dark_pixels = np.sum(bubble_region < threshold)
                total_pixels = bubble_region.size
            
            dark_pixel_ratio = dark_pixels / total_pixels if total_pixels > 0 else 0
            
            classification_info["pixel_stats"] = {
                "dark_pixels": int(dark_pixels),
                "total_pixels": int(total_pixels),
                "dark_ratio": float(dark_pixel_ratio),
                "mean_intensity": float(np.mean(bubble_region)),
                "std_intensity": float(np.std(bubble_region))
            }
            
            # Step 2b: Primary classification based on pixel count
            if dark_pixel_ratio > 0.7:
                return "filled", 0.9, classification_info
            elif dark_pixel_ratio < 0.2:
                return "empty", 0.9, classification_info
            else:
                # Step 2c: Ambiguous case - use ML classifier
                classification_info["method_used"] = "ml_classification"
                classification_info["ml_used"] = True
                
                ml_result, ml_confidence = self.preprocessor.classify_ambiguous_bubble(bubble_region)
                
                classification_info["ml_result"] = {
                    "classification": ml_result,
                    "confidence": ml_confidence
                }
                
                # Convert ML result to our standard format
                if ml_result == "filled" or ml_result == "partially_filled":
                    return "filled", ml_confidence, classification_info
                else:
                    return "empty", ml_confidence, classification_info
                    
        except Exception as e:
            self.logger.error(f"Error in bubble classification: {e}")
            classification_info["error"] = str(e)
            return "empty", 0.0, classification_info
    
    def extract_student_answers(self, processed_image: np.ndarray, grid_info: Dict) -> Dict[str, any]:
        """
        Complete answer extraction process for all 100 questions
        """
        extraction_results = {
            "answers": {},
            "confidence_scores": {},
            "ambiguous_questions": [],
            "multiple_marks": [],
            "processing_details": {},
            "extraction_successful": False
        }
        
        try:
            if not grid_info["grid_identified"]:
                extraction_results["error"] = "Grid not properly identified"
                return extraction_results
            
            # Process each question
            for question_num, question_rois in grid_info["rois_by_question"].items():
                question_results = {}
                option_confidences = {}
                
                # Check each option (A, B, C, D) for this question
                for option_letter, roi_info in question_rois.items():
                    classification, confidence, details = self.classify_bubble_advanced(
                        processed_image, roi_info
                    )
                    
                    question_results[option_letter] = {
                        "classification": classification,
                        "confidence": confidence,
                        "details": details
                    }
                    
                    if classification == "filled":
                        option_confidences[option_letter] = confidence
                
                # Determine final answer for this question
                filled_options = list(option_confidences.keys())
                
                if len(filled_options) == 0:
                    # No bubbles filled
                    extraction_results["answers"][question_num] = "BLANK"
                    extraction_results["confidence_scores"][question_num] = 0.0
                    
                elif len(filled_options) == 1:
                    # Single bubble filled (normal case)
                    answer = filled_options[0]
                    extraction_results["answers"][question_num] = answer
                    extraction_results["confidence_scores"][question_num] = option_confidences[answer]
                    
                else:
                    # Multiple bubbles filled
                    extraction_results["multiple_marks"].append(question_num)
                    # Choose the one with highest confidence
                    best_option = max(option_confidences, key=option_confidences.get)
                    extraction_results["answers"][question_num] = f"MULTIPLE_{best_option}"
                    extraction_results["confidence_scores"][question_num] = option_confidences[best_option]
                
                # Store detailed processing info
                extraction_results["processing_details"][question_num] = question_results
                
                # Check for ambiguous cases (low confidence)
                avg_confidence = np.mean(list(option_confidences.values())) if option_confidences else 0
                if avg_confidence < 0.7 and filled_options:
                    extraction_results["ambiguous_questions"].append(question_num)
            
            extraction_results["extraction_successful"] = True
            extraction_results["total_questions_processed"] = len(grid_info["rois_by_question"])
            
            return extraction_results
            
        except Exception as e:
            self.logger.error(f"Error in answer extraction: {e}")
            extraction_results["error"] = str(e)
            return extraction_results
    
    def generate_overlay_image(self, original_image: np.ndarray, grid_info: Dict, 
                              extraction_results: Dict) -> Optional[np.ndarray]:
        """
        Generate overlay image showing which bubbles were detected as marked
        This is required for audit trail as per implementation document
        """
        try:
            # Create a copy of the original image for overlay
            overlay = original_image.copy()
            if len(overlay.shape) == 2:  # Convert grayscale to color for overlay
                overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
            
            # Define colors for different states
            colors = {
                "filled": (0, 255, 0),      # Green for filled bubbles
                "empty": (128, 128, 128),   # Gray for empty bubbles  
                "multiple": (0, 0, 255),    # Red for multiple marks
                "ambiguous": (0, 255, 255)  # Yellow for ambiguous cases
            }
            
            # Draw overlays for each question
            for question_num, question_rois in grid_info["rois_by_question"].items():
                detected_answer = extraction_results["answers"].get(question_num, "BLANK")
                
                for option_letter, roi_info in question_rois.items():
                    center = roi_info["center"]
                    radius = roi_info["roi_size"] // 2
                    
                    # Determine color based on detection result
                    if detected_answer.startswith("MULTIPLE"):
                        color = colors["multiple"]
                    elif detected_answer == option_letter:
                        color = colors["filled"]
                    elif question_num in extraction_results["ambiguous_questions"]:
                        color = colors["ambiguous"]
                    else:
                        color = colors["empty"]
                    
                    # Draw circle overlay
                    cv2.circle(overlay, center, radius, color, 2)
                    
                    # Add question number label for first option
                    if option_letter == 'A':
                        cv2.putText(overlay, str(question_num), 
                                  (center[0] - 30, center[1]), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            return overlay
            
        except Exception as e:
            self.logger.error(f"Error generating overlay image: {e}")
            return None
    
    def complete_detection_process(self, processed_image: np.ndarray) -> Dict[str, any]:
        """
        Complete bubble detection process following implementation document specifications
        """
        detection_results = {
            "process_completed": False,
            "grid_info": {},
            "extraction_results": {},
            "overlay_generated": False,
            "total_processing_time": 0
        }
        
        import time
        start_time = time.time()
        
        try:
            # Step 1: Identify the bubble grid
            grid_info = self.identify_bubble_grid(processed_image)
            detection_results["grid_info"] = grid_info
            
            if not grid_info["grid_identified"]:
                detection_results["error"] = "Failed to identify bubble grid"
                return detection_results
            
            # Step 2: Extract student answers
            extraction_results = self.extract_student_answers(processed_image, grid_info)
            detection_results["extraction_results"] = extraction_results
            
            if not extraction_results["extraction_successful"]:
                detection_results["error"] = "Failed to extract answers"
                return detection_results
            
            # Step 3: Generate overlay image for audit trail
            overlay_image = self.generate_overlay_image(processed_image, grid_info, extraction_results)
            if overlay_image is not None:
                detection_results["overlay_generated"] = True
                detection_results["overlay_image"] = overlay_image
            
            detection_results["process_completed"] = True
            detection_results["total_processing_time"] = time.time() - start_time
            
            # Generate summary statistics
            detection_results["summary"] = {
                "total_questions": len(extraction_results["answers"]),
                "answered_questions": len([a for a in extraction_results["answers"].values() if a != "BLANK"]),
                "blank_questions": len([a for a in extraction_results["answers"].values() if a == "BLANK"]),
                "multiple_marks": len(extraction_results["multiple_marks"]),
                "ambiguous_cases": len(extraction_results["ambiguous_questions"]),
                "average_confidence": np.mean(list(extraction_results["confidence_scores"].values())) if extraction_results["confidence_scores"] else 0
            }
            
            return detection_results
            
        except Exception as e:
            self.logger.error(f"Error in complete detection process: {e}")
            detection_results["error"] = str(e)
            detection_results["total_processing_time"] = time.time() - start_time
            return detection_results