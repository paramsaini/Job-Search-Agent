import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="Blog - Job-Search-Agent", page_icon="📝", layout="wide")

# --- NEW ORANGE + GOLD NEON UI STYLING (HIDE SIDEBAR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0a0a0f !important;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* HIDE SIDEBAR */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* HIDE SIDEBAR BUTTON */
    button[kind="header"] {
        display: none !important;
    }
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Card styles */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"] {
        background: rgba(255, 107, 53, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 107, 53, 0.15) !important;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    
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
    
    div[data-testid="stMetricValue"] { 
        color: #ff6b35 !important; 
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
        font-weight: 700;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 107, 53, 0.08) !important;
        color: white !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
        border-radius: 10px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 35px rgba(255, 107, 53, 0.6);
        transform: translateY(-2px);
    }
    
    .stSelectbox>div>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    hr {
        border-color: rgba(255, 107, 53, 0.2) !important;
    }
    
    .stSlider>div>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    /* Back button style */
    .back-btn {
        background: rgba(255, 107, 53, 0.1);
        border: 1px solid rgba(255, 107, 53, 0.3);
        border-radius: 10px;
        padding: 10px 20px;
        color: #ff6b35;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .back-btn:hover {
        background: rgba(255, 107, 53, 0.2);
        box-shadow: 0 0 15px rgba(255, 107, 53, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Page Render ---

def blog_page():
    # Back to Main Page
    if st.button("← Back to Main Page"):
        st.session_state.current_page = "Main Page"
        st.switch_page("Main_Page.py")
    
    # Main Logo
    st.markdown("""
    <div style="text-align: center; margin: 10px 0;">
        <h1 style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; font-style: italic; margin: 0;">
            🚀 Job-Search-Agent
        </h1>
        <p style="color: #888; margin: 5px 0 0 0; font-size: 0.9rem;">AI-Powered Career Guidance</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Custom styled header
    st.markdown("""
    <h1 style="text-align: center; font-size: 2.5rem;">
        📝 Career Blog
    </h1>
    """, unsafe_allow_html=True)
    st.caption("Career tips, industry insights, and job search strategies")
    st.markdown("---")

    # --- Blog Post 1 ---
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

    # --- Blog Post 2 ---
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

    # --- Blog Post 3 ---
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

blog_page()
