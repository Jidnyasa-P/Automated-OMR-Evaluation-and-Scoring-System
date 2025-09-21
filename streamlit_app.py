import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json
import plotly.express as px
from datetime import datetime
import time
import os
os.system("pip install streamlit-back-camera-input")    # Avoid in production

# Try to import the back camera input - install with: pip install streamlit-back-camera-input
try:
    from streamlit_back_camera_input import back_camera_input
    BACK_CAMERA_AVAILABLE = True
except ImportError:
    BACK_CAMERA_AVAILABLE = False
    st.warning("📱 For mobile back camera support, install: pip install streamlit-back-camera-input")

# Configure Streamlit page
st.set_page_config(
    page_title="OMR Evaluation System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

def main():
    st.title("🎯 Automated OMR Evaluation System")
    st.markdown("---")

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
    st.header("📤 Upload & Process OMR Sheets")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload OMR Sheets")
        uploaded_files = st.file_uploader(
            "Choose one or more OMR sheet images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload clear images of OMR sheets"
        )
        
        set_choice = st.selectbox(
            "Select Answer Key Set", 
            ["A", "B"], 
            help="Choose Set A or Set B"
        )

        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) selected for processing")
            
            # Show preview of uploaded files
            if len(uploaded_files) <= 3:
                cols = st.columns(len(uploaded_files))
                for i, file in enumerate(uploaded_files):
                    with cols[i]:
                        image = Image.open(file)
                        st.image(image, caption=file.name, use_column_width=True)
            else:
                st.write("📋 Selected files:")
                for file in uploaded_files:
                    st.write(f"• {file.name}")

            if st.button("🚀 Process All Uploaded Sheets", type="primary"):
                if not uploaded_files:
                    st.error("Please upload at least one image.")
                    return
                
                process_bulk_sheets(uploaded_files, set_choice)
    
    with col2:
        st.subheader("Instructions")
        st.info("""
        **How to use:**
        1. Upload one or more clear images of OMR sheets
        2. Select the answer key set (A or B)
        3. Click 'Process All Uploaded Sheets'
        4. View results and download CSV exports
        5. Check 'View Results' and 'Dashboard' for details
        
        **Features:**
        - ✅ Bulk upload and processing
        - ✅ Auto-generated student IDs
        - ✅ Instant results with charts
        - ✅ CSV export functionality
        - ✅ Comprehensive analytics
        """)

def camera_capture_page():
    st.header("📷 Camera Capture (Back Camera Only)")

    if not BACK_CAMERA_AVAILABLE:
        st.error("Back camera feature not available. Please install 'streamlit-back-camera-input'.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📱 Mobile Back Camera (Recommended)")
        st.info("This feature uses your mobile device's back camera for better OMR sheet capture.")
        
        # Back camera input
        back_camera_image = back_camera_input(key="back_camera")

        if back_camera_image is not None:
            st.image(back_camera_image, caption="📱 Captured with Back Camera", use_column_width=True)
            
            set_choice_back = st.selectbox(
                "Select Answer Key Set",
                ["A", "B"],
                help="Choose Set A or Set B",
                key="back_camera_set_choice"
            )
            
            if st.button("🚀 Process Captured Image", type="primary", key="process_back_camera"):
                process_captured_image(back_camera_image, set_choice_back, "back_camera_capture.jpg")
        
        st.markdown("---")

    with col2:
        st.subheader("📱 Instructions")
        st.info("""
        **How to Use:**
        1. Tap the 'Choose file' or 'Take Photo' button below.
        2. Your device will open the back camera with a shutter/capture option.
        3. Take a clear photo of the OMR sheet.
        4. Photo will appear here after you confirm.
        5. Select answer key set.
        6. Tap 'Process Captured Image'.

        **Tips for best results:**
        - Ensure good lighting
        - Keep OMR sheet flat
        - Fill the entire frame
        - Avoid shadows
        """)


