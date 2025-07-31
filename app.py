import streamlit as st
from profile_builder import extract_marks_from_pdf, extract_interests_from_certificates, build_student_profile
from course_matcher import load_courses, get_recommendation

import tempfile
import os

st.set_page_config(page_title="🎓 AI Course Advisor", layout="centered")

st.title("🎓 AI Course Advisor")
st.write("Upload your details and chat with an academic AI agent to explore the best-fit university courses.")

# Store chat messages (session-limited)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# If profile not built yet, ask for input
if "profile" not in st.session_state:
    marksheet = st.file_uploader("📄 Upload your marksheet (PDF)", type=["pdf"])
    certificates = st.file_uploader("🏅 Upload any certificates (optional)", type=["pdf"], accept_multiple_files=True)

    st.header("🧠 Tell us more about you")
    q1 = st.text_input("1️⃣ What career or profession do you see yourself in 5–10 years from now?")
    q2 = st.multiselect(
        "2️⃣ Do you enjoy working with:",
        ["People", "Machines or Code", "Creative Tools", "Numbers and Data"]
    )
    q3 = st.text_input("3️⃣ What subjects do you enjoy learning the most and why?")
    q4 = st.text_area("4️⃣ Have you participated in any clubs, projects, or competitions?")

    if st.button("🔍 Build My Profile & Start Chat"):
        if not marksheet or not q1 or not q3:
            st.warning("Please upload your marksheet and answer at least questions 1 and 3.")
        else:
            with st.spinner("Analyzing your profile..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_marks:
                    tmp_marks.write(marksheet.read())
                    marks_path = tmp_marks.name

                cert_paths = []
                for cert in certificates:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_cert:
                        tmp_cert.write(cert.read())
                        cert_paths.append(tmp_cert.name)

                marks = extract_marks_from_pdf(marks_path)
                interests = extract_interests_from_certificates(cert_paths) if cert_paths else []

                profile = build_student_profile(marks, interests, q1, q2, q3, q4)
                st.session_state.profile = profile
                st.session_state.courses = load_courses()

                response = get_recommendation(profile, st.session_state.courses)
                st.session_state.messages.append({"role": "assistant", "content": response})

                os.unlink(marks_path)
                for path in cert_paths:
                    os.unlink(path)

                st.rerun()

# Chat UI (after profile is built)
else:
    prompt = st.chat_input("Ask me anything about the courses suggested or your academic future!")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Use profile + chat history to generate better response
                full_prompt = f"Student Profile:\n{st.session_state.profile}\n\nConversation:\n"
                for msg in st.session_state.messages:
                    full_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
                full_prompt += f"User: {prompt}\nAdvisor:"

                response = get_recommendation(st.session_state.profile, st.session_state.courses)
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
