import streamlit as st

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Blog - Job-Search-Agent", page_icon="🚀", layout="wide")

# --- SAME STYLING AS MAIN APP ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0a0a0f !important;
        background-attachment: fixed;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* HIDE DEFAULT SIDEBAR */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Typography */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    h1 {
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    p, label, .stMarkdown { color: #e2e8f0 !important; }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 35px rgba(255, 107, 53, 0.6);
        transform: translateY(-2px);
    }
    
    /* Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 107, 53, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 107, 53, 0.15) !important;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CHECK AUTH (Redirect if not logged in) ---
if 'user' not in st.session_state or not st.session_state.user:
    st.warning("Please login to access this page.")
    st.stop()

# --- HEADER ---
st.markdown("""
<div style="text-align: center; margin: 20px 0 30px 0;">
    <h1 style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-style: italic; margin: 0;">
        🚀 Job-Search-Agent
    </h1>
    <p style="color: #888; margin: 5px 0 0 0;">AI-Powered Career Guidance</p>
</div>
""", unsafe_allow_html=True)

# --- BACK BUTTON ---
if st.button("← Back to Dashboard", type="secondary"):
    st.switch_page("Main_Page.py")

st.markdown("---")

# --- BLOG CONTENT ---
st.title("📝 Blog")
st.caption("Career tips, industry insights, and job search strategies")

# Sample blog posts (you can replace with dynamic content later)
st.markdown("---")

# Blog Post 1
with st.container():
    st.subheader("🎯 5 Tips for Optimizing Your CV for ATS Systems")
    st.caption("January 2026 • 5 min read")
    st.write("""
    Applicant Tracking Systems (ATS) are used by most companies to filter resumes. 
    Here's how to ensure your CV makes it through...
    """)
    if st.button("Read More", key="blog1"):
        st.info("Full article coming soon!")

st.markdown("---")

# Blog Post 2
with st.container():
    st.subheader("💼 How to Prepare for Behavioral Interviews")
    st.caption("January 2026 • 7 min read")
    st.write("""
    Behavioral interviews focus on how you've handled situations in the past. 
    Use the STAR method to structure your answers...
    """)
    if st.button("Read More", key="blog2"):
        st.info("Full article coming soon!")

st.markdown("---")

# Blog Post 3
with st.container():
    st.subheader("📈 Career Transition: Moving from Technical to Management Roles")
    st.caption("December 2025 • 10 min read")
    st.write("""
    Thinking about moving into management? Here's what you need to know about 
    making the transition successfully...
    """)
    if st.button("Read More", key="blog3"):
        st.info("Full article coming soon!")

st.markdown("---")

st.info("💡 More blog posts coming soon! Check back regularly for career tips and insights.")
