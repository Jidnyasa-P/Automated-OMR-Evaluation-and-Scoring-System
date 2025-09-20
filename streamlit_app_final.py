import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json
import plotly.express as px
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="OMR Evaluation System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("🎯 Automated OMR Evaluation System")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Upload & Process", "Camera Capture", "View Results", "Dashboard", "About"]
    )
    
    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "Camera Capture":
        camera_capture_page()
    elif page == "View Results":
        view_results_page()
    elif page == "Dashboard":
        dashboard_page()
    elif page == "About":
        about_page()

def upload_and_process_page():
    st.header("📤 Upload & Process OMR Sheet")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload OMR Sheet")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose an OMR sheet image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of the OMR sheet"
        )
        
        # Answer key set selection
        set_choice = st.selectbox(
            "Select Answer Key Set",
            ["A", "B"],
            help="Choose Set A or Set B"
        )
        
        # Student details
        col_a, col_b = st.columns(2)
        with col_a:
            student_id = st.text_input("Student ID", value="STU001")
        with col_b:
            exam_id = st.number_input("Exam ID", min_value=1, value=1)
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded OMR Sheet", use_container_width=True)
            
            # Process button
            if st.button("🚀 Process OMR Sheet", type="primary"):
                process_omr_sheet(uploaded_file, set_choice, student_id, exam_id)
    
    with col2:
        st.subheader("Instructions")
        st.info("""
        **How to use:**
        1. Upload a clear image of the OMR sheet
        2. Select the answer key set (A or B)
        3. Enter student ID and exam ID
        4. Click 'Process OMR Sheet'
        5. Wait for processing to complete
        6. View results in the 'View Results' tab
        
        **Image Requirements:**
        - Clear, well-lit image
        - OMR sheet should be flat
        - All bubbles should be visible
        - Supported formats: PNG, JPG, JPEG
        """)

