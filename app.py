import streamlit as st
import google.generativeai as genai
import requests

# 1. SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]
    genai.configure(api_key=API_KEY)
    # Using 'gemini-1.5-flash' - if this still 404s, we will try 'gemini-pro'
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 2. SESSION STATE INITIALIZATION
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'original_essay' not in st.session_state:
    st.session_state.original_essay = ""
if 'first_feedback' not in st.session_state:
    st.session_state.first_feedback = ""

# 3. CONFIGURATION
ASSIGNMENT_NAME = "Email to Liam (End of Year Trip)"
TASK_INSTRUCTIONS = """Write an email to Liam (80-100 words), your exchange partner. Tell him about your end of year trip plans: places to visit, activities, and about your classmates, friends and family."""

SYSTEM_PROMPT = f"""You are a strict but encouraging British English teacher grading at B2 CEFR level.
TASK: {TASK_INSTRUCTIONS}
Provide feedback based on Adequacy, Morphosyntax, and Lexis. 
You MUST include the text 'FINAL MARK: X/10' at the end."""

# 4. USER INTERFACE
st.set_page_config(page_title="Writing Portal", layout="centered")
st.title("📝 Student Writing Portal")

with st.sidebar:
    st.header("Student Info")
    group = st.selectbox("Select Group", ["3A", "3C", "4A", "4B", "4C"])
    # RESTORING THE 4 STUDENT FIELDS
    s1 = st.text_input("Student 1 Name & Surname")
    s2 = st.text_input("Student 2 (Optional)")
    s3 = st.text_input("Student 3 (Optional)")
    s4 = st.text_input("Student 4 (Optional)")
    
    # Clean up the list to remove empty names
    names = [s.strip() for s in [s1, s2, s3, s4] if s.strip()]
    student_list = ", ".join(names)

st.info(f"**Task:** {ASSIGNMENT_NAME}\n\n{TASK_INSTRUCTIONS}")

# 5. LOGIC FLOW
if not st.session_state.submitted:
    essay = st.text_area("Type your essay here...", height=350, key="draft1")
    
    if st.button("Submit First Draft for Grade"):
        if not s1 or not essay:
            st.error("Please provide at least Name 1 and your essay.")
        else:
            with st.spinner("AI Teacher is marking..."):
                try:
                    response = model.generate_content(f"{SYSTEM_PROMPT}\n\nESSAY:\n{essay}")
                    if response.text:
                        fb = response.text
                        # Extract mark for the spreadsheet
                        mark = fb.split("FINAL MARK:")[1].split("\n")[0].strip() if "FINAL MARK:" in fb else "N/A"
                        
                        # Send to Google Sheets
                        requests.post(SHEET_URL, json={
                            "type": "FIRST_DRAFT", 
                            "group": group, 
                            "students": student_list,
                            "assignment": ASSIGNMENT_NAME, 
                            "grade": mark, 
                            "feedback": fb, 
                            "essay": essay
                        })
                        
                        st.session_state.first_feedback = fb
                        st.session_state.original_essay = essay
                        st.session_state.submitted = True
                        st.rerun()
                except Exception as e:
                    st.error(f"AI Error: {e}")

else:
    # REVISION MODE
    st.success(f"Well done, {s1}! Your first draft is submitted.")
    
    with st.expander("📝 View Your Grade & Feedback", expanded=True):
        st.markdown(st.session_state.first_feedback)
    
    st.divider()
    st.subheader("Final Revision")
    st.write("Use the feedback above to improve your text. When you are happy, submit the final version.")
    
    revised = st.text_area("Write your IMPROVED composition here:", value=st.session_state.original_essay, height=350)
    
    if st.button("Submit Final Revision"):
        with st.spinner("Checking your improvements..."):
            try:
                res = model.generate_content(f"Compare this revision to the original and comment on improvements. No grade.\n\nREVISION:\n{revised}")
                
                # Update the SAME row in Google Sheets
                requests.post(SHEET_URL, json={
                    "type": "REVISION", 
                    "group": group, 
                    "students": student_list,
                    "feedback": res.text, 
                    "essay": revised
                })
                
                st.subheader("Final Feedback")
                st.markdown(res.text)
                st.balloons()
            except Exception as e:
                st.error(f"Revision Error: {e}")
