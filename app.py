import streamlit as st
import google.generativeai as genai
import requests

# 1. SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') 
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

# 3. CONFIG
ASSIGNMENT_NAME = "Email to Liam (End of Year Trip)"
TASK_INSTRUCTIONS = """Write an email to Liam (80-100 words), your exchange partner. Tell him about your end of year trip plans: places to visit, activities, and about your classmates, friends and family."""

SYSTEM_PROMPT = f"""You are a strict but encouraging British English teacher grading at B2 CEFR level.
TASK: {TASK_INSTRUCTIONS}
RUBRIC: Criterion 1 (Adequació), Criterion 2 (Morfosintaxi), Criterion 3 (Lèxic).
OUTPUT: Breakdown per criterion, FINAL MARK: [Total/10], and a closing sentence. NO corrections."""

# 4. UI
st.set_page_config(page_title="Writing Portal", layout="centered")
st.title("📝 Student Writing Portal")

with st.sidebar:
    st.header("Student Info")
    group = st.selectbox("Select Group", ["3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Student 1 Name & Surname")
    student_list = s1 # Keeping it simple for the test

st.info(f"**Task:** {ASSIGNMENT_NAME}\n\n{TASK_INSTRUCTIONS}")

# 5. LOGIC
if not st.session_state.submitted:
    essay = st.text_area("Type your essay here...", height=350, key="draft1")
    if st.button("Submit First Draft"):
        if not s1 or not essay:
            st.error("Please provide your name and essay.")
        else:
            with st.spinner("Grading..."):
                try:
                    response = model.generate_content([SYSTEM_PROMPT, f"FIRST DRAFT: {essay}"])
                    if response and response.text:
                        fb = response.text
                        mark = fb.split("FINAL MARK:")[1].split("\n")[0].strip() if "FINAL MARK:" in fb else "N/A"
                        requests.post(SHEET_URL, json={
                            "type": "FIRST_DRAFT", "group": group, "students": student_list,
                            "assignment": ASSIGNMENT_NAME, "grade": mark, "feedback": fb, "essay": essay
                        })
                        st.session_state.first_feedback = fb
                        st.session_state.original_essay = essay
                        st.session_state.submitted = True
                        st.rerun()
                except Exception as ai_err:
                    st.error(f"Error: {ai_err}")
else:
    st.success("Draft submitted! Improve your text below.")
    with st.expander("View Feedback", expanded=True):
        st.markdown(st.session_state.first_feedback)
    revised = st.text_area("Revised version:", value=st.session_state.original_essay, height=350)
    if st.button("Submit Final Revision"):
        with st.spinner("Reviewing..."):
            try:
                res = model.generate_content([SYSTEM_PROMPT, f"REVISION: {revised}"])
                requests.post(SHEET_URL, json={
                    "type": "REVISION", "group": group, "students": student_list,
                    "feedback": res.text, "essay": revised
                })
                st.markdown(res.text)
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")
