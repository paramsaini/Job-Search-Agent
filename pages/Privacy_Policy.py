import streamlit as st

st.set_page_config(page_title="Privacy Policy - Job-Search-Agent", page_icon="🔒", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        background-attachment: fixed;
        color: #e2e8f0;
    }
    h1, h2, h3, p, li { color: #e2e8f0 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔒 Privacy Policy")
st.markdown("**Last Updated: January 27, 2026**")

st.markdown("""
---

## 1. Introduction

Welcome to Job-Search-Agent ("we," "our," or "us"). We are committed to protecting your privacy and personal information. This Privacy Policy explains how we collect, use, and safeguard your data when you use our mobile application.

## 2. Information We Collect

### Information You Provide
- **Account Information:** Email address and password when you create an account
- **Profile Information:** Resume/CV documents you upload for analysis
- **Career Data:** Job preferences, application history, and career goals

### Information Collected Automatically
- **Usage Data:** Features you use and interactions within the app
- **Device Information:** Device type and operating system for app optimization

## 3. How We Use Your Information

We use your information to:
- Provide personalized career recommendations and job matching
- Generate cover letters and analyze your CV
- Improve our AI-powered career guidance features
- Communicate important updates about our service
- Maintain and improve app functionality

## 4. Data Storage and Security

- Your data is stored securely using Supabase, an enterprise-grade database platform
- We use industry-standard encryption for data transmission (HTTPS/TLS)
- We do not sell, trade, or share your personal information with third parties for marketing purposes

## 5. Third-Party Services

Our app uses the following third-party services:
- **Supabase:** For secure authentication and data storage
- **Google Gemini API:** For AI-powered career analysis (your data is processed but not stored by Google)
- **Groq API:** For natural language processing features

## 6. Your Rights

You have the right to:
- **Access:** View all personal data we hold about you
- **Delete:** Request deletion of your account and all associated data through Account Settings
- **Export:** Request a copy of your data
- **Opt-out:** Stop using our services at any time

## 7. Account Deletion

You can delete your account and all associated data at any time:
1. Go to Account Settings in the app
2. Click "Delete Account"
3. Confirm deletion

All your data will be permanently removed from our systems.

## 8. Children's Privacy

Our app is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13.

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.

## 10. Contact Us

If you have any questions about this Privacy Policy, please contact us at:

**Email:** support@job-search-agent.com

---

*By using Job-Search-Agent, you agree to the collection and use of information in accordance with this Privacy Policy.*
""")
