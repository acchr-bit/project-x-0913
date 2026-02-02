import streamlit as st
import requests
import json

# 1. SETUP
API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]

# 2. SESSION STATE
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'feedback' not in st.session_state:
    st.session_state.feedback = ""

# 3. UI
st.set_page_config(page_title="Writing Portal", layout="centered")
st.title("📝 Student Writing Portal")

with st.sidebar:
    st.header("Student Info")
    group = st.selectbox("Group", ["3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Student Name")
    student_list = s1

# 4. DIRECT API CALL FUNCTION (Bypasses the library)
def call_gemini_direct(prompt):
    # Trying the most accessible endpoint for 2026
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        # This will tell us the EXACT reason from Google's server
        raise Exception(f"Status {response.status_code}: {response.text}")

# 5. LOGIC
if not st.session_state.submitted:
    essay = st.text_area("Type your essay here...", height=350)
    
    if st.button("Submit for Grade"):
        if not s1 or not essay:
            st.error("Missing name or essay.")
        else:
            with st.spinner("AI Teacher is analyzing..."):
                try:
                    prompt = f"You are a teacher. Grade this B2 English essay and provide feedback. End with 'FINAL MARK: X/10'.\n\nEssay: {essay}"
                    feedback = call_gemini_direct(prompt)
                    
                    # Save and Log
                    st.session_state.feedback = feedback
                    st.session_state.submitted = True
                    
                    requests.post(SHEET_URL, json={
                        "type": "FIRST_DRAFT", "group": group, "students": student_list, "feedback": feedback, "essay": essay
                    })
                    st.rerun()
                except Exception as e:
                    st.error("❌ Google Connection Blocked")
                    st.warning(f"Reason: {e}")
else:
    st.success("Submission successful!")
    st.markdown(st.session_state.feedback)
    if st.button("New Submission"):
        st.session_state.submitted = False
        st.rerun()
