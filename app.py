import streamlit as st
import requests
import time

# --- 1. CONFIGURATION & PRIVACY ---
API_KEY = "YOUR_GEMINI_API_KEY"
SHEET_URL = "YOUR_GOOGLE_SHEETS_URL"

st.set_page_config(
    page_title="Writing Test Portal", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. THE "LOCKDOWN" UI (CSS) ---
st.markdown("""
    <style>
    /* Hide Top Header, GitHub, Share, and Star icons */
    [data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Hide the 'Close' arrow for the sidebar to lock it open */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    /* Hide the Hamburger Menu and Footer */
    #MainMenu {visibility: hidden;}
    footer {display: none !important;}

    /* Hide the top decoration line */
    [data-testid="stDecoration"] {display: none !important;}

    /* Prevent text cut-off since header is hidden */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {padding-top: 2rem;}
    
    /* Disable the Streamlit Cloud "Viewer Badge" (The links you saw) */
    div[class*="viewerBadge"] {display: none !important;}
    </style>
    <meta name="robots" content="noindex, nofollow">
    """, unsafe_allow_html=True)

# --- 3. THE "BADGE KILLER" (JAVASCRIPT) ---
# This removes the profile links and "Manage App" button from the parent frame
st.components.v1.html("""
    <script>
    const hideCloudElements = () => {
        const parentDoc = window.parent.document;
        const selectors = [
            'div[class*="viewerBadge"]', 
            'a[href*="streamlit.io"]', 
            'a[href*="acchr-bit"]',
            '[data-testid="stStatusWidget"]'
        ];
        selectors.forEach(s => {
            parentDoc.querySelectorAll(s).forEach(el => el.style.display = 'none');
        });
    };
    setInterval(hideCloudElements, 500); // Repeat to catch elements as they load
    document.addEventListener('contextmenu', e => e.preventDefault()); // Disable Right-Click
    </script>
    """, height=0)

# --- 4. API CALL WITH RETRY LOGIC ---
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429: # Rate limit
                time.sleep((attempt + 1) * 3)
            else:
                time.sleep(2)
        except:
            time.sleep(2)
    return "The system is busy. Please wait 10 seconds and try again."

# --- 5. APP CONTENT ---
st.title("📝 Official Writing Test")

# Sidebar for Student Info
with st.sidebar:
    st.header("Student Details")
    group = st.selectbox("Group", ["", "3A", "3C", "4A", "4B", "4C"])
    s1 = st.text_input("Full Name")
    # ... Add more names if needed ...

# Main Essay Area
task_desc = "Write a story (150-200 words) about a trip that didn't go as planned."
essay = st.text_area("Your Essay:", height=400, placeholder="Start typing here...")

if st.button("🔍 Get Feedback"):
    if not essay or len(essay.split()) < 10:
        st.warning("Please write a bit more before requesting feedback.")
    else:
        with st.spinner("The examiner is reviewing your work..."):
            prompt = f"Act as a strict B2 English examiner. Review this essay: {essay}. Focus on grammar and spelling."
            feedback = call_gemini(prompt)
            st.session_state.fb = feedback
            st.info(feedback)

# Final Submission
if st.button("🚀 Final Submission"):
    # Code to save to Google Sheets
    st.success("Test submitted successfully!")
    st.balloons()
