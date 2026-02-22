import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- App Setup ---
st.set_page_config(page_title="Gemini 3.1 PDI Pro", layout="wide", page_icon="🔬")

st.title("🔬 Gemini 3.1 Advanced PDI Explainer")
st.write("Using Latest Gemini 3.1 Pro Preview (Tier 1)")

# --- SECURE API CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Streamlit Secrets check karein.")
    st.stop()

# --- Session State ---
if "gemini_file" not in st.session_state: st.session_state.gemini_file = None
if "current_file" not in st.session_state: st.session_state.current_file = ""

# Sidebar for Upload
with st.sidebar:
    st.header("📂 Upload Zone")
    uploaded_file = st.file_uploader("Technical PDF Upload Karein", type="pdf")

if uploaded_file:
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.gemini_file = None
        st.session_state.current_file = uploaded_file.name

    if st.session_state.gemini_file is None:
        with st.spinner("Processing with Gemini 3.1..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name
            
            uploaded_gemini_file = genai.upload_file(temp_path)
            
            # File Active hone ka wait karein
            while uploaded_gemini_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_gemini_file = genai.get_file(uploaded_gemini_file.name)
            
            st.session_state.gemini_file = uploaded_gemini_file
            os.remove(temp_path)
            st.sidebar.success("✅ File Ready!")

    if st.button("Deep Technical Analysis 🚀"):
        # YAHAN UPDATE: Latest Gemini 3.1 Pro Preview
        model = genai.GenerativeModel("gemini-3.1-pro-preview")
        
        with st.spinner("Analyzing with Gemini 3.1 Pro..."):
            try:
                prompt = (
                    "You are a Senior Biomedical Engineer. Create a Markdown table: "
                    "1. S.No. 2. English (Spec) 3. Hindi Meaning 4. Inspection Check. "
                    "Output ONLY the table."
                )
                response = model.generate_content([st.session_state.gemini_file, prompt])
                st.markdown("### 📋 Master Inspection Table")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Analysis Error: {e}")
