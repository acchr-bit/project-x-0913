import streamlit as st
import google.generativeai as genai
import requests

# 1. SETUP WITH AUTOMATIC MODEL DISCOVERY
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]
    genai.configure(api_key=API_KEY)
    
    # List of models to try in order of preference
    model_options = [
        'gemini-1.5-flash', 
        'gemini-2.0-flash-exp', 
        'gemini-1.5-pro', 
        'gemini-pro'
    ]
    
    model = None
    for m_name in model_options:
        try:
            test_model = genai.GenerativeModel(m_name)
            # Try a tiny 1-token generation to verify access
            test_model.generate_content("ok", generation_config={"max_output_tokens": 1})
            model = test_model
            break # If it works, stop looking!
        except Exception:
            continue
            
    if model is None:
        st.error("Connection Error: Your API key is active, but Google isn't granting access to the models. Check your 'Quotas' in Google Cloud Console.")
        st.stop()
        
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 2. SESSION STATE
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'original_essay' not in st.session_state:
    st.session_state.original_essay = ""
if 'first_feedback' not in st.session_state:
    st.session_state.first_feedback = ""

# 3. UI & LOGIC (The rest remains the same)
st.set_page_config(page_title="Writing Portal", layout="centered")
st.title("📝 Student Writing Portal")

with st.sidebar:
    st.header("Student Info")
    group = st.selectbox("Select Group", ["3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Student 1 Name")
    s2 = st.text_input("Student 2 (Optional)")
    s3 = st.text_input("Student 3 (Optional)")
    s4 = st.text_input("Student 4 (Optional)")
    student_list = ", ".join(filter(None, [s1, s2, s3, s4]))

# Instructions
TASK_INSTR = "Write an email to Liam (80-100 words) about your trip plans."
st.info(f"**Task:** {TASK_INSTR}")

if not st.session_state.submitted:
    essay = st.text_area("Type your essay here...", height=350)
    if st.button("Submit First Draft"):
        if not s1 or not essay:
            st.error("Please provide a name and essay.")
        else:
            with st.spinner("Grading..."):
                try:
                    response = model.generate_content(f"Grade this B2 essay: {essay}")
                    st.session_state.first_feedback = response.text
                    st.session_state.original_essay = essay
                    st.session_state.submitted = True
                    # Log to Sheets
                    requests.post(SHEET_URL, json={
                        "type": "FIRST_DRAFT", "group": group, "students": student_list, "essay": essay
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"AI Error: {e}")
else:
    st.success("Submitted!")
    st.markdown(st.session_state.first_feedback)
    if st.button("New Submission"):
        st.session_state.submitted = False
        st.rerun()
