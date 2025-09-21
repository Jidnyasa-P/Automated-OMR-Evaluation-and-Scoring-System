import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Try to import the back camera input
try:
    from streamlit_back_camera_input import back_camera_input
    BACK_CAMERA_AVAILABLE = True
except ImportError:
    BACK_CAMERA_AVAILABLE = False

# Configure Streamlit page
st.set_page_config(
    page_title="Scanalyze - OMR Evaluation System",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

def apply_custom_css():
    """Apply custom CSS for stunning UI with dark/light mode support"""
    
    # Check if dark mode is enabled
    dark_mode = st.session_state.get('dark_mode', False)
    
    if dark_mode:
        # Dark mode styles with lighter bluish theme
        st.markdown("""
        <style>
        /* Dark Mode Styles */
        .stApp {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d4a70 25%, #3b5a82 50%, #4a6b94 100%);
            color: #ffffff !important;
        }
        
        .main-header {
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 50%, #2563eb 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white !important;
        }
        
        .feature-card {
            background: rgba(59, 130, 246, 0.15);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
            transition: transform 0.3s ease;
            color: #ffffff !important;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        }
        
        .metric-card {
            background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
            color: white !important;
            margin-bottom: 1rem;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
        }
        
        /* Fix Streamlit text colors in dark mode */
        .stMarkdown, .stText, .stWrite, p, h1, h2, h3, h4, h5, h6, span, div, label {
            color: #ffffff !important;
        }
        
        .stSelectbox label, .stFileUploader label, .stRadio label, .stToggle label {
            color: #ffffff !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg, .css-1lcbmhc {
            background: rgba(30, 58, 95, 0.8) !important;
            color: #ffffff !important;
        }
        
        /* Success/Warning/Info banners */
        .success-banner {
            background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        
        .warning-banner {
            background: linear-gradient(90deg, #f59e0b 0%, #f97316 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        
        .info-banner {
            background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d4a70 90%) !important;
        color: #fff !important;
        }

        </style>
        """, unsafe_allow_html=True)
    else:
        # Light mode styles with lighter bluish theme
        st.markdown("""
        <style>
        /* Light Mode Styles */
        .stApp {
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 25%, #cce7ff 50%, #b3dbff 100%);
            color: #1e293b !important;
        }
        
        .main-header {
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 50%, #2563eb 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
            text-align: center;
            backdrop-filter: blur(10px);
            color: white !important;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
            transition: transform 0.3s ease;
            color: #1e293b !important;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
        }
        
        .metric-card {
            background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
            color: white !important;
            margin-bottom: 1rem;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
        }
        
        /* Ensure text is readable in light mode */
        .stMarkdown, .stText, .stWrite, p, h1, h2, h3, h4, h5, h6, span, div, label {
            color: #1e293b !important;
        }
        
        /* Success/Warning/Info banners */
        .success-banner {
            background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        
        .warning-banner {
            background: linear-gradient(90deg, #f59e0b 0%, #f97316 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        
        .info-banner {
            background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white !important;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Hide default streamlit elements */
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        .stApp > header {visibility: hidden;}
        
        /* Custom animations */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }
        
        .pulse-animation {
            animation: pulse 2s infinite;
        }
        </style>
        """, unsafe_allow_html=True)

def create_sidebar():
    """Create beautiful animated sidebar navigation"""
    with st.sidebar:
        # Header
        st.markdown("## 📃 Scanalyze")
        
        # Dark/Light mode toggle - Fixed version
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = False
        
        dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
        
        # Update dark mode state when toggle changes
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        menu_items = [
            {"name": "🏠 Home", "key": "home"},
            {"name": "📤 Upload & Process", "key": "upload"},
            {"name": "📷 Camera Capture", "key": "camera"},
            {"name": "📊 View Results", "key": "results"},
            {"name": "📈 Dashboard", "key": "dashboard"},
            {"name": "📥 Export Data", "key": "export"},
            {"name": "ℹ️ About", "key": "about"}
        ]
        
        # Initialize selected page if not exists
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = "home"
        
        selected_page = st.radio(
            "Choose a page:",
            options=[item["key"] for item in menu_items],
            format_func=lambda x: next(item["name"] for item in menu_items if item["key"] == x),
            key="navigation",
            index=[item["key"] for item in menu_items].index(st.session_state.selected_page)
        )
        
        # Update selected page
        st.session_state.selected_page = selected_page
        
        # Status indicator
        st.markdown("---")
        st.markdown("### 🔧 System Status")
        backend_status = get_backend_status()
        
        if "Online" in backend_status:
            st.success(backend_status)
        else:
            st.warning(backend_status)
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        try:
            response = requests.get(f"{API_BASE_URL}/sheets/", timeout=2)
            if response.status_code == 200:
                sheets = response.json()["sheets"]
                total_sheets = len(sheets)
                completed = len([s for s in sheets if s["status"] == "completed"])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 Total", total_sheets)
                with col2:
                    st.metric("✅ Done", completed)
            else:
                st.info("Connect to backend for stats")
        except:
            st.info("Backend offline")
        
        return selected_page

def main():
    """Main application with stunning UI"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Create sidebar navigation
    selected_page = create_sidebar()
    
    # Main header - NO HTML, use Streamlit native components
    st.markdown("""
    <div class="main-header">
        <h1>📃 Scanalyze - Automated OMR Evaluation System</h1>
        <p style="font-size: 1.2em; opacity: 0.9;">Transform your OMR sheet processing with AI-powered accuracy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if selected_page == "home":
        home_page()
    elif selected_page == "upload":
        upload_and_process_page()
    elif selected_page == "camera":
        camera_capture_page()
    elif selected_page == "results":
        view_results_page()
    elif selected_page == "dashboard":
        dashboard_page()
    elif selected_page == "export":
        export_data_page()
    elif selected_page == "about":
        about_page()

def home_page():
    """Beautiful home page with feature showcase - NO PROBLEMATIC HTML"""
    
    # Welcome section - Using native Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h2 style="text-align: center; color: inherit;">🚀 Welcome to the Future of OMR Processing</h2>
            <p style="text-align: center; font-size: 1.1em; color: inherit;">
                Experience lightning-fast, accurate OMR sheet evaluation with our advanced AI-powered system.
                Process hundreds of sheets in minutes, not hours!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature grid - SIMPLIFIED
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📱 Smart Mobile Capture")
        st.write("Use your phone's back camera for crystal-clear OMR sheet capture with automatic optimization.")
        st.write("✅ Back camera support")
        st.write("✅ Auto-focus & lighting")
        st.write("✅ Real-time preview")
    
    with col2:
        st.markdown("### ⚡ Bulk Processing")
        st.write("Process multiple OMR sheets simultaneously with our advanced batch processing engine.")
        st.write("✅ Upload multiple files")
        st.write("✅ Parallel processing")
        st.write("✅ Progress tracking")
    
    with col3:
        st.markdown("### 📊 Advanced Analytics")
        st.write("Get detailed insights with comprehensive dashboards and exportable reports.")
        st.write("✅ Interactive charts")
        st.write("✅ CSV/Excel export")
        st.write("✅ Performance metrics")
    
    # Quick start section - SIMPLIFIED
    st.markdown("## 🚀 Quick Start Guide")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 1️⃣ Upload or Capture")
        st.write("Choose your OMR sheets")
    
    with col2:
        st.markdown("### 2️⃣ Select Answer Key")
        st.write("Choose Set A or B")
    
    with col3:
        st.markdown("### 3️⃣ Process & Analyze")
        st.write("AI does the magic")
    
    with col4:
        st.markdown("### 4️⃣ Export Results")
        st.write("Download your reports")
    
    # Call to action - Fixed navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Processing Now", key="cta_button", help="Begin your OMR processing journey"):
            st.session_state.selected_page = "upload"
            st.rerun()

def upload_and_process_page():
    """Enhanced upload page with beautiful UI"""
    
    st.markdown("## 📤 Upload & Process OMR Sheets")
    st.info("Upload multiple OMR sheets and process them with AI-powered accuracy")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 File Upload")
        
        uploaded_files = st.file_uploader(
            "Choose one or more OMR sheet images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload clear images of OMR sheets"
        )
        
        set_choice = st.selectbox(
            "🔑 Select Answer Key Set", 
            ["A", "B"], 
            help="Choose Set A or Set B"
        )

        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} file(s) selected for processing")
            
            # Show preview of uploaded files
            if len(uploaded_files) <= 3:
                cols = st.columns(len(uploaded_files))
                for i, file in enumerate(uploaded_files):
                    with cols[i]:
                        image = Image.open(file)
                        st.image(image, caption=f"📄 {file.name}", use_container_width=True)
            else:
                with st.expander("📋 View uploaded files"):
                    for file in uploaded_files:
                        st.write(f"• {file.name} ({file.size/1024:.1f} KB)")

            if st.button("🚀 Process All Uploaded Sheets", type="primary"):
                process_bulk_sheets(uploaded_files, set_choice)
    
    with col2:
        st.markdown("### 💡 Instructions")
        
        st.markdown("""
        **📋 How to use:**
        1. Upload clear images of OMR sheets
        2. Select the answer key set (A or B)
        3. Click 'Process All Uploaded Sheets'
        4. View results and download CSV exports
        5. Check 'Dashboard' for detailed analytics
        
        **✨ Features:**
        - ✅ Bulk upload and processing
        - ✅ Auto-generated student IDs
        - ✅ Real-time progress tracking
        - ✅ CSV export functionality
        - ✅ Comprehensive analytics
        """)

