import streamlit as st
import requests

# 1. SETUP
API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]

# 2. SESSION STATE (To track progress)
if 'submitted_first' not in st.session_state:
    st.session_state.submitted_first = False
if 'fb1' not in st.session_state:
    st.session_state.fb1 = ""
if 'essay1' not in st.session_state:
    st.session_state.essay1 = ""

# 3. AI FUNCTION (Using the stable 2026 endpoint)
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    raise Exception(f"AI Error: {response.text}")

# 4. UI SETUP
st.set_page_config(page_title="Writing Portal", layout="centered")
st.title("📝 Writing Portal: Two-Draft System")

with st.sidebar:
    st.header("Student Info")
    group = st.selectbox("Group", ["3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Student 1")
    s2 = st.text_input("Student 2")
    names = [s.strip() for s in [s1, s2] if s.strip()]
    student_list = ", ".join(names)

task_name = "Email to Liam (Trip Plans)"
st.info(f"**Task:** {task_name}")

# 5. LOGIC: FIRST DRAFT
if not st.session_state.submitted_first:
    draft1 = st.text_area("Write your FIRST DRAFT here:", height=300)
    if st.button("Submit First Draft"):
        if not s1 or not draft1:
            st.error("Please enter a name and your essay.")
        else:
            with st.spinner("Teacher is marking Draft 1..."):
                try:
                    fb1 = call_gemini(f"Grade this B2 essay. Feedback first, then end with 'FINAL MARK: X/10'.\n\n{draft1}")
                    mark = fb1.split("FINAL MARK:")[1].split("\n")[0].strip() if "FINAL MARK:" in fb1 else "N/A"
                    
                    # Send to Sheets (Type: FIRST)
                    requests.post(SHEET_URL, json={
                        "type": "FIRST",
                        "Group": group,
                        "Students": student_list,
                        "Task": task_name,
                        "Mark": mark,
                        "FB1": fb1,
                        "Draft1": draft1
                    })
                    
                    st.session_state.fb1 = fb1
                    st.session_state.essay1 = draft1
                    st.session_state.submitted_first = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# 6. LOGIC: SECOND DRAFT
else:
    st.success("First Draft Submitted!")
    with st.expander("View Teacher Feedback", expanded=True):
        st.markdown(st.session_state.fb1)
    
    final_essay = st.text_area("Write your IMPROVED Final Essay:", value=st.session_state.essay1, height=300)
    
    if st.button("Submit Final Revision"):
        with st.spinner("AI is analyzing your improvements..."):
            try:
                fb2 = call_gemini(f"Review this improved essay based on the previous feedback. Is it better? Provide brief final comments.\n\n{final_essay}")
                
                # Send to Sheets (Type: REVISION)
                requests.post(SHEET_URL, json={
                    "type": "REVISION",
                    "Group": group,
                    "Students": student_list,
                    "Task": task_name,
                    "FinalEssay": final_essay,
                    "FB2": fb2
                })
                
                st.balloons()
                st.subheader("Final Feedback")
                st.markdown(fb2)
                if st.button("Start New Assignment"):
                    st.session_state.submitted_first = False
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
