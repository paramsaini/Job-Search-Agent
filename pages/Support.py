import streamlit as st
import os
from supabase import create_client

st.set_page_config(page_title="Support", page_icon="💬", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom right, #0f172a, #1e1b4b); color: #e2e8f0; }
    .support-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(88, 116, 176, 0.3); border-radius: 12px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

# BACK BUTTON
if st.button("← Back to Main Page"):
    st.switch_page("Main_Page.py")

# CONSISTENT HEADER
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF8C00; margin-bottom: 0;">🚀 Job-Search-Agent</h1>
    <p style="color: #e2e8f0; font-size: 1.2rem; margin-top: 5px;">AI-Powered Career Guidance</p>
    <hr style="border-color: rgba(255, 140, 0, 0.3);">
</div>
""", unsafe_allow_html=True)

st.title("💬 Support Center")
col1, col2 = st.columns(2)
with col1:
    st.subheader("📧 Contact Us")
    st.markdown('<div class="support-card"><p>📩 jobsearchagent26@gmail.com</p></div>', unsafe_allow_html=True)

st.subheader("❓ FAQ")
with st.expander("How do I delete my account?"):
    st.write("Go to Settings > Delete Account and type DELETE.")
with st.expander("How does the Simulator work?"):
    st.write("Enter a role, get a question, record answer, get AI feedback.")

st.subheader("📝 Send Feedback")
with st.form("feedback"):
    msg = st.text_area("Message")
    if st.form_submit_button("Submit"):
        st.success("Sent!")
