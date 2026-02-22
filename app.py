import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 4. DARK/LIGHT & MOBILE LAYOUT ---
st.set_page_config(
    page_title="Gemini 3.1 PDI Field Assistant",
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="🔬"
)

# Custom CSS for Mobile Table Scrolling (Fixed the error here)
st.markdown("""
    <style>
    .stTable { overflow-x: auto; }
    [data-testid="stSidebar"] { min-width: 300px; max-width: 300px; }
    /* Mobile optimization */
    @media (max-width: 640px) {
        .main .block-container { padding: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True) # <-- Corrected from unsafe_content_type

# --- SECURE API CONFIGURATION ---
try:
    # Streamlit Cloud Secrets se key uthayega
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Settings > Secrets mein GEMINI_API_KEY set karein.")
    st.stop()

# --- Session State ---
if "gemini_files" not in st.session_state: st.session_state.gemini_files = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- 3. PROFESSIONAL PDF SIDEBAR 📑 ---
with st.sidebar:
    st.title("🔬 PDI Control Center")
    st.info("Tier 1: Gemini 3.1 Pro Active")
    
    # MULTIPLE PDF UPLOAD (Upto 100MB per file supported now)
    uploaded_files = st.file_uploader(
        "Upload Technical PDFs", 
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
                
                try:
                    gem_file = genai.upload_file(temp_path)
                    # File Active hone ka wait karein
                    while gem_file.state.name == "PROCESSING":
                        time.sleep(2)
                        gem_file = genai.get_file(gem_file.name)
                    
                    st.session_state.gemini_files.append({"name": uploaded_file.name, "file": gem_file})
                    os.remove(temp_path)
                except Exception as e:
                    st.error(f"Error uploading {uploaded_file.name}: {e}")

# --- MAIN SCREEN ---
st.title("📑 Smart Inspection Dashboard")

if st.session_state.gemini_files:
    # Desktop par Tabs mobile par achhe dikhte hain
    tabs = st.tabs(["📊 Analysis", "🆚 Comparison", "💬 Field Q&A"])

    # TAB 1: MASTER PDI TABLE (Gemini 3.1 Pro)
    with tabs[0]:
        selected_file_name = st.selectbox("Select File", [f['name'] for f in st.session_state.gemini_files])
        if st.button("Generate Master PDI Table 🚀"):
            model = genai.GenerativeModel("gemini-3.1-pro-preview")
            file_to_analyze = next(f['file'] for f in st.session_state.gemini_files if f['name'] == selected_file_name)
            
            with st.spinner("Extracting Specifications..."):
                prompt = (
                    "You are a Senior Biomedical Engineer. Create a Markdown table: "
                    "1. S.No. 2. English (Spec) 3. Hindi Meaning 4. Inspection Check. "
                    "Output ONLY the table."
                )
                response = model.generate_content([file_to_analyze, prompt])
                st.markdown("### 📋 Master Inspection Table")
                st.markdown(response.text)
                
                # 5. ONE-CLICK DOWNLOAD (CSV format)
                st.download_button(
                    "📥 Download for Excel", 
                    response.text, 
                    file_name=f"PDI_{selected_file_name}.csv"
                )

    # TAB 2: MULTIPLE PDF COMPARISON
    with tabs[1]:
        if len(st.session_state.gemini_files) > 1:
            st.write(f"Comparing {len(st.session_state.gemini_files)} documents...")
            if st.button("Start Comparison 🆚"):
                model = genai.GenerativeModel("gemini-3.1-pro-preview")
                with st.spinner("Analyzing differences..."):
                    all_gem_files = [f['file'] for f in st.session_state.gemini_files]
                    compare_prompt = "Compare these medical equipment documents in a detailed table. Highlight technical differences, warranty, and compliance. Answer in Hindi."
                    response = model.generate_content([*all_gem_files, compare_prompt])
                    st.markdown(response.text)
        else:
            st.warning("Comparison ke liye kam se kam 2 PDF upload karein.")

    # TAB 3: SMART FIELD Q&A
    with tabs[2]:
        st.info("Field par sawal puchein (Mobile voice typing use kar sakte hain)")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        query = st.chat_input("Machine ya report ke baare mein puchein...")
        if query:
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            
            with st.chat_message("assistant"):
                # Chat ke liye fast model
                model = genai.GenerativeModel("gemini-3-flash-preview")
                all_gem_files = [f['file'] for f in st.session_state.gemini_files]
                response = model.generate_content([*all_gem_files, f"Answer in simple Hindi: {query}"])
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
else:
    st.info("⬅️ Left side se PDI report ya technical specification PDF upload karein.")