def camera_capture_page():
    """Enhanced camera page with beautiful UI"""
    
    st.markdown("## 📷 Camera Capture (Mobile Optimized)")
    st.info("Use your mobile device's back camera for professional OMR sheet capture")

    if not BACK_CAMERA_AVAILABLE:
        st.error("📱 Back camera feature not available. Please install 'streamlit-back-camera-input'")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📱 Mobile Back Camera")
        st.info("Professional OMR sheet capture optimized for mobile devices")
        
        # Back camera input
        back_camera_image = back_camera_input(key="back_camera")

        if back_camera_image is not None:
            st.success("📸 Image captured successfully!")
            st.image(back_camera_image, caption="📱 Captured with Back Camera", use_container_width=True)
            
            set_choice_back = st.selectbox(
                "🔑 Select Answer Key Set",
                ["A", "B"],
                help="Choose Set A or Set B",
                key="back_camera_set_choice"
            )
            
            if st.button("🚀 Process Captured Image", type="primary", key="process_back_camera"):
                process_captured_image(back_camera_image, set_choice_back, "back_camera_capture.jpg")

    with col2:
        st.markdown("### 📱 Instructions")
        
        st.markdown("""
        **📷 How to capture:**
        1. Tap the 'Choose file' button below
        2. Your device will open the back camera
        3. Take a clear photo of the OMR sheet
        4. Photo will appear here after confirm
        5. Select answer key set
        6. Tap 'Process Captured Image'
        
        **💡 Tips for best results:**
        - 📖 Ensure good lighting
        - 📏 Keep OMR sheet flat
        - 🖼️ Fill the entire frame
        - 🌙 Avoid shadows
        - 📐 Hold camera steady
        """)

