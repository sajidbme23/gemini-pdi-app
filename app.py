import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import pandas as pd
import io

# --- App Setup ---
st.set_page_config(page_title="Gemini PDI Pro", layout="wide", page_icon="🔬")

# --- SECURE API CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Settings > Secrets check karein.")
    st.stop()

# --- Session State ---
if "gemini_file" not in st.session_state: st.session_state.gemini_file = None
if "report_df" not in st.session_state: st.session_state.report_df = None

# Sidebar
with st.sidebar:
    st.title("🔬 PDI Control")
    uploaded_file = st.file_uploader("Upload Technical PDF", type="pdf")

if uploaded_file:
    if st.session_state.gemini_file is None:
        with st.spinner("Processing PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name
            gem_file = genai.upload_file(temp_path)
            while gem_file.state.name == "PROCESSING":
                time.sleep(2)
                gem_file = genai.get_file(gem_file.name)
            st.session_state.gemini_file = gem_file
            os.remove(temp_path)

# Main Dashboard
st.title("📑 Smart Inspection Dashboard")

if st.session_state.gemini_file:
    if st.button("Generate Master PDI Table 🚀"):
        model = genai.GenerativeModel("gemini-3.1-pro-preview")
        with st.spinner("Analyzing and creating table..."):
            # AI ko CSV format me output dene ke liye bolna taaki table ban sake
            prompt = (
                "Analyze this document. Extract all specifications and provide the output "
                "ONLY as a CSV-formatted string with these columns: "
                "S.No., English (Spec), Hindi Meaning, Inspection Check. "
                "Do not include markdown or extra text."
            )
            response = model.generate_content([st.session_state.gemini_file, prompt])
            
            # AI output ko Table (DataFrame) me badalna
            try:
                csv_data = response.text.replace('```csv', '').replace('```', '').strip()
                st.session_state.report_df = pd.read_csv(io.StringIO(csv_data))
            except:
                st.error("Table format me error aaya. Please try again.")

    if st.session_state.report_df is not None:
        # Screen par Table dikhana
        st.write("### PDI Specification Table")
        st.dataframe(st.session_state.report_df, use_container_width=True)
        
        # --- PDF GENERATION (BROWSWER PRINT METHOD) ---
        st.info("💡 **PDF ke liye:** Table generate hone ke baad PC ya Mobile ke browser menu se 'Print' dabayein aur 'Save as PDF' karein. Isse ye ekdum same table format me save hogi jaisa screen par dikh raha hai.")
        
        # Backup: Excel Download
        csv = st.session_state.report_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Table for Excel", csv, "PDI_Report.csv", "text/csv")
