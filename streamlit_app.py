# streamlit_app.py

import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json
import plotly.express as px

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
        ["Upload & Process", "View Results", "Dashboard", "About"]
    )
    
    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "View Results":
        view_results_page()
    elif page == "Dashboard":
        dashboard_page()
    else:
        about_page()

def upload_and_process_page():
    st.header("📤 Upload & Process OMR Sheet")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "Choose an OMR sheet image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of the OMR sheet"
        )
        
        # Select answer key set
        set_choice = st.selectbox(
            "Select Answer Key Set",
            ["A", "B"]
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded OMR Sheet", use_column_width=True)
            
            if st.button("🚀 Process OMR Sheet"):
                process_omr_sheet(uploaded_file, set_choice)
    
    with col2:
        st.subheader("Instructions")
        st.info("""
        1. Upload a clear image of the OMR sheet  
        2. Select the answer key set (A or B)  
        3. Click 'Process OMR Sheet'  
        4. View results in the 'View Results' tab  
        """)

def process_omr_sheet(uploaded_file, set_choice):
    try:
        # Upload file
        files = {"file": uploaded_file}
        data = {"exam_version": set_choice}
        upload_resp = requests.post(
            f"{API_BASE_URL}/upload-sheet/",
            files=files,
            data=data
        )
        upload_resp.raise_for_status()
        sheet_id = upload_resp.json()["sheet_id"]
        
        # Process sheet
        process_resp = requests.post(
            f"{API_BASE_URL}/process-sheet/{sheet_id}",
            params={"exam_version": set_choice}
        )
        process_resp.raise_for_status()
        result = process_resp.json()
        
        # Display metrics
        st.success("✅ OMR Sheet processed successfully!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Score", f"{result['total_score']}/{result['total_questions']}")
        col2.metric("Percentage", f"{result['percentage']:.1f}%")
        col3.metric("Processing Time", f"{result['processing_time']:.2f}s")
        
        # Subject-wise results
        st.subheader("📊 Subject-wise Results")
        subject_data = []
        for subject, scores in result['subject_scores'].items():
            subject_data.append({
                "Subject": subject,
                "Correct": scores["correct"],
                "Wrong": scores["wrong"],
                "Blank": scores["blank"] if "blank" in scores else 0,
                "Score %": scores["score_percentage"]
            })
        df = pd.DataFrame(subject_data)
        st.dataframe(df, use_container_width=True)
        
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
        
        # Save last processed sheet for view
        st.session_state['last_processed_sheet'] = sheet_id
        
    except Exception as e:
        st.error(f"Error: {e}")

def view_results_page():
    st.header("📊 View Results")
    try:
        resp = requests.get(f"{API_BASE_URL}/sheets/")
        resp.raise_for_status()
        sheets = resp.json().get("sheets", [])
        
        if not sheets:
            st.info("No sheets processed yet.")
            return
        
        options = [f"Sheet {s['id']} ({s['status']})" for s in sheets]
        choice = st.selectbox("Select a sheet:", options)
        sheet_id = int(choice.split()[1])
        display_sheet_results(sheet_id)
    except Exception as e:
        st.error(f"Error fetching sheets: {e}")

def display_sheet_results(sheet_id):
    try:
        resp = requests.get(f"{API_BASE_URL}/sheet/{sheet_id}/results")
        resp.raise_for_status()
        data = resp.json()
        
        st.metric("Sheet ID", data["sheet_id"])
        st.metric("Status", data["status"])
        st.metric("Total Score", data.get("total_score", "N/A"))
        
        if data["status"] == "completed":
            df = pd.DataFrame([
                {
                    "Subject": s,
                    "Correct": stats["correct"],
                    "Wrong": stats["wrong"],
                    "Percentage": stats["percentage"]
                }
                for s, stats in data["subject_results"].items()
            ])
            st.dataframe(df, use_container_width=True)
            fig = px.bar(df, x="Subject", y="Percentage", title="Subject-wise Performance", color="Percentage", color_continuous_scale="RdYlGn")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching results: {e}")

def dashboard_page():
    st.header("📈 Dashboard")
    try:
        resp = requests.get(f"{API_BASE_URL}/sheets/")
        resp.raise_for_status()
        sheets = resp.json().get("sheets", [])
        if not sheets:
            st.info("No data available.")
            return
        
        completed = [s for s in sheets if s["status"] == "completed"]
        total = len(sheets)
        st.metric("Total Sheets", total)
        st.metric("Completed", len(completed))
        
        status_counts = {}
        for s in sheets:
            status_counts[s["status"]] = status_counts.get(s["status"], 0) + 1
        
        fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()), title="Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        recent = sorted(sheets, key=lambda x: x["upload_time"] or "", reverse=True)[:10]
        df = pd.DataFrame([
            {"Sheet ID": r["id"], "Status": r["status"], "Score": r.get("total_score", "N/A"), "Uploaded": r["upload_time"]}
            for r in recent
        ])
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def about_page():
    st.header("ℹ️ About")
    st.markdown("""
    This OMR system lets you upload a sheet image,
    select your answer key set (A or B), and get instant results.
    It uses OpenCV for image processing, ML for ambiguous bubble checks,
    and Streamlit for the web interface.
    """)

if __name__ == "__main__":
    main()