def process_captured_image(image_data, set_choice, filename):
    """Process an image captured from camera (back camera or regular camera)"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Preparing image...")
        progress_bar.progress(10)
        
        # Convert image to file-like object
        if hasattr(image_data, 'read'):
            # It's already a file-like object
            image_data.seek(0)
            files = {"file": (filename, image_data, "image/jpeg")}
        else:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            if isinstance(image_data, Image.Image):
                image_data.save(img_byte_arr, format='JPEG')
            else:
                # Assume it's already bytes
                img_byte_arr.write(image_data)
            img_byte_arr.seek(0)
            files = {"file": (filename, img_byte_arr, "image/jpeg")}
        
        data = {"exam_version": set_choice}
        
        status_text.text("Uploading...")
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

        sheet_id = upload_response.json()["sheet_id"]
        
        status_text.text("Processing...")
        progress_bar.progress(70)
        
        process_response = requests.post(
            f"{API_BASE_URL}/process-sheet/{sheet_id}",
            params={"exam_version": set_choice},
            timeout=30
        )
        
        if process_response.status_code != 200:
            st.error(f"Processing failed: {process_response.text}")
            return
        
        progress_bar.progress(100)
        status_text.text("Completed!")
        
        result = process_response.json()
        display_single_result(result, sheet_id)
        
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"Error processing camera image: {str(e)}")

def process_bulk_sheets(uploaded_files, set_choice):
    """Process multiple OMR sheets and show summary"""
    summary_data = []
    total_files = len(uploaded_files)
    
    # Create progress tracking
    overall_progress = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # Update overall progress
            progress_percent = (i / total_files)
            overall_progress.progress(progress_percent)
            status_text.text(f"Processing {i+1}/{total_files}: {uploaded_file.name}")
            
            result = process_single_sheet(uploaded_file, set_choice)
            
            if result:
                summary_data.append({
                    "Filename": uploaded_file.name,
                    "Student ID": result.get("student_id", "N/A"),
                    "Total Score": f"{result['total_score']}/{result['total_questions']}",
                    "Percentage": f"{result['percentage']:.1f}%",
                    "Processing Time": f"{result['processing_time']:.2f}s",
                    "Status": "✅ Success"
                })
            else:
                summary_data.append({
                    "Filename": uploaded_file.name,
                    "Student ID": "N/A",
                    "Total Score": "N/A",
                    "Percentage": "N/A",
                    "Processing Time": "N/A",
                    "Status": "❌ Failed"
                })
                
        except Exception as e:
            summary_data.append({
                "Filename": uploaded_file.name,
                "Student ID": "N/A",
                "Total Score": "N/A",
                "Percentage": "N/A",
                "Processing Time": "N/A",
                "Status": f"❌ Error: {str(e)[:50]}"
            })
    
    # Complete progress
    overall_progress.progress(1.0)
    status_text.text("✅ All files processed!")
    
    # Display summary table
    if summary_data:
        st.subheader("📊 Bulk Processing Summary")
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)
        
        # Calculate statistics
        successful = len([s for s in summary_data if "Success" in s["Status"]])
        failed = len(summary_data) - successful
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Processed", len(summary_data))
        with col2:
            st.metric("Successful", successful)
        with col3:
            st.metric("Failed", failed)
        
        # Add export button for all results
        if successful > 0:
            st.subheader("📥 Export Options")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Download All Results (CSV)"):
                    download_url = f"{API_BASE_URL}/export/all/csv"
                    st.markdown(f"[Click here to download CSV]({download_url})")
            
            with col2:
                st.info("CSV file contains detailed results for all processed sheets")

def process_single_sheet(uploaded_file, set_choice):
    """Process a single OMR sheet"""
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Upload file
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"exam_version": set_choice}
        
        upload_response = requests.post(
            f"{API_BASE_URL}/upload-sheet/",
            files=files,
            data=data,
            timeout=30
        )
        
        if upload_response.status_code != 200:
            st.error(f"Upload failed for {uploaded_file.name}: {upload_response.text}")
            return None

        sheet_id = upload_response.json()["sheet_id"]
        
        # Process sheet
        process_response = requests.post(
            f"{API_BASE_URL}/process-sheet/{sheet_id}",
            params={"exam_version": set_choice},
            timeout=30
        )
        
        if process_response.status_code != 200:
            st.error(f"Processing failed for {uploaded_file.name}: {process_response.text}")
            return None

        result = process_response.json()
        return result

    except requests.exceptions.RequestException as e:
        st.error(f"Network error for {uploaded_file.name}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None

def display_single_result(result, sheet_id):
    """Display results for a single processed sheet"""
    st.success("✅ OMR Sheet processed successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Score", f"{result['total_score']}/{result['total_questions']}")
    with col2:
        st.metric("Percentage", f"{result['percentage']:.1f}%")
    with col3:
        st.metric("Processing Time", f"{result['processing_time']:.2f}s")
    
    # Subject-wise results
    st.subheader("📊 Subject-wise Results")
    
    subject_data = []
    for subject, scores in result['subject_scores'].items():
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
    
    # Export option
    st.subheader("📥 Export Results")
    download_url = f"{API_BASE_URL}/export/sheet/{sheet_id}/csv"
    st.markdown(f"[📄 Download Results as CSV]({download_url})")

def view_results_page():
    st.header("📊 View Results")
    
    try:
        response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
        if response.status_code == 200:
            sheets_data = response.json()
            sheets = sheets_data["sheets"]
            
            if sheets:
                sheet_options = [f"Sheet {sheet['id']} - {sheet['student_id']} ({sheet['status']})" for sheet in sheets]
                selected_option = st.selectbox("Select a sheet to view results:", sheet_options)
                
                if selected_option:
                    sheet_id = int(selected_option.split(" ")[1])
                    display_detailed_results(sheet_id)
            else:
                st.info("No sheets processed yet. Upload and process a sheet first.")
        else:
            st.error(f"Failed to fetch sheets list: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
        st.info("Make sure the backend server is running")

def display_detailed_results(sheet_id):
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
                
                # Export button
                st.subheader("📥 Export Results")
                download_url = f"{API_BASE_URL}/export/sheet/{sheet_id}/csv"
                st.markdown(f"[📄 Download Results as CSV]({download_url})")
            else:
                st.warning(f"Sheet status: {results['status']}. Results may not be available yet.")
                
        else:
            st.error(f"Failed to fetch results for sheet {sheet_id}: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def dashboard_page():
    st.header("📈 Dashboard")
    
    try:
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
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Status distribution
                    status_counts = {}
                    for sheet in sheets:
                        status = sheet["status"]
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    fig_status = px.pie(
                        values=list(status_counts.values()),
                        names=list(status_counts.keys()),
                        title="Processing Status Distribution"
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                
                with col2:
                    # Score distribution
                    if valid_scores:
                        fig_scores = px.histogram(
                            x=valid_scores,
                            nbins=10,
                            title="Score Distribution"
                        )
                        st.plotly_chart(fig_scores, use_container_width=True)
                    else:
                        st.info("No score data available yet")
                
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
                
                # Export all results
                st.subheader("📥 Export All Data")
                download_url = f"{API_BASE_URL}/export/all/csv"
                st.markdown(f"[📄 Download All Results as CSV]({download_url})")
                
            else:
                st.info("No data available yet. Process some OMR sheets to see dashboard statistics.")
        else:
            st.error(f"Failed to fetch dashboard data: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def about_page():
    st.header("ℹ️ About OMR Evaluation System")
    
    st.markdown("""
    ## 🎯 Overview
    
    The **Automated OMR Evaluation System** streamlines the evaluation process for 
    Optical Mark Recognition (OMR) sheets in educational assessments.
    
    ## 🚀 Key Features
    
    - **✅ Bulk Upload**: Process multiple OMR sheets simultaneously
    - **✅ Auto ID Generation**: Automatic student and exam ID assignment
    - **✅ Mobile Back Camera**: Optimized back camera capture for mobile devices
    - **✅ Real-time Results**: Instant processing and scoring
    - **✅ CSV Export**: Download results in Excel-compatible format
    - **✅ Subject-wise Analysis**: Detailed breakdown by subject areas
    - **✅ Dashboard Analytics**: Comprehensive statistics and insights
    - **✅ Secure Database**: All results stored securely with audit trail
    
    ## 📱 Mobile Features
    
    - **Back Camera Support**: Uses device's back camera for better OMR capture
    - **Mobile Optimized**: Responsive design for mobile devices
    - **Touch Friendly**: Large buttons and intuitive interface
    
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
    - **Version**: 1.0.0 with Mobile Back Camera Support
    - **Last Updated**: September 2025
    
    ## 📦 Dependencies
    
    **Required packages:**
    - streamlit
    - requests
    - pandas
    - plotly
    - pillow
    
    **Optional (for mobile back camera):**
    - streamlit-back-camera-input
    
    **Installation:**
    ```bash
    pip install streamlit-back-camera-input
    ```
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
        return "🔴 Offline"

if __name__ == "__main__":
    main()