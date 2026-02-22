import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- App Setup ---
st.set_page_config(page_title="Gemini PDI Pro Assistant", layout="wide", page_icon="🔬")

st.title("🔬 Gemini Advanced PDI Explainer (Tier 1)")
st.write("Professional Biomedical Inspection Tool - Powered by Gemini 1.5 Pro")

# --- SECURE API CONFIGURATION (Hide Process) ---
try:
    # Hum API key ko st.secrets se uthayenge, code mein nahi likhenge
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("❌ API Key nahi mili! Streamlit Settings mein 'Secrets' check karein.")
    st.stop()

# --- Session State ---
if "gemini_file" not in st.session_state: st.session_state.gemini_file = None
if "current_file" not in st.session_state: st.session_state.current_file = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# Sidebar for Upload
with st.sidebar:
    st.header("📂 Upload Zone")
    uploaded_file = st.file_uploader("Technical PDF Upload Karein", type="pdf")

if uploaded_file:
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.gemini_file = None
        st.session_state.current_file = uploaded_file.name
        st.session_state.chat_history = []

    if st.session_state.gemini_file is None:
        with st.spinner("PDF process ho rahi hai..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name
            
            # File upload
            uploaded_gemini_file = genai.upload_file(temp_path)
            
            # File Active hone ka wait karein (Wait Logic)
            while uploaded_gemini_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_gemini_file = genai.get_file(uploaded_gemini_file.name)
            
            st.session_state.gemini_file = uploaded_gemini_file
            os.remove(temp_path)
            st.sidebar.success(f"✅ {uploaded_file.name} ready hai!")

    # --- Analysis Section ---
    if st.button("Deep Technical Analysis 🚀"):
        # Yahan hum stable model version use kar rahe hain
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        with st.spinner("Specifications extract ho rahi hain..."):
            try:
                prompt = (
                    "You are a Senior Biomedical Engineer. Analyze this document. Create a Markdown table: "
                    "1. S.No. 2. English (Spec) 3. Hindi Meaning 4. Inspection Check. "
                    "Output only the table."
                )
                response = model.generate_content([st.session_state.gemini_file, prompt])
                st.markdown("### 📋 Master Inspection Table")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Analysis Error: {e}")

    # --- Chat Section ---
    st.divider()
    st.header("💬 Smart Q&A")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    query = st.chat_input("PDF ke baare mein sawal puchein...")
    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        
        with st.chat_message("assistant"):
            try:
                flash_model = genai.GenerativeModel("gemini-1.5-flash")
                response = flash_model.generate_content([st.session_state.gemini_file, f"Answer in Hindi: {query}"])
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Chat Error: {e}")