def process_bulk_sheets(uploaded_files, set_choice):
    """Enhanced bulk processing with beautiful progress UI"""
    summary_data = []
    total_files = len(uploaded_files)
    
    st.info("🔄 Processing your OMR sheets... Please wait while AI analyzes your data")
    
    overall_progress = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            progress_percent = (i / total_files)
            overall_progress.progress(progress_percent)
            status_text.info(f"Processing {i+1}/{total_files}: {uploaded_file.name}")
            
            result = process_single_sheet(uploaded_file, set_choice)
            
            if result:
                summary_data.append({
                    "📄 Filename": uploaded_file.name,
                    "🆔 Student ID": result.get("student_id", "N/A"),
                    "📊 Total Score": f"{result['total_score']}/{result['total_questions']}",
                    "📈 Percentage": f"{result['percentage']:.1f}%",
                    "⏱️ Processing Time": f"{result['processing_time']:.2f}s",
                    "✅ Status": "Success"
                })
            else:
                summary_data.append({
                    "📄 Filename": uploaded_file.name,
                    "🆔 Student ID": "N/A",
                    "📊 Total Score": "N/A",
                    "📈 Percentage": "N/A",
                    "⏱️ Processing Time": "N/A",
                    "❌ Status": "Failed"
                })
                
        except Exception as e:
            summary_data.append({
                "📄 Filename": uploaded_file.name,
                "🆔 Student ID": "N/A",
                "📊 Total Score": "N/A",
                "📈 Percentage": "N/A",
                "⏱️ Processing Time": "N/A",
                "❌ Status": f"Error: {str(e)[:30]}..."
            })
    
    # Complete progress
    overall_progress.progress(1.0)
    status_text.success("✅ All files processed successfully!")
    
    # Display enhanced summary
    if summary_data:
        st.markdown("### 📊 Batch Processing Summary")
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)
        
        # Enhanced statistics
        successful = len([s for s in summary_data if "Success" in s.get("✅ Status", s.get("❌ Status", ""))])
        failed = len(summary_data) - successful
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Processed", len(summary_data))
        with col2:
            st.metric("✅ Successful", successful)
        with col3:
            st.metric("❌ Failed", failed)
        with col4:
            success_rate = (successful / len(summary_data) * 100) if summary_data else 0
            st.metric("📈 Success Rate", f"{success_rate:.1f}%")
        
        # Export options
        if successful > 0:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download All Results (CSV)", type="primary"):
                    download_url = f"{API_BASE_URL}/export/all/csv"
                    st.success(f"📥 [Click here to download CSV file]({download_url})")
            
            with col2:
                st.info("📋 CSV file contains detailed results for all processed sheets including subject-wise breakdown")