def camera_capture_page():
    st.header("📷 Camera Capture")
    
    st.info("📸 Take a clear photo of your OMR sheet. Ensure good lighting and the sheet is flat.")
    
    # Camera input
    camera_photo = st.camera_input("Take a picture of your OMR sheet")
    
    if camera_photo is not None:
        # Display captured image
        st.image(camera_photo, caption="Captured OMR Sheet", use_column_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Answer key set selection
            set_choice = st.selectbox(
                "Select Answer Key Set",
                ["A", "B"],
                help="Choose Set A or Set B",
                key="camera_set_choice"
            )
        
        with col2:
            student_id = st.text_input("Student ID", value="CAM001", key="camera_student_id")
        
        if st.button("🚀 Process Captured Image", type="primary"):
            # Process camera photo directly
            process_camera_photo(camera_photo, set_choice, student_id, 1)

def process_camera_photo(camera_photo, set_choice, student_id, exam_id):
    """Process the camera captured photo"""
    try:
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Prepare file for upload
        status_text.text("Preparing image...")
        progress_bar.progress(10)
        
        # Reset file pointer to beginning
        camera_photo.seek(0)
        
        # Prepare the files dict for requests
        files = {"file": ("camera_capture.jpg", camera_photo, "image/jpeg")}
        data = {
            "exam_version": set_choice,
            "student_id": student_id,
            "exam_id": exam_id
        }
        
        # Step 2: Upload file
        status_text.text("Uploading file...")
        progress_bar.progress(30)
        
        upload_response = requests.post(
            f"{API_BASE_URL}/upload-sheet/",
            files=files,
            data=data,
            timeout=30
        )
        
        if upload_response.status_code != 200:
            st.error(f"Upload failed: {upload_response.text}")
            return
        
        upload_result = upload_response.json()
        sheet_id = upload_result["sheet_id"]
        
        # Step 3: Process sheet
        status_text.text("Processing OMR sheet...")
        progress_bar.progress(60)
        
        process_response = requests.post(
            f"{API_BASE_URL}/process-sheet/{sheet_id}",
            params={"exam_version": set_choice},
            timeout=30
        )
        
        if process_response.status_code != 200:
            st.error(f"Processing failed: {process_response.text}")
            return
        
        progress_bar.progress(100)
        status_text.text("Processing completed!")
        
        process_result = process_response.json()
        display_results(process_result, sheet_id)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
    except Exception as e:
        st.error(f"Error processing camera image: {str(e)}")

def process_omr_sheet(uploaded_file, set_choice, student_id, exam_id):
    """Process the uploaded OMR sheet"""
    try:
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Prepare file for upload
        status_text.text("Preparing file...")
        progress_bar.progress(10)
        
        # Get file details
        file_details = {
            "filename": uploaded_file.name,
            "content_type": uploaded_file.type
        }
        
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Prepare the files dict for requests
        files = {"file": (file_details["filename"], uploaded_file, file_details["content_type"])}
        data = {
            "exam_version": set_choice,
            "student_id": student_id,
            "exam_id": exam_id
        }
        
        # Step 2: Upload file
        status_text.text("Uploading file...")
        progress_bar.progress(30)
        
        upload_response = requests.post(
            f"{API_BASE_URL}/upload-sheet/",
            files=files,
            data=data,
            timeout=30
        )
        
        if upload_response.status_code != 200:
            st.error(f"Upload failed: {upload_response.text}")
            progress_bar.empty()
            status_text.empty()
            return
        
        upload_result = upload_response.json()
        sheet_id = upload_result["sheet_id"]
        
        # Step 3: Process sheet
        status_text.text("Processing OMR sheet...")
        progress_bar.progress(60)
        
        process_response = requests.post(
            f"{API_BASE_URL}/process-sheet/{sheet_id}",
            params={"exam_version": set_choice},
            timeout=30
        )
        
        if process_response.status_code != 200:
            st.error(f"Processing failed: {process_response.text}")
            progress_bar.empty()
            status_text.empty()
            return
        
        progress_bar.progress(100)
        status_text.text("Processing completed!")
        
        process_result = process_response.json()
        display_results(process_result, sheet_id)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
    except Exception as e:
        st.error(f"Error processing OMR sheet: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")

def display_results(process_result, sheet_id):
    """Display the processing results"""
    # Display results
    st.success("✅ OMR Sheet processed successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Score", f"{process_result['total_score']}/{process_result['total_questions']}")
    with col2:
        st.metric("Percentage", f"{process_result['percentage']:.1f}%")
    with col3:
        st.metric("Processing Time", f"{process_result['processing_time']:.2f}s")
    
    # Subject-wise results
    st.subheader("📊 Subject-wise Results")
    
    subject_data = []
    for subject, scores in process_result['subject_scores'].items():
        subject_data.append({
            "Subject": subject,
            "Correct": scores["correct"],
            "Wrong": scores["wrong"],
            "Blank": scores.get("blank", 0),
            "Score %": scores["score_percentage"]
        })
    
    df = pd.DataFrame(subject_data)
    st.dataframe(df, use_container_width=True)
    
    # Visualization
    fig = px.bar(
        df, 
        x="Subject", 
        y="Score %",
        title="Subject-wise Performance",
        color="Score %",
        color_continuous_scale="RdYlGn"
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Store sheet ID in session state for results viewing
    st.session_state['last_processed_sheet'] = sheet_id

def view_results_page():
    st.header("📊 View Results")
    
    try:
        # Get list of all sheets
        response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
        if response.status_code == 200:
            sheets_data = response.json()
            sheets = sheets_data["sheets"]
            
            if sheets:
                # Create a selectbox for sheet selection
                sheet_options = [f"Sheet {sheet['id']} - {sheet['student_id']} ({sheet['status']})" for sheet in sheets]
                selected_option = st.selectbox("Select a sheet to view results:", sheet_options)
                
                if selected_option:
                    # Extract sheet ID from selection
                    sheet_id = int(selected_option.split(" ")[1])
                    display_sheet_results(sheet_id)
            else:
                st.info("No sheets processed yet. Upload and process a sheet first.")
        else:
            st.error(f"Failed to fetch sheets list: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
        st.info("Make sure the backend server is running (start_backend.bat)")
    except Exception as e:
        st.error(f"Error fetching results: {str(e)}")

def display_sheet_results(sheet_id):
    """Display detailed results for a specific sheet"""
    try:
        response = requests.get(f"{API_BASE_URL}/sheet/{sheet_id}/results", timeout=10)
        if response.status_code == 200:
            results = response.json()
            
            # Header info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sheet ID", results["sheet_id"])
            with col2:
                st.metric("Student ID", results["student_id"])
            with col3:
                st.metric("Status", results["status"])
            with col4:
                st.metric("Total Score", results["total_score"] if results["total_score"] is not None else "N/A")
            
            if results["status"] == "completed" and results["subject_results"]:
                # Subject results table
                st.subheader("Subject-wise Performance")
                
                subject_df = pd.DataFrame([
                    {
                        "Subject": subject,
                        "Correct": data["correct"],
                        "Wrong": data["wrong"],
                        "Percentage": data["percentage"]
                    }
                    for subject, data in results["subject_results"].items()
                ])
                
                st.dataframe(subject_df, use_container_width=True)
                
                # Performance chart
                fig = px.bar(
                    subject_df,
                    x="Subject",
                    y="Percentage",
                    title="Subject-wise Performance",
                    color="Percentage",
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Sheet status: {results['status']}. Results may not be available yet.")
                
        else:
            st.error(f"Failed to fetch results for sheet {sheet_id}: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def dashboard_page():
    st.header("📈 Dashboard")
    
    try:
        # Get all sheets
        response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
        if response.status_code == 200:
            sheets_data = response.json()
            sheets = sheets_data["sheets"]
            
            if sheets:
                # Overview metrics
                completed_sheets = [s for s in sheets if s["status"] == "completed"]
                total_sheets = len(sheets)
                completed_count = len(completed_sheets)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Sheets", total_sheets)
                with col2:
                    st.metric("Completed", completed_count)
                with col3:
                    processing_rate = (completed_count/total_sheets*100) if total_sheets > 0 else 0
                    st.metric("Success Rate", f"{processing_rate:.1f}%")
                with col4:
                    valid_scores = [s["total_score"] for s in completed_sheets if s["total_score"] is not None]
                    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                    st.metric("Avg Score", f"{avg_score:.1f}")
                
                # Status distribution
                status_counts = {}
                for sheet in sheets:
                    status = sheet["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_status = px.pie(
                        values=list(status_counts.values()),
                        names=list(status_counts.keys()),
                        title="Processing Status Distribution"
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                
                with col2:
                    if valid_scores:
                        fig_scores = px.histogram(
                            x=valid_scores,
                            nbins=10,
                            title="Score Distribution"
                        )
                        st.plotly_chart(fig_scores, use_container_width=True)
                
                # Recent activity
                st.subheader("Recent Activity")
                recent_sheets = sorted(sheets, key=lambda x: x["upload_time"] if x["upload_time"] else "", reverse=True)[:10]
                
                recent_df = pd.DataFrame([
                    {
                        "Sheet ID": sheet["id"],
                        "Student ID": sheet["student_id"],
                        "Status": sheet["status"],
                        "Score": sheet["total_score"] if sheet["total_score"] is not None else "N/A",
                        "Upload Time": sheet["upload_time"][:19] if sheet["upload_time"] else "N/A"
                    }
                    for sheet in recent_sheets
                ])
                
                st.dataframe(recent_df, use_container_width=True)
                
            else:
                st.info("No data available yet. Process some OMR sheets to see dashboard statistics.")
        else:
            st.error(f"Failed to fetch dashboard data: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
        st.info("Make sure the backend server is running (start_backend.bat)")
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def about_page():
    st.header("ℹ️ About OMR Evaluation System")
    
    st.markdown("""
    ## 🎯 Overview
    
    The **Automated OMR Evaluation System** is designed to streamline the process of evaluating 
    Optical Mark Recognition (OMR) sheets for educational assessments.
    
    ## 🚀 Key Features
    
    - **File Upload**: Upload OMR sheet images directly
    - **Camera Capture**: Take photos directly through your camera
    - **Automated Processing**: Eliminate manual evaluation errors
    - **Real-time Results**: Instant processing and scoring
    - **Subject-wise Analysis**: Detailed breakdown by subject areas
    - **Dashboard Analytics**: Comprehensive statistics and insights
    
    ## 📊 Supported Exam Format
    
    - **Total Questions**: 100 questions
    - **Subjects**: 5 subjects (20 questions each)
    - **Options**: A, B, C, D (4 options per question)
    - **Answer Key Sets**: Set A and Set B support
    
    ## 🎪 Demo Configuration
    
    This system is configured for:
    - Data Analytics (Questions 1-20)
    - Machine Learning (Questions 21-40)
    - Python Programming (Questions 41-60)
    - Statistics (Questions 61-80)
    - Database Management (Questions 81-100)
    
    ## 🔧 System Status
    
    - **Backend Status**: """ + get_backend_status() + """
    - **Version**: 1.0.0  
    - **Last Updated**: September 2025
    """)

def get_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            return "🟢 Online"
        else:
            return "🟡 Issues detected"
    except:
        return "🔴 Offline (Run start_backend.bat)"

if __name__ == "__main__":
    main()