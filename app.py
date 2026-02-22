import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 4. 🌙 DARK/LIGHT & MOBILE LAYOUT ---
st.set_page_config(
    page_title="Gemini PDI Field Assistant",
    layout="wide", 
    initial_sidebar_state="auto", 
    page_icon="🔬"
)

# Sidebar aur Mobile Table ke liye custom CSS
st.markdown("""
    <style>
    /* Mobile par table ko scrollable banane ke liye */
    .stTable { overflow-x: auto !important; }
    
    /* Sidebar ki width set karne ke liye */
    [data-testid="stSidebar"] { min-width: 280px; max-width: 320px; }
    
    /* Mobile padding adjustment */
    @media (max-width: 640px) {
        .main .block-container { padding: 1rem; }
        .stButton>button { width: 100%; } /* Mobile par buttons full width */
    }
    </style>
    """, unsafe_allow_html=True)

# --- SECURE API CONFIGURATION ---
try:
    # Streamlit Secrets se key uthayega (Hiding Process)
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Settings > Secrets mein GEMINI_API_KEY set karein.")
    st.stop()

# --- Session State Management ---
if "gemini_file" not in st.session_state: st.session_state.gemini_file = None
if "current_filename" not in st.session_state: st.session_state.current_filename = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- 3. PROFESSIONAL PDF SIDEBAR 📑 ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-doctor.png", width=80)
    st.title("PDI Control Center")
    st.markdown("---")
    
    st.subheader("📁 Document Upload")
    uploaded_file = st.file_uploader("Upload Technical PDF", type="pdf")
    
    if uploaded_file:
        st.success(f"Selected: {uploaded_file.name}")
        
    st.markdown("---")
    st.info("💡 **Tip:** Mobile par voice typing use karke sawal puchein.")
    
    if st.button("Clear App Data"):
        st.session_state.gemini_file = None
        st.session_state.chat_history = []
        st.rerun()

# --- File Processing Logic ---
if uploaded_file:
    # Nayi file check
    if st.session_state.current_filename != uploaded_file.name:
        st.session_state.gemini_file = None
        st.session_state.current_filename = uploaded_file.name
        st.session_state.chat_history = []

    if st.session_state.gemini_file is None:
        with st.spinner("Processing PDF for Field Use..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name
            
            try:
                # Gemini 3.1 Pro (Tier 1) use kar rahe hain
                gem_file = genai.upload_file(temp_path)
                
                # File Active hone ka wait (Critical for 404/NotFound errors)
                while gem_file.state.name == "PROCESSING":
                    time.sleep(2)
                    gem_file = genai.get_file(gem_file.name)
                
                st.session_state.gemini_file = gem_file
                os.remove(temp_path)
                st.sidebar.success("✅ Analysis Ready!")
            except Exception as e:
                st.error(f"Upload Error: {e}")

# --- MAIN DASHBOARD ---
st.title("📑 Smart Inspection Dashboard")

if st.session_state.gemini_file:
    # 5. ONE-CLICK PDI REPORT & Q&A Tabs
    tab1, tab2 = st.tabs(["📊 Technical Analysis", "💬 Field Assistant (Q&A)"])

    with tab1:
        st.subheader("Master PDI Specification Table")
        if st.button("Generate Full Analysis Report 🚀"):
            model = genai.GenerativeModel("gemini-3.1-pro-preview")
            
            with st.spinner("Extracting Specifications..."):
                prompt = (
                    "You are a Senior Biomedical Engineer. Create a detailed Markdown table: "
                    "1. S.No. (exact) 2. English (Spec) 3. Hindi Meaning 4. Inspection Check. "
                    "Output ONLY the table."
                )
                response = model.generate_content([st.session_state.gemini_file, prompt])
                report_data = response.text
                st.markdown(report_data)
                
                # 5. ONE-CLICK DOWNLOAD (Email/Excel ready)
                st.download_button(
                    label="📧 Download PDI Report (Excel/CSV)",
                    data=report_data,
                    file_name=f"PDI_Report_{st.session_state.current_filename}.csv",
                    mime="text/csv"
                )

    with tab2:
        st.subheader("💬 Smart Q&A Assistant")
        # Chat history display
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat Input
        query = st.chat_input("Ask anything about the document...")
        if query:
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            
            with st.chat_message("assistant"):
                with st.spinner("Searching..."):
                    # Chat ke liye Flash model fast hai
                    model = genai.GenerativeModel("gemini-3-flash-preview")
                    response = model.generate_content([st.session_state.gemini_file, f"Answer in simple Hindi: {query}"])
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
else:
    st.info("⬅️ PDI Manual ya Technical Specification PDF upload karke shuru karein.")
