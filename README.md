Job-Search-Agent - AI-Powered Career Development Platform
📋 Executive Summary
This app is a comprehensive, AI-powered career development application built with Streamlit and Supabase. The platform helps job seekers optimize their career journey through intelligent CV analysis, personalized career path recommendations, emotional wellness tracking, and interview preparation tools.

🚀 Key Features
1. Smart Dashboard (streamlit_app.py)

AI-Powered CV Analysis: Upload your CV and receive instant strategic insights
Predictive Match Scoring: Get a compatibility score for your target roles
Personalized Strategy Generation: AI generates tailored job search strategies with domestic and international opportunities
Secure Authentication: Full user authentication with login, signup, password reset, and account deletion
Instant Cover Letter Generator: AI-crafted cover letters tailored to specific job descriptions
Voice Interview Simulator: Practice interviews with AI-generated questions and receive feedback

2. Emotional Endurance Tracker (1_Emotional_Tracker.py)

Resilience Score Calculation: Track your mental wellness during the job search
Daily Mood & Activity Logging: Record your emotional state and activity levels
Trend Visualization: Interactive charts showing your emotional patterns over time
AI-Powered Insights: Personalized tips based on your current resilience status
Burnout Prevention Alerts: Early warning system for mental fatigue

3. Feedback Loop (2_Feedback_Loop.py)

Application Outcome Tracking: Monitor your job application results
Performance Analytics: Identify patterns in successful vs unsuccessful applications
Continuous Improvement Insights: Learn from past applications to improve future ones

4. Skill Migration Map (3_Skill_Migration.py)

Industry-Specific Career Paths: Automatic detection of your industry (Education, Healthcare, Technology, Finance, Retail, Hospitality, Construction)
Personalized Career Progression: Three tailored career paths with success rates and timelines
90-Day Skill Sprint Generator: AI-powered action plans for skill development
Skill Gap Analysis: Visual representation of your current skills vs required skills
Skill Decay Warnings: Alerts for certifications and skills that need refreshing
Milestone Tracking: Month-by-month roadmap for career advancement

5. CV Compiler & Optimizer (4_CV_Compiler.py)

Smart CV Tailor: AI rewrites your CV bullets to match job descriptions
ATS Compliance Scoring: Check how well your CV passes Applicant Tracking Systems
Human Clarity Score: Ensure your CV is readable and impactful
Application Ledger: Track all your job applications in one place
Status Updates: Monitor application outcomes (Pending, Interview, Rejected, Offer)
PDF/Text Export: Download optimized CVs in multiple formats

6. Password Reset (Reset_Password.py)

Secure Password Recovery: Email-based password reset flow
Token Verification: Secure OTP-based authentication
Manual Token Entry: Fallback option for token input


🛠 Technology Stack
ComponentTechnologyFrontendStreamlitBackend/DatabaseSupabase (PostgreSQL)AuthenticationSupabase AuthAI/ML EngineGoogle Gemini 2.5 FlashNLP ProcessingGroq (LLaMA 3.3 70B)Vector DatabaseQdrantPDF ProcessingPyPDF, FPDFDeploymentRailwayMobile AppsMedian.co (iOS/Android wrapper)

📊 Database Schema
TablePurposeprofilesUser profile informationanalysesCV analysis reports and strategiesmood_logsEmotional tracking dataapplicationsJob application history

🔐 Security Features

Secure Authentication: Email/password with encrypted storage
Password Reset: Secure token-based recovery via email
Account Deletion: Full GDPR-compliant data removal
Session Management: Secure session handling with Supabase Auth


📱 Platform Availability
PlatformStatusWeb App✅ LiveiOS App🔄 In ReviewAndroid App🔄 Ready for Deployment

🎯 Target Users

Job seekers across all industries
Career changers looking to transition
Professionals seeking advancement
Recent graduates entering the workforce
International candidates seeking visa sponsorship


🌟 Unique Value Propositions

AI-Driven Personalization: Every recommendation is tailored to your unique CV and career goals
Holistic Approach: Combines technical optimization with emotional wellness tracking
Industry-Specific Guidance: Recognizes 7+ industries and provides relevant career paths
Real-Time ATS Optimization: Ensures your CV passes automated screening systems
End-to-End Tracking: From CV optimization to application tracking to interview prep


📈 Future Roadmap

 LinkedIn Integration
 Job Board API Connections
 AI Video Interview Practice
 Salary Negotiation Coach
 Networking Recommendations
 Multi-language Support


🔗 Links

Live App: https://job-search-agent.com
GitHub: [Your Repository URL]
App Store: Coming Soon
Play Store: Coming Soon


📄 License
© 2026 job-search-agent. All rights reserved.

👨‍💻 Developer
Paramjeet Singh Saini
