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
    
    /* Blog post styling */
    .blog-post {
        background: rgba(255, 107, 53, 0.03);
        border: 1px solid rgba(255, 107, 53, 0.1);
        border-radius: 16px;
        padding: 30px;
        margin: 20px 0;
    }
    
    .blog-meta {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    .blog-content {
        line-height: 1.8;
        font-size: 1.1rem;
    }
    
    .blog-content h2 {
        margin-top: 30px;
        margin-bottom: 15px;
    }
    
    .highlight-box {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(247, 197, 49, 0.1));
        border-left: 4px solid #ff6b35;
        padding: 20px;
        margin: 20px 0;
        border-radius: 0 12px 12px 0;
    }
    
    .stat-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #10B981;
    }
    
    .cta-box {
        background: linear-gradient(135deg, #ff6b35, #f7c531);
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin: 30px 0;
    }
    
    .cta-box h3, .cta-box p {
        color: #000 !important;
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
    
    # Blog Header
    st.markdown("""
    <h1 style="text-align: center; font-size: 2.5rem;">
        📝 Career Blog
    </h1>
    """, unsafe_allow_html=True)
    st.caption("Expert career tips, industry insights, and AI-powered job search strategies")
    st.markdown("---")
    
    # Blog Navigation
    blog_selection = st.selectbox(
        "Select Article",
        [
            "📌 Featured: Complete Guide to AI-Powered Job Searching in 2026",
            "🎯 5 Tips for Optimizing Your CV for ATS Systems",
            "💼 How to Prepare for Behavioral Interviews",
            "📈 Career Transition: Technical to Management Roles"
        ]
    )
    
    st.markdown("---")
    
    if "Complete Guide to AI-Powered Job Searching" in blog_selection:
        render_featured_article()
    elif "ATS Systems" in blog_selection:
        render_ats_article()
    elif "Behavioral Interviews" in blog_selection:
        render_interview_article()
    else:
        render_career_transition_article()


def render_featured_article():
    """Main featured SEO-optimized article"""
    
    # Article Header
    st.markdown("""
    <div class="blog-post">
        <h1 style="font-size: 2.2rem; margin-bottom: 10px;">The Complete Guide to AI-Powered Job Searching in 2026: Strategies That Actually Work</h1>
        <div class="blog-meta">
            📅 February 2026 • ⏱️ 12 min read • 👤 By Job-Search-Agent Team
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Statistics
    st.markdown("### 📊 The 2026 Job Market Reality")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">73%</div>
            <p>of companies use ATS to filter resumes</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">41%</div>
            <p>of tech jobs now require AI skills</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">85%</div>
            <p>of employers use skills assessments</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Introduction
    st.markdown("""
    ### Introduction: Why Traditional Job Searching No Longer Works
    
    The job market in 2026 has fundamentally changed. According to recent data from Indeed's Hiring Lab, 
    we're in a "low-hire, low-fire" environment where competition for available positions is fiercer than ever. 
    The days of simply submitting your resume and hoping for the best are over.
    
    Today's hiring process is dominated by Applicant Tracking Systems (ATS), AI-powered screening tools, 
    and recruiters who spend an average of just 6-7 seconds scanning each profile. If your job search 
    strategy hasn't evolved, you're likely missing out on opportunities you're perfectly qualified for.
    
    This comprehensive guide will show you exactly how to leverage AI tools and modern strategies to 
    stand out in 2026's competitive job market.
    """)
    
    st.markdown("""
    <div class="highlight-box">
        <strong>💡 Key Insight:</strong> Jobs that mention AI in their postings are growing while overall 
        hiring remains flat. Developing AI skills isn't just beneficial—it's becoming essential for 
        career advancement in 2026.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Section 1
    st.markdown("""
    ### 1. Understanding How Modern Hiring Actually Works
    
    Before diving into strategies, you need to understand the hiring pipeline you're navigating:
    
    **Stage 1: ATS Screening**
    
    Your resume first encounters an Applicant Tracking System. These systems scan for keywords, 
    qualifications, and formatting. Around 73% of organizations use an ATS as a core part of their 
    recruiting process. If your resume doesn't pass this digital gatekeeper, no human will ever see it.
    
    **Stage 2: AI-Assisted Evaluation**
    
    Many companies now use AI tools to rank candidates based on skills matching, experience relevance, 
    and even predict job performance. These systems analyze your resume against successful employees' 
    profiles and industry benchmarks.
    
    **Stage 3: Human Review**
    
    Only after passing automated screening do recruiters review your application—and they typically 
    spend less than 10 seconds making an initial decision.
    
    **Stage 4: Skills Assessment**
    
    According to TestGorilla, 85% of employers now use skills assessments, believing they're more 
    accurate predictors of job performance than resumes alone.
    """)
    
    st.markdown("---")
    
    # Section 2
    st.markdown("""
    ### 2. Optimizing Your Resume for ATS and Human Readers
    
    Your resume needs to satisfy two very different audiences: algorithms and humans. Here's how to do both:
    
    **Format for ATS Compatibility:**
    
    • Use standard section headings (Experience, Education, Skills)
    • Avoid tables, graphics, and complex formatting
    • Save as .docx or .pdf (check job posting for preference)
    • Use standard fonts like Arial, Calibri, or Times New Roman
    • Include keywords from the job description naturally
    
    **Optimize for Human Readers:**
    
    • Lead with quantified achievements, not responsibilities
    • Use action verbs (Led, Developed, Increased, Optimized)
    • Keep bullet points concise (1-2 lines maximum)
    • Tailor your summary for each application
    • Highlight results with specific numbers and percentages
    """)
    
    # Pro Tips Box
    st.markdown("""
    <div class="highlight-box">
        <strong>🎯 Pro Tip:</strong> Before submitting, paste the job description and your resume into 
        an ATS simulator to check your keyword match rate. Aim for at least 70% keyword alignment with 
        the job posting.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Section 3
    st.markdown("""
    ### 3. Leveraging AI Tools for Your Job Search
    
    AI isn't just being used by employers—smart job seekers are using it too. Here's how to make AI 
    work for you:
    
    **Resume Optimization:**
    
    AI-powered tools can analyze your resume against job descriptions and suggest improvements. 
    They identify missing keywords, formatting issues, and areas where you could strengthen your 
    presentation.
    
    **Job Matching:**
    
    Rather than manually searching through hundreds of listings, AI job matching tools analyze your 
    skills, experience, and preferences to surface the most relevant opportunities. This saves hours 
    of searching and helps you discover roles you might have missed.
    
    **Interview Preparation:**
    
    AI mock interview tools can simulate real interview scenarios, providing feedback on your answers, 
    delivery, and areas for improvement. Practice with AI before facing real interviewers.
    
    **Skills Gap Analysis:**
    
    AI can analyze your current skills against market demands and identify specific areas where 
    upskilling would make you more competitive. This data-driven approach to career development 
    ensures you're investing time in skills that actually matter.
    """)
    
    st.markdown("---")
    
    # Section 4
    st.markdown("""
    ### 4. The Skills That Matter in 2026
    
    The skills landscape is shifting rapidly. Here's what employers are actually looking for:
    
    **Technical Skills in Demand:**
    
    • AI and Machine Learning fundamentals
    • Data analysis and visualization
    • Cloud computing (AWS, Azure, GCP)
    • Automation and workflow optimization
    • Cybersecurity awareness
    
    **Soft Skills That Differentiate:**
    
    According to the 2025 GMAC survey, the top future skills employers seek are:
    
    • Problem-solving with a human edge
    • Strategic thinking and adaptability
    • Communication and collaboration
    • Ethical leadership and decision-making
    • Cultural awareness for global challenges
    
    **The AI Competency Factor:**
    
    Nearly 41% of tech job postings now list AI as a required skill or focus area. Even in non-technical 
    roles, familiarity with AI tools is becoming expected. This doesn't mean you need to be a data 
    scientist—but you should be comfortable using AI-powered tools in your work.
    """)
    
    st.markdown("---")
    
    # Section 5
    st.markdown("""
    ### 5. Building Your Personal Brand Online
    
    In 2026, your online presence is often reviewed before your resume. Here's how to make it work for you:
    
    **LinkedIn Optimization:**
    
    • Use a professional photo and compelling headline
    • Write a summary that tells your career story
    • List skills that match your target roles
    • Request recommendations from colleagues
    • Engage with industry content regularly
    
    **Digital Portfolio:**
    
    • Create a simple website showcasing your work
    • Include case studies with measurable results
    • Document projects with clear problem-solution-outcome format
    • Keep content updated and relevant
    
    **Thought Leadership:**
    
    • Share insights on industry trends
    • Comment thoughtfully on relevant posts
    • Write articles demonstrating your expertise
    • Participate in professional communities
    """)
    
    st.markdown("---")
    
    # Section 6
    st.markdown("""
    ### 6. The Modern Interview: What to Expect
    
    Interviews in 2026 go beyond traditional Q&A. Be prepared for:
    
    **Video Interviews:**
    
    Many first-round interviews are now conducted via video. Test your technology, ensure good lighting 
    and audio, and maintain eye contact with the camera.
    
    **AI-Assisted Interviews:**
    
    Some companies use AI to analyze video interviews, evaluating factors like communication clarity, 
    enthusiasm, and keyword usage. Be natural but mindful of clear articulation.
    
    **Skills-Based Assessments:**
    
    Expect practical tests relevant to the role. These might include coding challenges, case studies, 
    writing samples, or role-play scenarios.
    
    **Behavioral Questions:**
    
    The STAR method (Situation, Task, Action, Result) remains essential. Prepare 5-7 strong examples 
    that demonstrate key competencies.
    
    **Reverse Interviews:**
    
    Companies increasingly want to see your curiosity. Prepare thoughtful questions about the role, 
    team dynamics, growth opportunities, and company culture.
    """)
    
    st.markdown("---")
    
    # Section 7
    st.markdown("""
    ### 7. Maintaining Mental Resilience During Your Search
    
    Job searching is emotionally demanding. Here's how to stay resilient:
    
    **Set Realistic Expectations:**
    
    The average job search takes 3-6 months. Understand this is a marathon, not a sprint. 
    Celebrate small wins along the way.
    
    **Create Structure:**
    
    Treat your job search like a job. Set daily goals, maintain regular hours, and take 
    scheduled breaks. Structure prevents burnout.
    
    **Track Your Progress:**
    
    Keep a log of applications, responses, and learnings. This helps identify what's working 
    and provides evidence of your efforts during difficult periods.
    
    **Build Support Systems:**
    
    Connect with other job seekers, join professional groups, and maintain relationships with 
    friends and family. You don't have to do this alone.
    
    **Practice Self-Care:**
    
    Regular exercise, adequate sleep, and activities you enjoy aren't luxuries—they're essential 
    for maintaining the energy and positivity needed for a successful search.
    """)
    
    st.markdown("---")
    
    # Conclusion
    st.markdown("""
    ### Conclusion: Your 2026 Job Search Action Plan
    
    The job market has changed, but opportunity still exists for those who adapt. Here's your action plan:
    
    **Week 1-2: Foundation**
    • Audit and update your resume for ATS compatibility
    • Optimize your LinkedIn profile
    • Identify 3-5 AI tools to enhance your search
    
    **Week 3-4: Skills Assessment**
    • Evaluate your skills against market demands
    • Identify 1-2 high-impact skills to develop
    • Begin relevant coursework or certification
    
    **Week 5-8: Active Search**
    • Apply strategically to 5-10 well-matched positions weekly
    • Customize each application for the specific role
    • Track all applications and follow up appropriately
    
    **Ongoing: Continuous Improvement**
    • Analyze what's working and adjust
    • Keep learning and building skills
    • Maintain your network and online presence
    
    Remember: In 2026's job market, success goes to those who combine traditional fundamentals with 
    modern AI-powered tools and strategies. The technology exists to make your search more efficient 
    and effective—use it.
    """)
    
    # CTA Box
    st.markdown("""
    <div class="cta-box">
        <h3>🚀 Ready to Supercharge Your Job Search?</h3>
        <p>Job-Search-Agent combines AI-powered CV optimization, career strategy analysis, and emotional 
        resilience tracking to give you every advantage in your job search.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Start Your Free Career Analysis →", type="primary", use_container_width=True):
        st.session_state.current_page = "Main Page"
        st.switch_page("Main_Page.py")
    
    st.markdown("---")
    
    # Article Footer
    st.markdown("""
    **Tags:** job search 2026, AI job search tools, resume optimization, ATS resume tips, career guidance, 
    interview preparation, skills development, career transition, job hunting strategies
    
    **Share this article:** Help others navigate the modern job market by sharing these insights.
    """)


def render_ats_article():
    """ATS optimization article"""
    st.markdown("""
    <div class="blog-post">
        <h1 style="font-size: 2rem;">🎯 5 Tips for Optimizing Your CV for ATS Systems</h1>
        <div class="blog-meta">📅 January 2026 • ⏱️ 5 min read</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Applicant Tracking Systems (ATS) are used by most companies to filter resumes before any human 
    sees them. Here's how to ensure your CV makes it through:
    
    ### 1. Use Standard Formatting
    
    ATS systems struggle with complex layouts. Stick to simple, clean formatting with standard 
    section headers like "Experience," "Education," and "Skills."
    
    ### 2. Include Relevant Keywords
    
    Carefully read the job description and include matching keywords naturally throughout your CV. 
    Don't keyword stuff—integrate them meaningfully.
    
    ### 3. Avoid Graphics and Tables
    
    While visually appealing, graphics, tables, and text boxes often confuse ATS parsers. Keep 
    your content in standard text format.
    
    ### 4. Use Standard File Formats
    
    Submit your CV as a .docx or .pdf file unless otherwise specified. These formats are most 
    reliably parsed by ATS systems.
    
    ### 5. Quantify Your Achievements
    
    Use numbers to demonstrate impact: "Increased sales by 25%" is more powerful than "Improved 
    sales performance."
    """)
    
    st.info("💡 Use Job-Search-Agent's CV Compiler to check your ATS compatibility score!")


def render_interview_article():
    """Interview preparation article"""
    st.markdown("""
    <div class="blog-post">
        <h1 style="font-size: 2rem;">💼 How to Prepare for Behavioral Interviews</h1>
        <div class="blog-meta">📅 January 2026 • ⏱️ 7 min read</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Behavioral interviews focus on how you've handled situations in the past. Master the STAR 
    method to structure winning answers:
    
    ### The STAR Method
    
    **S - Situation:** Set the context for your story
    
    **T - Task:** Describe your responsibility in that situation
    
    **A - Action:** Explain the steps you took to address it
    
    **R - Result:** Share the outcomes of your actions
    
    ### Common Behavioral Questions
    
    • Tell me about a time you faced a difficult challenge at work
    • Describe a situation where you had to work with a difficult colleague
    • Give an example of when you showed leadership
    • Tell me about a time you failed and what you learned
    
    ### Preparation Tips
    
    1. Prepare 5-7 strong STAR stories covering different competencies
    2. Practice out loud—verbal delivery matters
    3. Keep answers concise (2-3 minutes maximum)
    4. Be honest—interviewers can spot fabrication
    5. Show reflection and growth from each experience
    """)
    
    st.info("💡 Use Job-Search-Agent's Voice Interview Simulator to practice your responses!")


def render_career_transition_article():
    """Career transition article"""
    st.markdown("""
    <div class="blog-post">
        <h1 style="font-size: 2rem;">📈 Career Transition: Moving from Technical to Management Roles</h1>
        <div class="blog-meta">📅 December 2025 • ⏱️ 10 min read</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Thinking about moving from an individual contributor role into management? Here's what you 
    need to know about making the transition successfully:
    
    ### Understanding the Shift
    
    Moving to management isn't just a promotion—it's a career change. Your success will be 
    measured differently: not by what you produce, but by what your team produces.
    
    ### Skills You'll Need to Develop
    
    **People Management**
    • Giving effective feedback
    • Conducting productive 1:1 meetings
    • Handling difficult conversations
    • Building and maintaining team morale
    
    **Strategic Thinking**
    • Setting team objectives aligned with company goals
    • Resource allocation and prioritization
    • Long-term planning and roadmapping
    
    **Communication**
    • Translating between technical and business stakeholders
    • Presenting to leadership
    • Writing clear documentation and updates
    
    ### Making the Transition
    
    1. **Seek leadership opportunities** in your current role
    2. **Find a mentor** who has made similar transitions
    3. **Take on project management** responsibilities
    4. **Develop your emotional intelligence**
    5. **Build relationships** across departments
    
    ### Common Challenges
    
    • Letting go of hands-on technical work
    • Managing former peers
    • Dealing with ambiguity and competing priorities
    • Taking responsibility for others' performance
    """)
    
    st.info("💡 Use Job-Search-Agent's Skill Migration tool to map your path to management!")


blog_page()