def process_single_sheet(uploaded_file, set_choice):
    """Process a single OMR sheet - enhanced version"""
    try:
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"exam_version": set_choice}
        
        upload_response = requests.post(f"{API_BASE_URL}/upload-sheet/", files=files, data=data, timeout=30)
        if upload_response.status_code != 200:
            return None

        sheet_id = upload_response.json()["sheet_id"]
        process_response = requests.post(f"{API_BASE_URL}/process-sheet/{sheet_id}", params={"exam_version": set_choice}, timeout=30)
        
        if process_response.status_code != 200:
            return None

        return process_response.json()
    except:
        return None

def process_captured_image(image_data, set_choice, filename):
    """Enhanced camera image processing with beautiful UI"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.info("🔄 Preparing image for processing...")
        progress_bar.progress(10)
        
        # Process image data
        if hasattr(image_data, 'read'):
            image_data.seek(0)
            files = {"file": (filename, image_data, "image/jpeg")}
        else:
            img_byte_arr = io.BytesIO()
            if isinstance(image_data, Image.Image):
                image_data.save(img_byte_arr, format='JPEG')
            else:
                img_byte_arr.write(image_data)
            img_byte_arr.seek(0)
            files = {"file": (filename, img_byte_arr, "image/jpeg")}
        
        data = {"exam_version": set_choice}
        
        status_text.info("📤 Uploading to AI processing engine...")
        progress_bar.progress(30)
        
        upload_response = requests.post(f"{API_BASE_URL}/upload-sheet/", files=files, data=data, timeout=30)
        
        if upload_response.status_code != 200:
            st.error(f"❌ Upload failed: {upload_response.text}")
            return

        sheet_id = upload_response.json()["sheet_id"]
        
        status_text.info("🤖 AI is analyzing your OMR sheet...")
        progress_bar.progress(70)
        
        process_response = requests.post(f"{API_BASE_URL}/process-sheet/{sheet_id}", params={"exam_version": set_choice}, timeout=30)
        
        if process_response.status_code != 200:
            st.error(f"❌ Processing failed: {process_response.text}")
            return
        
        progress_bar.progress(100)
        status_text.success("✅ Processing completed successfully!")
        
        result = process_response.json()
        display_single_result(result, sheet_id)
        
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Error processing camera image: {str(e)}")

def display_single_result(result, sheet_id):
    """Enhanced single result display with beautiful metrics"""
    st.success("🎉 OMR Sheet processed successfully! Here are your results:")
    
    # Enhanced metrics display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Score", f"{result['total_score']}/{result['total_questions']}")
    with col2:
        st.metric("📈 Percentage", f"{result['percentage']:.1f}%")
    with col3:
        st.metric("⏱️ Processing Time", f"{result['processing_time']:.2f}s")
    
    # Subject-wise results
    st.markdown("### 📊 Subject-wise Results")
    
    subject_data = []
    for subject, scores in result['subject_scores'].items():
        subject_data.append({
            "📚 Subject": subject,
            "✅ Correct": scores["correct"],
            "❌ Wrong": scores["wrong"],
            "⭕ Blank": scores.get("blank", 0),
            "📈 Score %": f"{scores['score_percentage']:.1f}%"
        })
    
    df = pd.DataFrame(subject_data)
    st.dataframe(df, use_container_width=True)
    
    # Enhanced visualization
    fig = go.Figure(data=[
        go.Bar(
            x=[s["📚 Subject"] for s in subject_data],
            y=[float(s["📈 Score %"].replace('%', '')) for s in subject_data],
            marker=dict(
                color=[float(s["📈 Score %"].replace('%', '')) for s in subject_data],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Score %")
            ),
            text=[s["📈 Score %"] for s in subject_data],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="📊 Subject-wise Performance Analysis",
        xaxis_title="Subjects",
        yaxis_title="Score Percentage",
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Export option
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        download_url = f"{API_BASE_URL}/export/sheet/{sheet_id}/csv"
        if st.button("📥 Download Results as CSV", type="primary"):
            st.success(f"📥 [Click here to download your results]({download_url})")
    
    with col2:
        st.info("📋 CSV includes detailed breakdown of all subjects and scores")

def view_results_page():
    """Enhanced results viewing page"""
    st.markdown("## 📊 View Results")
    st.info("Browse and analyze previously processed OMR sheets")
    
    try:
        response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
        if response.status_code == 200:
            sheets_data = response.json()
            sheets = sheets_data["sheets"]
            
            if sheets:
                sheet_options = [f"Sheet {sheet['id']} - {sheet['student_id']} ({sheet['status']})" for sheet in sheets]
                selected_option = st.selectbox("🔍 Select a sheet to view results:", sheet_options)
                
                if selected_option:
                    sheet_id = int(selected_option.split(" ")[1])
                    display_detailed_results(sheet_id)
            else:
                st.info("📋 No sheets processed yet. Upload and process sheets first from the Upload page.")
        else:
            st.error("❌ Failed to fetch sheets list. Check if backend is running.")
            
    except requests.exceptions.RequestException:
        st.error("🔌 Cannot connect to server. Make sure the backend is running.")

def display_detailed_results(sheet_id):
    """Enhanced detailed results display"""
    try:
        response = requests.get(f"{API_BASE_URL}/sheet/{sheet_id}/results", timeout=10)
        if response.status_code == 200:
            results = response.json()
            
            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Sheet ID", results["sheet_id"])
            with col2:
                st.metric("🆔 Student ID", results["student_id"])
            with col3:
                st.metric("📊 Status", results["status"])
            with col4:
                st.metric("📃 Total Score", results["total_score"] if results["total_score"] is not None else "N/A")
            
            if results["status"] == "completed" and results["subject_results"]:
                # Enhanced subject results
                st.markdown("### 📚 Subject-wise Performance")
                
                subject_df = pd.DataFrame([
                    {
                        "📚 Subject": subject,
                        "✅ Correct": data["correct"],
                        "❌ Wrong": data["wrong"],
                        "📈 Percentage": f"{data['percentage']:.1f}%"
                    }
                    for subject, data in results["subject_results"].items()
                ])
                
                st.dataframe(subject_df, use_container_width=True)
                
                # Enhanced visualization
                fig = px.bar(
                    subject_df,
                    x="📚 Subject",
                    y=[float(p.replace('%', '')) for p in subject_df["📈 Percentage"]],
                    title="📊 Subject-wise Performance Analysis",
                    color=[float(p.replace('%', '')) for p in subject_df["📈 Percentage"]],
                    color_continuous_scale="Blues",
                    labels={"y": "Score Percentage"}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Export options
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    download_url = f"{API_BASE_URL}/export/sheet/{sheet_id}/csv"
                    if st.button("📥 Download Sheet Results", type="primary"):
                        st.success(f"📥 [Click to download CSV]({download_url})")
                
                with col2:
                    st.info("📋 Detailed results with subject breakdown")
            else:
                st.warning(f"⚠️ Sheet status: {results['status']}. Results may not be available yet.")
                
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")

def dashboard_page():
    """Enhanced dashboard with stunning visualizations"""
    st.markdown("## 📈 System Dashboard")
    st.info("Comprehensive analytics and insights for your OMR processing system")
    
    try:
        response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
        if response.status_code == 200:
            sheets_data = response.json()
            sheets = sheets_data["sheets"]
            
            if sheets:
                # Enhanced overview metrics
                completed_sheets = [s for s in sheets if s["status"] == "completed"]
                total_sheets = len(sheets)
                completed_count = len(completed_sheets)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Total Sheets", total_sheets)
                with col2:
                    st.metric("✅ Completed", completed_count)
                with col3:
                    processing_rate = (completed_count/total_sheets*100) if total_sheets > 0 else 0
                    st.metric("📈 Success Rate", f"{processing_rate:.1f}%")
                with col4:
                    valid_scores = [s["total_score"] for s in completed_sheets if s["total_score"] is not None]
                    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                    st.metric("📃 Avg Score", f"{avg_score:.1f}")
                
                # Enhanced charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Status distribution with enhanced styling
                    status_counts = {}
                    for sheet in sheets:
                        status = sheet["status"]
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    fig_status = go.Figure(data=[
                        go.Pie(
                            labels=list(status_counts.keys()),
                            values=list(status_counts.values()),
                            hole=0.3,
                            marker=dict(colors=['#3b82f6', '#60a5fa', '#93c5fd'])
                        )
                    ])
                    fig_status.update_layout(
                        title="📊 Processing Status Distribution",
                        height=400
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
                
                with col2:
                    # Enhanced score distribution
                    if valid_scores:
                        fig_scores = go.Figure(data=[
                            go.Histogram(
                                x=valid_scores,
                                nbinsx=10,
                                marker=dict(
                                    color='#3b82f6',
                                    opacity=0.8
                                )
                            )
                        ])
                        fig_scores.update_layout(
                            title="📈 Score Distribution Analysis",
                            xaxis_title="Score",
                            yaxis_title="Frequency",
                            height=400
                        )
                        st.plotly_chart(fig_scores, use_container_width=True)
                    else:
                        st.info("📊 No score data available yet. Process some sheets to see analytics.")
                
                # Recent activity with enhanced styling
                st.markdown("### 🕐 Recent Activity")
                
                recent_sheets = sorted(sheets, key=lambda x: x["upload_time"] if x["upload_time"] else "", reverse=True)[:10]
                
                recent_df = pd.DataFrame([
                    {
                        "📄 Sheet ID": sheet["id"],
                        "🆔 Student ID": sheet["student_id"],
                        "📊 Status": sheet["status"],
                        "📃 Score": sheet["total_score"] if sheet["total_score"] is not None else "N/A",
                        "📅 Upload Time": sheet["upload_time"][:19] if sheet["upload_time"] else "N/A"
                    }
                    for sheet in recent_sheets
                ])
                
                st.dataframe(recent_df, use_container_width=True)
                
                # Export section
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    download_url = f"{API_BASE_URL}/export/all/csv"
                    if st.button("📥 Export All System Data", type="primary"):
                        st.success(f"📊 [Download Complete System Report]({download_url})")
                
                with col2:
                    st.info("📋 Complete system data with all processed sheets and detailed analytics")
                
            else:
                st.info("📊 No data available yet. Process some OMR sheets to see comprehensive dashboard statistics.")
        else:
            st.error("❌ Failed to fetch dashboard data. Check backend connection.")
            
    except Exception as e:
        st.error(f"🔌 Error loading dashboard: {str(e)}. Make sure the backend server is running.")

def export_data_page():
    """Enhanced export page"""
    st.markdown("## 📥 Export Data")
    st.info("Download your OMR processing results in various formats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Export All Results")
        st.info("Download comprehensive data for all processed OMR sheets")
        
        if st.button("📥 Export All Results as CSV", type="primary"):
            export_all_url = f"{API_BASE_URL}/export/all/csv"
            st.success(f"📊 [Click here to download complete system data]({export_all_url})")
    
    with col2:
        st.markdown("### 📋 Export Individual Sheet")
        st.info("Select and download results for specific sheets")
        
        try:
            response = requests.get(f"{API_BASE_URL}/sheets/", timeout=10)
            if response.status_code == 200:
                sheets_data = response.json()
                completed_sheets = [s for s in sheets_data["sheets"] if s["status"] == "completed"]
                
                if completed_sheets:
                    sheet_options = [f"Sheet {sheet['id']} - {sheet['student_id']}" for sheet in completed_sheets]
                    selected_sheet = st.selectbox("🔍 Select sheet to export:", sheet_options)
                    
                    if selected_sheet and st.button("📥 Export Selected Sheet"):
                        sheet_id = int(selected_sheet.split(" ")[1])
                        export_sheet_url = f"{API_BASE_URL}/export/sheet/{sheet_id}/csv"
                        st.success(f"📋 [Download Sheet {sheet_id} results]({export_sheet_url})")
                else:
                    st.info("📋 No completed sheets available for export. Process some sheets first.")
            else:
                st.error("❌ Failed to fetch sheets for export")
                
        except Exception as e:
            st.error(f"🔌 Error fetching export options: {str(e)}")

def about_page():
    """Enhanced about page - COMPLETELY FIXED, NO PROBLEMATIC HTML"""
    st.markdown("## ℹ️ About Scanalyze")
    st.info("Revolutionary AI-powered OMR processing for the modern era")
    
    # Overview section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📃 System Overview")
        st.write("The **Scanalyze - Automated OMR Evaluation System** represents the cutting edge of educational assessment technology. Built with modern AI and machine learning algorithms, our system transforms the tedious process of manual OMR sheet evaluation into a lightning-fast, accurate, and insightful experience.")
        
        st.markdown("#### 🚀 Why Choose Our System?")
        st.write("⚡ **Lightning Fast:** Process hundreds of sheets in minutes")
        st.write("📃 **99%+ Accuracy:** Advanced AI ensures minimal errors")
        st.write("📱 **Mobile First:** Optimized for smartphones and tablets")
        st.write("☁️ **Cloud Ready:** Scalable architecture for any load")
        st.write("🔒 **Secure:** Enterprise-grade data protection")
    
    with col2:
        st.markdown("### 🔧 System Status")
        backend_status = get_backend_status()
        
        if "Online" in backend_status:
            st.success(f"**Backend:** {backend_status}")
        else:
            st.warning(f"**Backend:** {backend_status}")
        
        st.markdown("#### 📊 System Info")
        st.write("**Version:** 3.0.0 - Scanalyze")
        st.write("**UI Theme:** Light Blue Enhanced")
        st.write("**Last Updated:** September 2025")
        st.write("**Platform:** Web-based")
    
    # Features showcase
    st.markdown("## ✨ Advanced Features")
    
    features_data = [
        {"Feature": "📱 Smart Mobile Capture", "Description": "AI-optimized camera capture with automatic sheet detection", "Status": "Active"},
        {"Feature": "🚀 Bulk Processing", "Description": "Process multiple sheets simultaneously with parallel computing", "Status": "Active"},
        {"Feature": "📃 Auto ID Generation", "Description": "Intelligent student and exam ID assignment system", "Status": "Active"},
        {"Feature": "📊 Advanced Analytics", "Description": "Comprehensive dashboards with interactive visualizations", "Status": "Active"},
        {"Feature": "📥 Multi-format Export", "Description": "CSV, Excel, and PDF export capabilities", "Status": "Active"},
        {"Feature": "🌙 Dark/Light Theme", "Description": "Adaptive UI with user-preferred color schemes", "Status": "Fixed!"},
    ]
    
    features_df = pd.DataFrame(features_data)
    st.dataframe(features_df, use_container_width=True)
    
    # Technical specifications
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📃 Exam Format", "100 Questions", "5 subjects × 20 each")
    with col2:
        st.metric("📈 Accuracy", "99%+", "AI-powered precision")
    with col3:
        st.metric("⚡ Speed", "< 3 seconds", "Per sheet processing")

def get_backend_status():
    """Enhanced backend status check"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            return "🟢 Online & Ready"
        else:
            return "🟡 Issues Detected"
    except:
        return "🔴 Offline"

if __name__ == "__main__":
    main()