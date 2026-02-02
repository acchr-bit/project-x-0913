import streamlit as st
import requests
import re

# 1. DATABASE & API SETUP
API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]

# 2. SESSION STATE (Ensures data persists during the session)
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""
if 'essay_at_draft1' not in st.session_state:
    st.session_state.essay_at_draft1 = ""
if 'fb1' not in st.session_state:
    st.session_state.fb1 = ""
if 'fb2' not in st.session_state:
    st.session_state.fb2 = ""
if 'submitted_first' not in st.session_state:
    st.session_state.submitted_first = False

# 3. AI CONNECTION
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Error: {e}"

# 4. USER INTERFACE
st.set_page_config(page_title="B2 Writing Portal", layout="centered")
st.title("📝 B2 English Writing Portal")

# Sidebar for names and group
with st.sidebar:
    st.header("Student Information")
    group = st.selectbox("Group", ["3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Student 1 Name and Surname")
    s2 = st.text_input("Student 2 Name and Surname (Optional)")
    s3 = st.text_input("Student 3 Name and Surname (Optional)")
    s4 = st.text_input("Student 4 Name and Surname (Optional)")
    
    names = [s.strip() for s in [s1, s2, s3, s4] if s.strip()]
    student_list = ", ".join(names)

task_name = "Email to Liam (End of Year Trip)"
st.info(f"**Current Task:** {task_name}")

# The main text area for the essay
essay = st.text_area(
    "Type your essay here. You can edit this text after getting feedback.", 
    value=st.session_state.essay_content, 
    height=400
)
st.session_state.essay_content = essay

# Two columns for buttons
col1, col2 = st.columns(2)

# --- STEP 1: SUBMIT FIRST DRAFT ---
with col1:
    if st.button("🔍 Get Initial Feedback"):
        if not s1 or not essay:
            st.error("Please provide at least one name and write an essay.")
        else:
            with st.spinner("Teacher is checking your draft..."):
                try:
                    # Prompt designed to hide the mark from the student text
                    prompt = (
                        f"You are a British English teacher. Task: {task_name}. "
                        f"Review this B2 essay. Provide diagnostic feedback on grammar, vocabulary, and organization. "
                        f"Do not tell the student their mark in your main text. "
                        f"At the very end of your response, write 'SECRET MARK: X/10'."
                    )
                    fb_raw = call_gemini(f"{prompt}\n\nEssay: {essay}")
                    
                    # Regex to find the mark and clean the feedback
                    mark_search = re.search(r"SECRET MARK:\s*(\d+/\d+)", fb_raw)
                    mark_value = mark_search.group(1) if mark_search else "N/A"
                    fb_clean = re.sub(r"SECRET MARK:.*", "", fb_raw).strip()
                    
                    # Save to Session State
                    st.session_state.fb1 = fb_clean
                    st.session_state.essay_at_draft1 = essay
                    st.session_state.submitted_first = True
                    
                    # SEND TO GOOGLE SHEETS (Spaced names to match your headers)
                    requests.post(SHEET_URL, json={
                        "type": "FIRST",
                        "Group": group,
                        "Students": student_list,
                        "Task": task_name,
                        "Mark": mark_value,
                        "FB 1": fb_clean,
                        "Draft 1": essay
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing draft: {e}")

# --- DISPLAY FEEDBACK 1 ---
if st.session_state.fb1:
    st.markdown("---")
    st.subheader("💡 Teacher Feedback (Draft 1)")
    st.info(st.session_state.fb1)
    st.caption("☝️ Edit your essay in the box above to improve it, then click below.")

    # --- STEP 2: SUBMIT FINAL VERSION ---
    with col2:
        if st.button("🚀 Submit FINAL Version"):
            with st.spinner("Analyzing improvements..."):
                try:
                    context_prompt = (
                        f"Compare this student's REVISED VERSION with their ORIGINAL DRAFT. "
                        f"ORIGINAL: {st.session_state.essay_at_draft1}\n\n"
                        f"REVISED VERSION: {essay}\n\n"
                        f"Briefly state if they improved and provide a final encouraging comment with a mark."
                    )
                    fb2 = call_gemini(context_prompt)
                    st.session_state.fb2 = fb2
                    
                    # UPDATE GOOGLE SHEET (Using spaced names to match headers)
                    requests.post(SHEET_URL, json={
                        "type": "REVISION",
                        "Group": group,
                        "Students": student_list,
                        "Final Essay": essay,
                        "FB 2": fb2
                    })
                    st.balloons()
                except Exception as e:
                    st.error(f"Error processing final: {e}")

# --- DISPLAY FEEDBACK 2 ---
if st.session_state.fb2:
    st.subheader("✅ Final Teacher Comments")
    st.success(st.session_state.fb2)
