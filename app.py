# --- SUBMISSION LOGIC ---

if not st.session_state.submitted:
    if st.button("Submit First Draft for Grade"):
        if not s1 or not essay:
            st.error("Please provide your name and essay.")
        else:
            with st.spinner("Analyzing First Draft..."):
                response = model.generate_content([SYSTEM_PROMPT, essay])
                feedback_text = response.text
                mark = feedback_text.split("FINAL MARK:")[1].split("\n")[0].strip() if "FINAL MARK:" in feedback_text else "N/A"

                # Send First Draft
                requests.post(SHEET_URL, json={
                    "type": "FIRST_DRAFT",
                    "group": group, "students": students, "assignment": ASSIGNMENT_NAME,
                    "grade": mark, "feedback": feedback_text, "essay": essay
                })
                
                st.subheader("Draft 1 Feedback")
                st.markdown(feedback_text)
                st.session_state.submitted = True

else:
    st.warning("Revision Mode: Improve your text below.")
    revised_essay = st.text_area("Write your IMPROVED composition here:", value=essay, height=300)
    
    if st.button("Submit Final Revision"):
        with st.spinner("Reviewing Improvements..."):
            rev_prompt = f"{SYSTEM_PROMPT}\n\nSUBMISSION: FINAL REVISION. Compare with original. Feedback on improvements only. No grade."
            response = model.generate_content([rev_prompt, revised_essay])
            
            # Update the SAME row in Google Sheets
            requests.post(SHEET_URL, json={
                "type": "REVISION",
                "group": group, 
                "students": students, 
                "feedback": response.text, 
                "essay": revised_essay 
            })
            
            st.subheader("Final Feedback")
            st.markdown(response.text)
            st.balloons()