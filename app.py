import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 4. DARK/LIGHT & MOBILE LAYOUT ---
st.set_page_config(
    page_title="Gemini 3.1 PDI Field Assistant",
    layout="wide", # Desktop par bada dikhega
    initial_sidebar_state="expanded", # Mobile par menu hide ho jayega
    page_icon="🔬"
)

# Custom CSS for Mobile Table Scrolling
st.markdown("""
    <style>
    .stTable { overflow-x: auto; }
    [data-testid="stSidebar"] { min-width: 300px; max-width: 300px; }
    </style>
    """, unsafe_content_type=True)

# --- SECURE API CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Settings > Secrets mein check karein.")
    st.stop()

# --- Session State ---
if "gemini_files" not in st.session_state: st.session_state.gemini_files = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- 3. PROFESSIONAL PDF SIDEBAR 📑 ---
with st.sidebar:
    st.title("🔬 PDI Control Center")
    st.info("Tier 1: Gemini 3.1 Pro Active")
    
    # 3. MULTIPLE PDF COMPARISON (Upto 5 Files)
    uploaded_files = st.file_uploader(
        "Upload Multiple Technical PDFs", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    if st.button("Clear All Files"):
        st.session_state.gemini_files = []
        st.rerun()

# --- File Processing Logic ---
if uploaded_files:
    for uploaded_file in uploaded_files:
        # Check if file already uploaded
        if not any(f['name'] == uploaded_file.name for f in st.session_state.gemini_files):
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(uploaded_file.getbuffer())
                    temp_path = temp_file.name
                
                gem_file = genai.upload_file(temp_path)
                while gem_file.state.name == "PROCESSING":
                    time.sleep(2)
                    gem_file = genai.get_file(gem_file.name)
                
                st.session_state.gemini_files.append({"name": uploaded_file.name, "file": gem_file})
                os.remove(temp_path)

# --- MAIN SCREEN ---
st.title("📑 Smart Inspection Dashboard")

if st.session_state.gemini_files:
    tabs = st.tabs(["📊 Technical Analysis", "🆚 Comparison Mode", "💬 Field Q&A"])

    # TAB 1: SINGLE FILE ANALYSIS
    with tabs[0]:
        selected_file = st.selectbox("Select File for Analysis", [f['name'] for f in st.session_state.gemini_files])
        if st.button("Generate Master PDI Table 🚀"):
            model = genai.GenerativeModel("gemini-3.1-pro-preview")
            file_to_analyze = next(f['file'] for f in st.session_state.gemini_files if f['name'] == selected_file)
            
            with st.spinner("Extracting Specs..."):
                prompt = "Create a Markdown table: 1. S.No. 2. English (Spec) 3. Hindi Meaning 4. Inspection Check. Output ONLY the table."
                response = model.generate_content([file_to_analyze, prompt])
                st.markdown(response.text)
                
                # 5. ONE-CLICK REPORT (CSV Download for now)
                st.download_button("📧 Download PDI Report (Excel)", response.text, file_name=f"PDI_{selected_file}.csv")

    # TAB 2: MULTIPLE PDF COMPARISON
    with tabs[1]:
        if len(st.session_state.gemini_files) > 1:
            if st.button("Compare All Vendors/Models 🆚"):
                model = genai.GenerativeModel("gemini-3.1-pro-preview")
                with st.spinner("Comparing documents..."):
                    all_files = [f['file'] for f in st.session_state.gemini_files]
                    compare_prompt = "Compare these medical equipment documents. Create a comparison table highlighting key differences in technical specs, warranty, and price. Answer in Hindi."
                    response = model.generate_content([*all_files, compare_prompt])
                    st.markdown(response.text)
        else:
            st.warning("Comparison ke liye kam se kam 2 PDF upload karein.")

    # TAB 3: SMART Q&A
    with tabs[2]:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        query = st.chat_input("Machine specifications ke bare mein puchein...")
        if query:
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-3-flash-preview") # Fast model for chat
                # Sabhi files ko context mein lena
                all_files = [f['file'] for f in st.session_state.gemini_files]
                response = model.generate_content([*all_files, f"Answer based on these files in Hindi: {query}"])
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
else:
    st.info("⬅️ Left side se PDI report ya technical specification PDF upload karein.")
