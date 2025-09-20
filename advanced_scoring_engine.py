import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class ScoringResult:
    """Data class for individual question scoring result"""
    question_number: int
    student_answer: str
    correct_answer: str
    is_correct: bool
    subject: str
    confidence_score: float

class AdvancedScoringEngine:
    """
    Advanced Scoring and Results Logic following implementation document
    Handles answer key matching, comparison logic, and result generation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.subjects = [
            "Data Analytics", 
            "Machine Learning", 
            "Python Programming", 
            "Statistics", 
            "Database Management"
        ]
        self.questions_per_subject = 20
        
    def load_answer_key(self, exam_version: str = "A") -> Dict[int, str]:
        """
        Load answer key for specific exam version
        In production, this would be loaded from database or secure file
        """
        answer_keys_file = f"answer_keys_{exam_version}.json"
        
        try:
            if os.path.exists(answer_keys_file):
                with open(answer_keys_file, 'r') as f:
                    answer_key = json.load(f)
                    # Convert string keys to integers
                    return {int(k): v for k, v in answer_key.items()}
            else:
                # Generate default answer key for demo
                return self.generate_default_answer_key()
                
        except Exception as e:
            self.logger.error(f"Error loading answer key: {e}")
            return self.generate_default_answer_key()
    
    def generate_default_answer_key(self) -> Dict[int, str]:
        """Generate a default answer key for demonstration"""
        answer_key = {}
        options = ['A', 'B', 'C', 'D']
        
        # Generate answers with some pattern for realism
        for i in range(1, 101):
            # Use a pseudo-random but deterministic pattern
            if i % 10 <= 2:
                answer_key[i] = 'A'
            elif i % 10 <= 4:
                answer_key[i] = 'B'
            elif i % 10 <= 7:
                answer_key[i] = 'C'
            else:
                answer_key[i] = 'D'
        
        return answer_key
    
    def identify_exam_version(self, image_metadata: Dict, detected_answers: Dict) -> str:
        """
        Identify exam version from sheet markers or metadata
        In production, this would analyze specific markers on the sheet
        """
        # For demo purposes, default to version A
        # In real implementation, this would:
        # 1. Look for version markers on the sheet
        # 2. Use metadata provided during upload
        # 3. Analyze answer patterns to determine version
        
        return image_metadata.get("exam_version", "A")
    
    def compare_answers(self, student_answers: Dict[int, str], 
                       correct_answers: Dict[int, str],
                       confidence_scores: Dict[int, float]) -> List[ScoringResult]:
        """
        Compare student answers with correct answers question by question
        """
        scoring_results = []
        
        for question_num in range(1, 101):  # Questions 1-100
            # Determine subject for this question
            subject_index = (question_num - 1) // self.questions_per_subject
            subject_name = self.subjects[subject_index] if subject_index < len(self.subjects) else "Unknown"
            
            # Get answers
            student_answer = student_answers.get(question_num, "BLANK")
            correct_answer = correct_answers.get(question_num, "")
            confidence = confidence_scores.get(question_num, 0.0)
            
            # Handle special cases
            if student_answer.startswith("MULTIPLE_"):
                # Multiple bubbles filled - extract the chosen answer
                actual_answer = student_answer.split("_")[1]
                is_correct = actual_answer == correct_answer
            elif student_answer == "BLANK":
                # No answer given
                is_correct = False
                actual_answer = "BLANK"
            else:
                # Normal case
                actual_answer = student_answer
                is_correct = actual_answer == correct_answer
            
            scoring_result = ScoringResult(
                question_number=question_num,
                student_answer=actual_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                subject=subject_name,
                confidence_score=confidence
            )
            
            scoring_results.append(scoring_result)
        
        return scoring_results
    
    def compute_subject_scores(self, scoring_results: List[ScoringResult]) -> Dict[str, Dict]:
        """
        Compute subject-wise and total scores
        """
        subject_scores = {}
        
        # Initialize subject scores
        for subject in self.subjects:
            subject_scores[subject] = {
                "correct": 0,
                "wrong": 0,
                "blank": 0,
                "multiple_marks": 0,
                "total_questions": self.questions_per_subject,
                "score_percentage": 0.0,
                "confidence_avg": 0.0
            }
        
        # Process each scoring result
        for result in scoring_results:
            if result.subject in subject_scores:
                subject_data = subject_scores[result.subject]
                
                if result.student_answer == "BLANK":
                    subject_data["blank"] += 1
                elif result.student_answer.startswith("MULTIPLE"):
                    subject_data["multiple_marks"] += 1
                    if result.is_correct:
                        subject_data["correct"] += 1
                    else:
                        subject_data["wrong"] += 1
                else:
                    if result.is_correct:
                        subject_data["correct"] += 1
                    else:
                        subject_data["wrong"] += 1
        
        # Calculate percentages and averages
        for subject, data in subject_scores.items():
            if data["total_questions"] > 0:
                data["score_percentage"] = (data["correct"] / data["total_questions"]) * 100
            
            # Calculate average confidence for answered questions
            subject_results = [r for r in scoring_results if r.subject == subject and r.student_answer != "BLANK"]
            if subject_results:
                data["confidence_avg"] = sum(r.confidence_score for r in subject_results) / len(subject_results)
        
        return subject_scores
    
    def calculate_total_score(self, subject_scores: Dict[str, Dict]) -> Dict[str, any]:
        """
        Calculate total score across all subjects
        """
        total_correct = sum(scores["correct"] for scores in subject_scores.values())
        total_wrong = sum(scores["wrong"] for scores in subject_scores.values())
        total_blank = sum(scores["blank"] for scores in subject_scores.values())
        total_multiple = sum(scores["multiple_marks"] for scores in subject_scores.values())
        total_questions = sum(scores["total_questions"] for scores in subject_scores.values())
        
        total_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "total_correct": total_correct,
            "total_wrong": total_wrong,
            "total_blank": total_blank,
            "total_multiple_marks": total_multiple,
            "total_questions": total_questions,
            "total_percentage": round(total_percentage, 2),
            "attempted_questions": total_correct + total_wrong + total_multiple
        }
    
    def generate_structured_output(self, student_id: str, exam_version: str,
                                  subject_scores: Dict[str, Dict], total_scores: Dict,
                                  scoring_results: List[ScoringResult], 
                                  processing_metadata: Dict) -> Dict[str, any]:
        """
        Generate structured JSON output as specified in implementation document
        """
        # Create detailed answer breakdown
        answer_breakdown = {}
        for result in scoring_results:
            answer_breakdown[result.question_number] = {
                "student_answer": result.student_answer,
                "correct_answer": result.correct_answer,
                "is_correct": result.is_correct,
                "subject": result.subject,
                "confidence": round(result.confidence_score, 3)
            }
        
        # Generate quality metrics
        quality_metrics = {
            "average_confidence": round(sum(r.confidence_score for r in scoring_results) / len(scoring_results), 3),
            "low_confidence_questions": len([r for r in scoring_results if r.confidence_score < 0.7]),
            "ambiguous_answers": processing_metadata.get("ambiguous_questions", []),
            "multiple_marks_detected": processing_metadata.get("multiple_marks", []),
            "processing_time_seconds": processing_metadata.get("total_processing_time", 0)
        }
        
        # Create the final structured output
        structured_output = {
            "student_information": {
                "student_id": student_id,
                "exam_version": exam_version,
                "processing_timestamp": datetime.now().isoformat(),
                "image_filename": processing_metadata.get("image_filename", "unknown")
            },
            "score_summary": {
                "total_scores": total_scores,
                "subject_scores": subject_scores,
                "quality_metrics": quality_metrics
            },
            "detailed_results": {
                "answer_breakdown": answer_breakdown,
                "flagged_questions": {
                    "multiple_marks": processing_metadata.get("multiple_marks", []),
                    "low_confidence": [r.question_number for r in scoring_results if r.confidence_score < 0.5],
                    "ambiguous": processing_metadata.get("ambiguous_questions", [])
                }
            },
            "processing_information": {
                "preprocessing_successful": processing_metadata.get("preprocessing_successful", False),
                "detection_successful": processing_metadata.get("detection_successful", False),
                "total_processing_time": processing_metadata.get("total_processing_time", 0),
                "grid_identification": processing_metadata.get("grid_identified", False),
                "overlay_generated": processing_metadata.get("overlay_generated", False)
            }
        }
        
        return structured_output
    
    def save_results_to_file(self, structured_output: Dict, output_directory: str = "exports") -> str:
        """
        Save structured results to JSON file
        """
        try:
            os.makedirs(output_directory, exist_ok=True)
            
            student_id = structured_output["student_information"]["student_id"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_id}_results_{timestamp}.json"
            filepath = os.path.join(output_directory, filename)
            
            with open(filepath, 'w') as f:
                json.dump(structured_output, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving results to file: {e}")
            return ""
    
    def complete_scoring_process(self, student_id: str, detected_answers: Dict[int, str],
                                confidence_scores: Dict[int, float], 
                                processing_metadata: Dict) -> Dict[str, any]:
        """
        Complete scoring process following implementation document specifications
        """
        scoring_process_result = {
            "scoring_completed": False,
            "structured_output": {},
            "results_file_path": "",
            "error": None
        }
        
        try:
            # Step 1: Identify exam version
            exam_version = self.identify_exam_version(processing_metadata, detected_answers)
            
            # Step 2: Load appropriate answer key
            correct_answers = self.load_answer_key(exam_version)
            
            # Step 3: Compare answers question by question
            scoring_results = self.compare_answers(detected_answers, correct_answers, confidence_scores)
            
            # Step 4: Compute subject-wise scores
            subject_scores = self.compute_subject_scores(scoring_results)
            
            # Step 5: Calculate total scores
            total_scores = self.calculate_total_score(subject_scores)
            
            # Step 6: Generate structured output
            structured_output = self.generate_structured_output(
                student_id, exam_version, subject_scores, total_scores,
                scoring_results, processing_metadata
            )
            
            # Step 7: Save results to file
            results_file_path = self.save_results_to_file(structured_output)
            
            scoring_process_result.update({
                "scoring_completed": True,
                "structured_output": structured_output,
                "results_file_path": results_file_path,
                "exam_version_used": exam_version,
                "total_questions_scored": len(scoring_results)
            })
            
            return scoring_process_result
            
        except Exception as e:
            self.logger.error(f"Error in complete scoring process: {e}")
            scoring_process_result["error"] = str(e)
            return scoring_process_result