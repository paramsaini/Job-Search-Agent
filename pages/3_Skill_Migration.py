import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import os
import json
import pypdf
from groq import Groq

# --- PAGE CONFIG ---
st.set_page_config(page_title="Skill Migration - Job-Search-Agent", page_icon="📈", layout="wide")

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
    [data-testid="stSidebar"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
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
    }
    
    .stSelectbox>div>div, .stFileUploader>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    hr { border-color: rgba(255, 107, 53, 0.2) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Configuration ---
BG_DARK = "#0a0a0f"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#ff6b35"
ACCENT_GOLD = "#f7c531"
ACCENT_GREEN = "#10B981"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_BLUE = "#3B82F6"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key: return None
    return create_client(url, key)

def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None

# Initialize Groq
if 'groq' not in st.session_state:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key:
        st.session_state.groq = Groq(api_key=groq_key)
    else:
        st.session_state.groq = None

# --- Helper Functions ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""
# --- Industry Detection with Career Paths ---
def detect_industry_and_paths(report, cv_text=""):
    """Detect the industry from the CV and return industry-specific career paths"""
    
    industries = {
        'construction': {
            'keywords': ['carpenter', 'carpentry', 'construction', 'builder', 'joinery', 'woodwork', 
                        'timber', 'framing', 'roofing', 'flooring', 'cabinet', 'furniture', 'plumber',
                        'electrician', 'mason', 'bricklayer', 'plasterer', 'painter', 'decorator',
                        'site', 'foreman', 'apprentice', 'tradesman', 'tools', 'safety', 'building',
                        'renovation', 'remodel', 'install', 'fitting', 'measure', 'cut', 'saw'],
            'title': '🔨 Construction & Trades Industry',
            'career_paths': {
                "Senior Tradesperson": {
                    "color": "#10B981",
                    "success_rate": 85,
                    "timeline": "6-12 months",
                    "target_role": "Lead Carpenter / Site Supervisor",
                    "required_skills": ["Advanced Trade Skills", "Team Leadership", "Quality Control"],
                    "skill_gaps": [
                        {"skill": "Site Supervision", "gap": 25, "priority": "High"},
                        {"skill": "Team Leadership", "gap": 20, "priority": "Medium"},
                        {"skill": "Health & Safety Compliance", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Complete advanced trade certifications (NVQ Level 3+)"},
                        {"month": "Month 3-4", "task": "Lead small team projects"},
                        {"month": "Month 5-6", "task": "Obtain CSCS Gold Card / Supervisor card"},
                        {"month": "Month 7-9", "task": "Manage quality control on projects"},
                        {"month": "Month 10-12", "task": "Apply for Lead Tradesperson positions"}
                    ]
                },
                "Site Management": {
                    "color": "#3B82F6",
                    "success_rate": 70,
                    "timeline": "12-18 months",
                    "target_role": "Site Manager / Project Coordinator",
                    "required_skills": ["Project Management", "Budget Control", "Client Relations"],
                    "skill_gaps": [
                        {"skill": "Project Planning", "gap": 35, "priority": "High"},
                        {"skill": "Budget Management", "gap": 40, "priority": "High"},
                        {"skill": "Contractor Coordination", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-3", "task": "SMSTS (Site Management Safety Training Scheme)"},
                        {"month": "Month 4-6", "task": "Learn project management software"},
                        {"month": "Month 7-9", "task": "Shadow existing site managers"},
                        {"month": "Month 10-12", "task": "Manage sub-contractors on projects"},
                        {"month": "Month 13-18", "task": "Transition to Site Manager role"}
                    ]
                },
                "Business Owner": {
                    "color": "#8B5CF6",
                    "success_rate": 55,
                    "timeline": "18-24 months",
                    "target_role": "Self-Employed Contractor / Business Owner",
                    "required_skills": ["Business Management", "Marketing", "Financial Planning"],
                    "skill_gaps": [
                        {"skill": "Business Planning", "gap": 50, "priority": "High"},
                        {"skill": "Marketing & Sales", "gap": 45, "priority": "High"},
                        {"skill": "Accounting Basics", "gap": 35, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-4", "task": "Complete business management course"},
                        {"month": "Month 5-8", "task": "Build client network and portfolio"},
                        {"month": "Month 9-12", "task": "Register business and get insurance"},
                        {"month": "Month 13-18", "task": "Start taking independent contracts"},
                        {"month": "Month 19-24", "task": "Scale business and hire apprentices"}
                    ]
                }
            },
            'skills': ['Trade Expertise', 'Safety Compliance', 'Blueprint Reading', 'Tool Proficiency', 'Physical Stamina', 'Time Management'],
            'decay_skills': ['Safety Certifications', 'Building Regulations Knowledge', 'Tool Technology']
        },
        'healthcare': {
            'keywords': ['patient care', 'healthcare', 'medical', 'nursing', 'clinical', 
                        'carer', 'nurse', 'hospital', 'elderly care', 'disability support', 'support worker',
                        'nhs', 'doctor', 'therapist', 'pharmacist', 'midwife', 'caregiver', 'care home',
                        'mental health', 'social care', 'care assistant', 'health visitor', 'physiotherapy',
                        'occupational therapy', 'care worker', 'residential care', 'nursing home'],
            'title': '🏥 Healthcare & Care Industry',
            'career_paths': {
                "Senior Care Worker": {
                    "color": "#10B981",
                    "success_rate": 85,
                    "timeline": "6-12 months",
                    "target_role": "Team Leader / Care Supervisor",
                    "required_skills": ["Advanced Patient Care", "Team Leadership", "Documentation"],
                    "skill_gaps": [
                        {"skill": "Leadership Skills", "gap": 25, "priority": "High"},
                        {"skill": "Care Planning", "gap": 20, "priority": "Medium"},
                        {"skill": "Medication Administration", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Complete NVQ Level 3 in Health & Social Care"},
                        {"month": "Month 3-4", "task": "Shadow senior care workers"},
                        {"month": "Month 5-6", "task": "Lead shift handovers"},
                        {"month": "Month 7-9", "task": "Manage care plans independently"},
                        {"month": "Month 10-12", "task": "Apply for Team Leader positions"}
                    ]
                },
                "Care Management": {
                    "color": "#3B82F6",
                    "success_rate": 70,
                    "timeline": "12-18 months",
                    "target_role": "Care Manager / Registered Manager",
                    "required_skills": ["Staff Management", "CQC Compliance", "Budget Management"],
                    "skill_gaps": [
                        {"skill": "Regulatory Compliance", "gap": 35, "priority": "High"},
                        {"skill": "Staff Recruitment", "gap": 30, "priority": "High"},
                        {"skill": "Budget Control", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-3", "task": "Level 5 Diploma in Leadership for Health & Social Care"},
                        {"month": "Month 4-6", "task": "Learn CQC requirements thoroughly"},
                        {"month": "Month 7-9", "task": "Assist with staff management duties"},
                        {"month": "Month 10-12", "task": "Handle family liaison and care reviews"},
                        {"month": "Month 13-18", "task": "Register as Care Manager with CQC"}
                    ]
                },
                "Clinical Specialist": {
                    "color": "#8B5CF6",
                    "success_rate": 60,
                    "timeline": "24-36 months",
                    "target_role": "Registered Nurse / Clinical Lead",
                    "required_skills": ["Clinical Knowledge", "Medical Procedures", "Critical Thinking"],
                    "skill_gaps": [
                        {"skill": "Clinical Expertise", "gap": 50, "priority": "High"},
                        {"skill": "Medical Knowledge", "gap": 45, "priority": "High"},
                        {"skill": "Emergency Response", "gap": 30, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-6", "task": "Enroll in nursing degree or equivalent"},
                        {"month": "Month 7-12", "task": "Complete clinical placements"},
                        {"month": "Month 13-24", "task": "Pass NMC registration requirements"},
                        {"month": "Month 25-30", "task": "Work as newly qualified nurse"},
                        {"month": "Month 31-36", "task": "Specialize in chosen clinical area"}
                    ]
                }
            },
            'skills': ['Patient Care', 'Communication', 'First Aid/CPR', 'Documentation', 'Empathy', 'Time Management'],
            'decay_skills': ['First Aid Certification', 'Medication Training', 'Safeguarding Updates']
        },
        'technology': {
            'keywords': ['python', 'java', 'cloud', 'aws', 'coding', 'programming', 'software', 
                        'data', 'machine learning', 'developer', 'engineer', 'devops', 'api',
                        'javascript', 'react', 'database', 'agile', 'scrum', 'web', 'mobile', 'app'],
            'title': '💻 Technology Industry',
            'career_paths': {
                "Senior Developer": {
                    "color": "#10B981",
                    "success_rate": 85,
                    "timeline": "6-12 months",
                    "target_role": "Senior Engineer / Tech Lead",
                    "required_skills": ["Advanced Programming", "System Design", "Code Review"],
                    "skill_gaps": [
                        {"skill": "System Architecture", "gap": 25, "priority": "High"},
                        {"skill": "Technical Leadership", "gap": 20, "priority": "Medium"},
                        {"skill": "Performance Optimization", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Master advanced design patterns"},
                        {"month": "Month 3-4", "task": "Lead code reviews and mentoring"},
                        {"month": "Month 5-6", "task": "Architect a major feature"},
                        {"month": "Month 7-9", "task": "Present technical decisions to stakeholders"},
                        {"month": "Month 10-12", "task": "Apply for Senior/Lead positions"}
                    ]
                },
                "Engineering Management": {
                    "color": "#3B82F6",
                    "success_rate": 70,
                    "timeline": "12-18 months",
                    "target_role": "Engineering Manager / Director",
                    "required_skills": ["People Management", "Strategic Planning", "Stakeholder Management"],
                    "skill_gaps": [
                        {"skill": "People Management", "gap": 40, "priority": "High"},
                        {"skill": "Strategic Planning", "gap": 35, "priority": "High"},
                        {"skill": "Budget Management", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-3", "task": "Complete leadership training"},
                        {"month": "Month 4-6", "task": "Manage sprint planning and retrospectives"},
                        {"month": "Month 7-9", "task": "Handle 1:1s and performance reviews"},
                        {"month": "Month 10-12", "task": "Own team roadmap and hiring"},
                        {"month": "Month 13-18", "task": "Transition to full management role"}
                    ]
                },
                "Technical Architect": {
                    "color": "#8B5CF6",
                    "success_rate": 60,
                    "timeline": "18-24 months",
                    "target_role": "Solutions Architect / Principal Engineer",
                    "required_skills": ["Enterprise Architecture", "Cloud Platforms", "Technical Strategy"],
                    "skill_gaps": [
                        {"skill": "Enterprise Patterns", "gap": 45, "priority": "High"},
                        {"skill": "Cloud Architecture", "gap": 40, "priority": "High"},
                        {"skill": "Technical Writing", "gap": 30, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-4", "task": "AWS/Azure Solutions Architect certification"},
                        {"month": "Month 5-8", "task": "Design enterprise-scale systems"},
                        {"month": "Month 9-12", "task": "Lead architecture review boards"},
                        {"month": "Month 13-18", "task": "Define technical standards"},
                        {"month": "Month 19-24", "task": "Become go-to technical authority"}
                    ]
                }
            },
            'skills': ['Programming', 'Cloud/DevOps', 'System Design', 'Problem Solving', 'Communication', 'Agile/Scrum'],
            'decay_skills': ['Framework Versions', 'Security Best Practices', 'Cloud Services Updates']
        },
        'finance': {
            'keywords': ['accounting', 'finance', 'banking', 'investment', 'audit', 'tax', 'financial',
                        'bookkeeping', 'payroll', 'budget', 'accounts', 'ledger', 'reconciliation'],
            'title': '💰 Finance & Accounting Industry',
            'career_paths': {
                "Senior Accountant": {
                    "color": "#10B981",
                    "success_rate": 80,
                    "timeline": "6-12 months",
                    "target_role": "Senior Accountant / Finance Lead",
                    "required_skills": ["Advanced Accounting", "Financial Reporting", "Analysis"],
                    "skill_gaps": [
                        {"skill": "Financial Analysis", "gap": 25, "priority": "High"},
                        {"skill": "Reporting Standards", "gap": 20, "priority": "Medium"},
                        {"skill": "Software Proficiency", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Complete ACCA/CIMA modules"},
                        {"month": "Month 3-4", "task": "Lead month-end close process"},
                        {"month": "Month 5-6", "task": "Prepare board-level reports"},
                        {"month": "Month 7-9", "task": "Mentor junior accountants"},
                        {"month": "Month 10-12", "task": "Apply for Senior positions"}
                    ]
                },
                "Finance Management": {
                    "color": "#3B82F6",
                    "success_rate": 65,
                    "timeline": "12-24 months",
                    "target_role": "Finance Manager / Financial Controller",
                    "required_skills": ["Team Leadership", "Strategic Finance", "Stakeholder Management"],
                    "skill_gaps": [
                        {"skill": "Strategic Planning", "gap": 35, "priority": "High"},
                        {"skill": "Team Management", "gap": 30, "priority": "High"},
                        {"skill": "Business Partnering", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-4", "task": "Complete professional qualification (ACA/ACCA/CIMA)"},
                        {"month": "Month 5-8", "task": "Lead budget planning cycles"},
                        {"month": "Month 9-12", "task": "Manage finance team members"},
                        {"month": "Month 13-18", "task": "Present to senior leadership"},
                        {"month": "Month 19-24", "task": "Take on Controller responsibilities"}
                    ]
                },
                "CFO Track": {
                    "color": "#8B5CF6",
                    "success_rate": 45,
                    "timeline": "36-60 months",
                    "target_role": "CFO / Finance Director",
                    "required_skills": ["Executive Leadership", "Corporate Strategy", "Investor Relations"],
                    "skill_gaps": [
                        {"skill": "Executive Presence", "gap": 50, "priority": "High"},
                        {"skill": "Corporate Strategy", "gap": 45, "priority": "High"},
                        {"skill": "Board Relations", "gap": 40, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-12", "task": "MBA or executive education program"},
                        {"month": "Month 13-24", "task": "Lead major transformation projects"},
                        {"month": "Month 25-36", "task": "Build investor/stakeholder relationships"},
                        {"month": "Month 37-48", "task": "Serve on subsidiary boards"},
                        {"month": "Month 49-60", "task": "Transition to FD/CFO role"}
                    ]
                }
            },
            'skills': ['Financial Analysis', 'Excel/Modeling', 'Accounting Standards', 'Communication', 'Attention to Detail', 'Regulatory Knowledge'],
            'decay_skills': ['Tax Regulations', 'Accounting Standards Updates', 'Financial Software']
        },
        'retail': {
            'keywords': ['sales', 'retail', 'customer service', 'shop', 'store', 'merchandise', 'stock',
                        'cashier', 'supervisor', 'inventory', 'visual merchandising', 'till'],
            'title': '🛒 Retail & Sales Industry',
            'career_paths': {
                "Senior Sales Associate": {
                    "color": "#10B981",
                    "success_rate": 85,
                    "timeline": "6-12 months",
                    "target_role": "Team Leader / Supervisor",
                    "required_skills": ["Sales Excellence", "Customer Service", "Team Support"],
                    "skill_gaps": [
                        {"skill": "Sales Techniques", "gap": 20, "priority": "High"},
                        {"skill": "Conflict Resolution", "gap": 25, "priority": "Medium"},
                        {"skill": "Product Knowledge", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Consistently exceed sales targets"},
                        {"month": "Month 3-4", "task": "Train new team members"},
                        {"month": "Month 5-6", "task": "Handle customer escalations"},
                        {"month": "Month 7-9", "task": "Lead visual merchandising"},
                        {"month": "Month 10-12", "task": "Apply for Supervisor role"}
                    ]
                },
                "Store Management": {
                    "color": "#3B82F6",
                    "success_rate": 70,
                    "timeline": "12-18 months",
                    "target_role": "Store Manager / Assistant Manager",
                    "required_skills": ["Staff Management", "P&L Responsibility", "Operations"],
                    "skill_gaps": [
                        {"skill": "People Management", "gap": 35, "priority": "High"},
                        {"skill": "Financial Acumen", "gap": 30, "priority": "High"},
                        {"skill": "Inventory Management", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-3", "task": "Complete retail management training"},
                        {"month": "Month 4-6", "task": "Manage staff rotas and schedules"},
                        {"month": "Month 7-9", "task": "Own store KPIs and targets"},
                        {"month": "Month 10-12", "task": "Handle recruitment and HR issues"},
                        {"month": "Month 13-18", "task": "Transition to Store Manager"}
                    ]
                },
                "Regional Manager": {
                    "color": "#8B5CF6",
                    "success_rate": 50,
                    "timeline": "24-36 months",
                    "target_role": "Area Manager / Regional Director",
                    "required_skills": ["Multi-site Management", "Strategic Planning", "Business Development"],
                    "skill_gaps": [
                        {"skill": "Multi-store Operations", "gap": 45, "priority": "High"},
                        {"skill": "Strategic Thinking", "gap": 40, "priority": "High"},
                        {"skill": "Change Management", "gap": 35, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-6", "task": "Excel as Store Manager"},
                        {"month": "Month 7-12", "task": "Support underperforming stores"},
                        {"month": "Month 13-18", "task": "Lead regional initiatives"},
                        {"month": "Month 19-24", "task": "Manage multiple store openings"},
                        {"month": "Month 25-36", "task": "Become Area/Regional Manager"}
                    ]
                }
            },
            'skills': ['Sales Skills', 'Customer Service', 'Visual Merchandising', 'Stock Management', 'Communication', 'Cash Handling'],
            'decay_skills': ['Product Knowledge', 'POS Systems', 'Company Policies']
        },
        'hospitality': {
            'keywords': ['hotel', 'restaurant', 'chef', 'hospitality', 'catering', 'tourism', 'bar',
                        'waiter', 'waitress', 'kitchen', 'food', 'beverage', 'front desk', 'concierge'],
            'title': '🏨 Hospitality & Tourism Industry',
            'career_paths': {
                "Senior Staff": {
                    "color": "#10B981",
                    "success_rate": 80,
                    "timeline": "6-12 months",
                    "target_role": "Shift Supervisor / Head Waiter",
                    "required_skills": ["Service Excellence", "Team Coordination", "Guest Relations"],
                    "skill_gaps": [
                        {"skill": "Leadership", "gap": 25, "priority": "High"},
                        {"skill": "Problem Solving", "gap": 20, "priority": "Medium"},
                        {"skill": "Upselling", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-2", "task": "Master all service standards"},
                        {"month": "Month 3-4", "task": "Train new team members"},
                        {"month": "Month 5-6", "task": "Handle VIP guests and complaints"},
                        {"month": "Month 7-9", "task": "Lead shifts independently"},
                        {"month": "Month 10-12", "task": "Apply for Supervisor position"}
                    ]
                },
                "Department Management": {
                    "color": "#3B82F6",
                    "success_rate": 65,
                    "timeline": "12-24 months",
                    "target_role": "Restaurant Manager / F&B Manager",
                    "required_skills": ["Operations Management", "Staff Development", "Cost Control"],
                    "skill_gaps": [
                        {"skill": "Financial Management", "gap": 35, "priority": "High"},
                        {"skill": "Staff Scheduling", "gap": 30, "priority": "High"},
                        {"skill": "Vendor Relations", "gap": 25, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-4", "task": "Hospitality management certification"},
                        {"month": "Month 5-8", "task": "Manage department budgets"},
                        {"month": "Month 9-12", "task": "Lead staff recruitment"},
                        {"month": "Month 13-18", "task": "Oversee department operations"},
                        {"month": "Month 19-24", "task": "Become Department Manager"}
                    ]
                },
                "General Management": {
                    "color": "#8B5CF6",
                    "success_rate": 45,
                    "timeline": "36-48 months",
                    "target_role": "Hotel General Manager",
                    "required_skills": ["Executive Leadership", "Revenue Management", "Brand Standards"],
                    "skill_gaps": [
                        {"skill": "P&L Management", "gap": 50, "priority": "High"},
                        {"skill": "Revenue Strategy", "gap": 45, "priority": "High"},
                        {"skill": "Owner Relations", "gap": 40, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-12", "task": "Hospitality degree or executive program"},
                        {"month": "Month 13-24", "task": "Manage multiple departments"},
                        {"month": "Month 25-36", "task": "Lead hotel-wide initiatives"},
                        {"month": "Month 37-42", "task": "Serve as Acting GM"},
                        {"month": "Month 43-48", "task": "Become General Manager"}
                    ]
                }
            },
            'skills': ['Customer Service', 'Food Safety', 'Communication', 'Multitasking', 'Attention to Detail', 'Teamwork'],
            'decay_skills': ['Food Hygiene Certificate', 'Health & Safety', 'Menu Knowledge']
        },
        'education': {
            'keywords': ['teacher', 'teaching', 'education', 'school', 'tutor', 'curriculum', 'student',
                        'classroom', 'learning', 'instructor', 'lecturer', 'training', 'academic',
                        'lesson', 'pupils', 'grade', 'elementary', 'secondary', 'primary', 'educator',
                        'pedagogy', 'assessment', 'grading', 'homework', 'lecture', 'faculty',
                        'principal', 'headteacher', 'professor', 'university', 'college', 'literacy',
                        'reading', 'mathematics', 'phonics', 'parent-teacher', 'instructional'],
            'title': '📚 Education Industry',
            'career_paths': {
                "Senior Teacher": {
                    "color": "#10B981",
                    "success_rate": 75,
                    "timeline": "12-24 months",
                    "target_role": "Head of Department / Lead Teacher",
                    "required_skills": ["Curriculum Development", "Mentoring", "Assessment"],
                    "skill_gaps": [
                        {"skill": "Curriculum Design", "gap": 25, "priority": "High"},
                        {"skill": "Staff Mentoring", "gap": 20, "priority": "Medium"},
                        {"skill": "Data Analysis", "gap": 15, "priority": "Low"}
                    ],
                    "milestones": [
                        {"month": "Month 1-4", "task": "Complete NPQ or equivalent qualification"},
                        {"month": "Month 5-8", "task": "Lead curriculum improvements"},
                        {"month": "Month 9-12", "task": "Mentor NQTs/new teachers"},
                        {"month": "Month 13-18", "task": "Coordinate department initiatives"},
                        {"month": "Month 19-24", "task": "Apply for HoD positions"}
                    ]
                },
                "School Leadership": {
                    "color": "#3B82F6",
                    "success_rate": 55,
                    "timeline": "36-48 months",
                    "target_role": "Assistant Head / Deputy Head",
                    "required_skills": ["School Management", "Policy Development", "Stakeholder Engagement"],
                    "skill_gaps": [
                        {"skill": "Strategic Leadership", "gap": 40, "priority": "High"},
                        {"skill": "Budget Management", "gap": 35, "priority": "High"},
                        {"skill": "Ofsted Preparation", "gap": 30, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-12", "task": "NPQSL qualification"},
                        {"month": "Month 13-24", "task": "Lead whole-school initiatives"},
                        {"month": "Month 25-36", "task": "Manage significant budgets"},
                        {"month": "Month 37-42", "task": "Support SLT responsibilities"},
                        {"month": "Month 43-48", "task": "Transition to Assistant Head"}
                    ]
                },
                "Headteacher": {
                    "color": "#8B5CF6",
                    "success_rate": 40,
                    "timeline": "60-84 months",
                    "target_role": "Headteacher / Principal",
                    "required_skills": ["Executive Leadership", "Governance", "Community Relations"],
                    "skill_gaps": [
                        {"skill": "School Vision", "gap": 50, "priority": "High"},
                        {"skill": "Governor Relations", "gap": 45, "priority": "High"},
                        {"skill": "Crisis Management", "gap": 40, "priority": "Medium"}
                    ],
                    "milestones": [
                        {"month": "Month 1-24", "task": "NPQH qualification"},
                        {"month": "Month 25-48", "task": "Serve as Deputy Head"},
                        {"month": "Month 49-60", "task": "Act as Headteacher"},
                        {"month": "Month 61-72", "task": "Apply for Headships"},
                        {"month": "Month 73-84", "task": "Establish as Headteacher"}
                    ]
                }
            },
            'skills': ['Teaching Methods', 'Curriculum Design', 'Student Engagement', 'Communication', 'Technology Integration', 'Assessment'],
            'decay_skills': ['Safeguarding Training', 'EdTech Tools', 'Curriculum Updates']
        }
    }
    
    # Default/general industry
    default_industry = {
        'keywords': [],
        'title': '🎯 General Career Paths',
        'career_paths': {
            "Senior Role": {
                "color": "#10B981",
                "success_rate": 80,
                "timeline": "6-12 months",
                "target_role": "Team Lead / Senior Position",
                "required_skills": ["Core Expertise", "Leadership", "Communication"],
                "skill_gaps": [
                    {"skill": "Leadership Skills", "gap": 25, "priority": "High"},
                    {"skill": "Project Management", "gap": 20, "priority": "Medium"},
                    {"skill": "Communication", "gap": 15, "priority": "Low"}
                ],
                "milestones": [
                    {"month": "Month 1-2", "task": "Excel in current role"},
                    {"month": "Month 3-4", "task": "Take on additional responsibilities"},
                    {"month": "Month 5-6", "task": "Lead small projects"},
                    {"month": "Month 7-9", "task": "Mentor colleagues"},
                    {"month": "Month 10-12", "task": "Apply for senior positions"}
                ]
            },
            "Management Track": {
                "color": "#3B82F6",
                "success_rate": 65,
                "timeline": "12-18 months",
                "target_role": "Manager / Department Head",
                "required_skills": ["People Management", "Strategic Thinking", "Budget Awareness"],
                "skill_gaps": [
                    {"skill": "People Management", "gap": 35, "priority": "High"},
                    {"skill": "Strategic Planning", "gap": 30, "priority": "High"},
                    {"skill": "Financial Acumen", "gap": 25, "priority": "Medium"}
                ],
                "milestones": [
                    {"month": "Month 1-3", "task": "Complete management training"},
                    {"month": "Month 4-6", "task": "Lead team projects"},
                    {"month": "Month 7-9", "task": "Handle team coordination"},
                    {"month": "Month 10-12", "task": "Manage team performance"},
                    {"month": "Month 13-18", "task": "Transition to Manager role"}
                ]
            },
            "Specialist Expert": {
                "color": "#8B5CF6",
                "success_rate": 55,
                "timeline": "18-24 months",
                "target_role": "Subject Matter Expert / Consultant",
                "required_skills": ["Deep Expertise", "Training Skills", "Industry Knowledge"],
                "skill_gaps": [
                    {"skill": "Domain Expertise", "gap": 40, "priority": "High"},
                    {"skill": "Presentation Skills", "gap": 35, "priority": "High"},
                    {"skill": "Consulting Skills", "gap": 30, "priority": "Medium"}
                ],
                "milestones": [
                    {"month": "Month 1-4", "task": "Deepen specialist knowledge"},
                    {"month": "Month 5-8", "task": "Create training materials"},
                    {"month": "Month 9-12", "task": "Present at industry events"},
                    {"month": "Month 13-18", "task": "Build expert reputation"},
                    {"month": "Month 19-24", "task": "Establish as go-to expert"}
                ]
            }
        },
        'skills': ['Communication', 'Problem Solving', 'Teamwork', 'Time Management', 'Adaptability', 'Learning Agility'],
        'decay_skills': ['Industry Knowledge', 'Software Tools', 'Best Practices']
    }
    
    # Combine report text and CV text for detection
    combined_text = str(report).lower() + " " + cv_text.lower()
    
    # Use word boundaries for more accurate matching
    import re
    
    # Find matching industry with weighted scoring
    best_match = None
    best_score = 0
    
    for industry_key, industry_data in industries.items():
        score = 0
        for kw in industry_data['keywords']:
            # Use word boundary matching for more accuracy
            # This prevents 'care' matching in 'career' or 'health' matching in 'healthcare'
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = len(re.findall(pattern, combined_text))
            
            # Give more weight to longer, more specific keywords
            if len(kw) >= 6:
                score += matches * 3  # Longer keywords are more specific
            elif len(kw) >= 4:
                score += matches * 2
            else:
                score += matches
        
        # Require minimum score threshold
        if score > best_score and score >= 4:
            best_score = score
            best_match = (industry_key, industry_data)
    
    if best_match:
        return best_match
    
    return 'general', default_industry

def fetch_latest_report():
    """Retrieves the latest analysis report from Supabase"""
    user_id = st.session_state.get('user_id')
    if not user_id or not supabase: return None
    try:
        response = supabase.table("analyses").select("report_json")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        if response.data:
            raw_json = response.data[0]['report_json']
            if isinstance(raw_json, str):
                return json.loads(raw_json)
            return raw_json
    except Exception as e:
        st.error(f"Database Error: {e}")
    return None

# --- Page Render ---
def skill_migration_page():
    # Back to Main Page
    st.page_link("Main_Page.py", label="← Back to Main Page", icon="🏠")
    
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
    
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🌐 Skill Migration Map</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to view your skill migration map.")
        return

    # Initialize session states
    if 'selected_career_path' not in st.session_state:
        st.session_state.selected_career_path = None
    if 'sprint_generated' not in st.session_state:
        st.session_state.sprint_generated = False
    if 'sprint_plan' not in st.session_state:
        st.session_state.sprint_plan = None
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = set()
    if 'skill_migration_report' not in st.session_state:
        st.session_state.skill_migration_report = None
    if 'cv_text_for_migration' not in st.session_state:
        st.session_state.cv_text_for_migration = ""

    # SECTION 1: ALWAYS VISIBLE - CV Upload Feature
    st.subheader("1️⃣ Upload Your Document")
    st.caption("Upload your CV to analyze your skills and generate personalized career paths")
    
    col_upload, col_buttons = st.columns([3, 1])
    
    with col_upload:
        uploaded_cv = st.file_uploader(
            "Upload your CV (PDF/TXT)", 
            type=["pdf", "txt"], 
            key="skill_migration_cv_upload",
            help="Supported formats: PDF, TXT"
        )
    
    with col_buttons:
        st.markdown("<br>", unsafe_allow_html=True)
        
        analyze_disabled = uploaded_cv is None
        if st.button("🚀 Analyze CV", type="primary", use_container_width=True, disabled=analyze_disabled):
            if uploaded_cv:
                cv_text = extract_text(uploaded_cv)
                if cv_text:
                    st.session_state.cv_text_for_migration = cv_text
                    
                    if st.session_state.get('agent'):
                        with st.spinner("🔍 Analyzing your CV..."):
                            try:
                                md, rep, src = st.session_state.agent.generate_strategy(cv_text, "All")
                                st.session_state.skill_migration_report = rep
                                
                                st.session_state.selected_career_path = None
                                st.session_state.sprint_generated = False
                                st.session_state.sprint_plan = None
                                st.session_state.completed_tasks = set()
                                
                                if supabase and st.session_state.user_id:
                                    try:
                                        supabase.table("analyses").insert({
                                            "user_id": st.session_state.user_id,
                                            "report_json": rep
                                        }).execute()
                                    except: pass
                                
                                st.success("✅ CV analyzed successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    else:
                        st.error("Analysis agent not available. Please check configuration.")
                else:
                    st.warning("Could not extract text from the uploaded file.")
        
        if st.button("🔄 Reset", use_container_width=True, help="Clear current analysis and start fresh"):
            st.session_state.skill_migration_report = None
            st.session_state.cv_text_for_migration = ""
            st.session_state.selected_career_path = None
            st.session_state.sprint_generated = False
            st.session_state.sprint_plan = None
            st.session_state.completed_tasks = set()
            st.success("🔄 Reset complete! Upload a new CV to start fresh analysis.")
            st.rerun()
    
    if not uploaded_cv:
        st.info("👆 Upload your CV above to get started with your personalized skill migration analysis.")
    
    st.markdown("---")

    # Load existing report
    report = st.session_state.get('skill_migration_report')
    cv_text = st.session_state.get('cv_text_for_migration', '')
    
    if not report:
        if "results" in st.session_state and "rep" in st.session_state.results:
            report = st.session_state.results["rep"]
            st.session_state.skill_migration_report = report
        else:
            with st.spinner("Loading your latest analysis..."):
                report = fetch_latest_report()
                if report:
                    st.session_state.skill_migration_report = report
    
    if not report:
        st.markdown("""
        <div style="background: rgba(255, 140, 0, 0.1); border: 1px solid #FF8C00; border-radius: 12px; padding: 30px; text-align: center; margin: 20px 0;">
            <h3 style="color: #FF8C00;">📊 No Analysis Found</h3>
            <p style="color: #ccc;">Upload your CV above and click <strong>"Analyze CV"</strong> to see your personalized:</p>
            <ul style="text-align: left; color: #aaa; max-width: 400px; margin: 0 auto;">
                <li>Industry-specific career trajectory recommendations</li>
                <li>90-day skill sprint plan tailored to your profession</li>
                <li>Skill gap analysis based on your experience</li>
                <li>Skill decay warnings relevant to your field</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return

    # DETECT INDUSTRY AND GET PERSONALIZED DATA
    industry_key, industry_data = detect_industry_and_paths(report, cv_text)
    career_paths = industry_data['career_paths']
    industry_skills = industry_data['skills']
    decay_skills = industry_data['decay_skills']
    industry_title = industry_data['title']

    # SECTION 2: Profile Scores
    st.subheader("2️⃣ Your Profile Scores")
    c1, c2, c3 = st.columns(3)
    with c1:
        score = report.get('predictive_score', 0)
        st.metric("Predictive Match", f"{score}%")
        st.progress(score / 100)
    with c2:
        tech = report.get('tech_score', 0)
        st.metric("Skills Strength", f"{tech}%")
        st.progress(tech / 100)
    with c3:
        weakest_skill = report.get('weakest_link_skill', 'N/A')
        st.error(f"Focus Area: {weakest_skill}")
        st.caption("Prioritize improving this skill.")

    st.markdown("---")
    
    # SECTION 3: Interactive Career Path Visualizer (INDUSTRY-SPECIFIC)
    st.subheader(f"3️⃣ {industry_title} - Career Paths")
    st.caption("👆 Click on a career path to see detailed requirements and timeline")
    
    cols = st.columns(3)
    path_names = list(career_paths.keys())
    
    for idx, path_name in enumerate(path_names):
        path_data = career_paths[path_name]
        with cols[idx]:
            card_selected = st.session_state.selected_career_path == path_name
            border_width = "3px" if card_selected else "1px"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {path_data['color']}40, {path_data['color']}20); 
                        padding: 20px; border-radius: 12px; border: {border_width} solid {path_data['color']}; 
                        min-height: 180px; margin-bottom: 10px;">
                <h4 style="color: {path_data['color']}; margin: 0 0 8px 0;">{path_name}</h4>
                <p style="color: #ccc; font-size: 0.85em; margin: 8px 0;">→ {path_data['target_role']}</p>
                <p style="color: white; font-weight: bold; font-size: 1.3em; margin: 10px 0;">{path_data['success_rate']}% success rate</p>
                <p style="color: #aaa; font-size: 0.85em; margin: 0;">⏱️ {path_data['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            btn_type = "primary" if card_selected else "secondary"
            btn_label = "✓ Selected" if card_selected else "View Details"
            
            if st.button(btn_label, key=f"btn_{path_name}", type=btn_type, use_container_width=True):
                if st.session_state.selected_career_path == path_name:
                    st.session_state.selected_career_path = None
                else:
                    st.session_state.selected_career_path = path_name
                st.rerun()
    
    # Display selected career path details
    if st.session_state.selected_career_path and st.session_state.selected_career_path in career_paths:
        selected_path = career_paths[st.session_state.selected_career_path]
        
        st.markdown("---")
        st.markdown(f"""
        <div style="background: {selected_path['color']}15; border: 2px solid {selected_path['color']}; border-radius: 12px; padding: 20px; margin: 15px 0;">
            <h3 style="color: {selected_path['color']}; margin-top: 0;">📋 {st.session_state.selected_career_path} - Detailed View</h3>
        </div>
        """, unsafe_allow_html=True)
        
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown("**🎯 Required Skill Gaps to Close:**")
            for gap in selected_path['skill_gaps']:
                if gap['priority'] == "High":
                    priority_color = "#ef4444"
                    priority_icon = "🔴"
                elif gap['priority'] == "Medium":
                    priority_color = "#f59e0b"
                    priority_icon = "🟡"
                else:
                    priority_color = "#10b981"
                    priority_icon = "🟢"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {priority_color};">
                    <strong>{gap['skill']}</strong>: {gap['gap']}% gap 
                    <span style="color: {priority_color}; font-size: 0.85em;">{priority_icon} {gap['priority']} Priority</span>
                </div>
                """, unsafe_allow_html=True)
        
        with detail_col2:
            st.markdown("**📅 Timeline & Milestones:**")
            for milestone in selected_path['milestones']:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <strong style="color: {selected_path['color']};">{milestone['month']}</strong><br>
                    <span style="color: #ccc;">✅ {milestone['task']}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    
    # SECTION 4: AI-Powered 90-Day Skill Sprint Generator
    st.subheader("4️⃣ AI-Powered 90-Day Skill Sprint Generator")
    st.caption(f"📚 Personalized learning plan for **{industry_title}** based on your weakest skill: **{weakest_skill}**")
    
    col_generate, col_reset_sprint = st.columns([3, 1])
    
    with col_generate:
        if st.button("🚀 Generate 90-Day Sprint Plan", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is creating your personalized learning plan..."):
                if st.session_state.get('groq'):
                    try:
                        prompt = f"""Create a detailed 90-day skill sprint plan for someone in the {industry_title} industry who needs to improve their "{weakest_skill}" skill.

The person's current profile:
- Industry: {industry_title}
- Weakest Skill: {weakest_skill}
- Current Skills Score: {report.get('tech_score', 50)}%
- Key skills in this industry: {', '.join(industry_skills)}

Format the response EXACTLY as follows:

WEEK 1-2: Foundation
- Task: [Specific task relevant to {industry_title}]
- Resource: [Free course or resource - Coursera, YouTube, industry-specific]
- Project: [Small project to practice]

WEEK 3-4: Building Blocks
- Task: [Specific task]
- Resource: [Free course or resource]
- Project: [Project to build]

WEEK 5-6: Intermediate Skills
- Task: [Specific task]
- Resource: [Free course or resource]
- Project: [Project to build]

WEEK 7-8: Advanced Concepts
- Task: [Specific task]
- Resource: [Free course or resource]
- Project: [Project to build]

WEEK 9-10: Real-World Application
- Task: [Specific task]
- Resource: [Free course or resource]
- Project: [Portfolio project]

WEEK 11-12: Certification & Portfolio
- Task: [Get certified]
- Certification: [Recommended certification for {industry_title}]
- Final Project: [Capstone project]

RECOMMENDED CERTIFICATIONS:
1. [Certification relevant to {industry_title}]
2. [Certification name and provider]
3. [Certification name and provider]

Keep it practical with free resources. Make all recommendations relevant to {industry_title}."""
                        
                        completion = st.session_state.groq.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.session_state.sprint_plan = completion.choices[0].message.content
                        st.session_state.sprint_generated = True
                        st.session_state.completed_tasks = set()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate plan: {e}")
                else:
                    st.session_state.sprint_plan = f"""WEEK 1-2: Foundation
- Task: Understand core concepts of {weakest_skill} in {industry_title}
- Resource: YouTube - Search "{weakest_skill} {industry_key} training"
- Project: Create a simple demonstration of {weakest_skill} skills

WEEK 3-4: Building Blocks
- Task: Learn intermediate {weakest_skill} techniques for {industry_title}
- Resource: Coursera/LinkedIn Learning - Free courses on {weakest_skill}
- Project: Apply skills in a real {industry_key} scenario

WEEK 5-6: Intermediate Skills
- Task: Deep dive into {industry_title} best practices for {weakest_skill}
- Resource: Industry association training materials
- Project: Contribute to a team project using {weakest_skill}

WEEK 7-8: Advanced Concepts
- Task: Master advanced {weakest_skill} patterns in {industry_title}
- Resource: Professional development courses
- Project: Complex real-world {industry_key} project

WEEK 9-10: Real-World Application
- Task: Apply {weakest_skill} in professional {industry_title} context
- Resource: Industry case studies and mentorship
- Project: Portfolio-worthy project for {industry_title}

WEEK 11-12: Certification & Portfolio
- Task: Get certified in {weakest_skill} for {industry_title}
- Certification: Research top {industry_title} certifications
- Final Project: Capstone demonstrating all competencies

RECOMMENDED CERTIFICATIONS:
1. Industry-specific {weakest_skill} certification
2. Professional body accreditation for {industry_title}
3. Specialist qualification in {weakest_skill}"""
                    st.session_state.sprint_generated = True
                    st.session_state.completed_tasks = set()
                    st.rerun()
    
    with col_reset_sprint:
        if st.session_state.sprint_generated:
            if st.button("🔄 Reset Plan", use_container_width=True):
                st.session_state.sprint_generated = False
                st.session_state.sprint_plan = None
                st.session_state.completed_tasks = set()
                st.rerun()
    
    if st.session_state.sprint_generated and st.session_state.sprint_plan:
        st.markdown("---")
        st.markdown(f"### 📚 Your Personalized 90-Day Plan for {industry_title}")
        
        plan_lines = st.session_state.sprint_plan.split('\n')
        
        for i, line in enumerate(plan_lines):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('**WEEK') or line.startswith('WEEK'):
                current_week = line.replace('**', '').replace('*', '')
                st.markdown(f"#### 📅 {current_week}")
            elif line.startswith('- ') or line.startswith('• '):
                task_key = f"sprint_task_{i}"
                task_text = line[2:].strip()
                
                completed = st.checkbox(
                    task_text, 
                    key=task_key,
                    value=task_key in st.session_state.completed_tasks
                )
                if completed:
                    st.session_state.completed_tasks.add(task_key)
                elif task_key in st.session_state.completed_tasks:
                    st.session_state.completed_tasks.remove(task_key)
                    
            elif line.startswith('**RECOMMENDED') or line.startswith('RECOMMENDED'):
                st.markdown(f"#### 🏆 {line.replace('**', '').replace(':', '')}")
            elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                st.markdown(f"  {line}")
        
        total_tasks = len([l for l in plan_lines if l.strip().startswith('- ') or l.strip().startswith('• ')])
        completed_count = len(st.session_state.completed_tasks)
        
        if total_tasks > 0:
            progress = completed_count / total_tasks
            st.markdown("---")
            
            progress_color = ACCENT_GREEN if progress >= 0.7 else ACCENT_ORANGE if progress >= 0.3 else "#ef4444"
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0;">
                <h4 style="color: {progress_color}; margin: 0;">📊 Overall Progress: {completed_count}/{total_tasks} tasks completed ({int(progress*100)}%)</h4>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress)

    st.markdown("---")
    
    # SECTION 5: Skill Decay Warning System
    st.subheader("5️⃣ Skill Decay Warning System")
    st.caption(f"⚠️ Track {industry_title} skills that may need refreshing")
    
    skill_decay_data = [
        {
            "skill": weakest_skill, 
            "last_updated": "Recently analyzed", 
            "status": "current", 
            "decay_risk": "Low",
            "message": f"✅ Your {weakest_skill} knowledge is current based on recent analysis"
        },
        {
            "skill": decay_skills[0] if decay_skills else "Core Skills", 
            "last_updated": "3 months ago", 
            "status": "moderate", 
            "decay_risk": "Medium",
            "message": f"⏰ {decay_skills[0] if decay_skills else 'Core skills'} may need refreshing - industry standards update regularly"
        },
        {
            "skill": decay_skills[1] if len(decay_skills) > 1 else "Industry Knowledge", 
            "last_updated": "6+ months ago", 
            "status": "outdated", 
            "decay_risk": "High",
            "message": f"⚠️ {decay_skills[1] if len(decay_skills) > 1 else 'Industry knowledge'} may be outdated - new regulations/practices have emerged"
        },
    ]
    
    for skill_data in skill_decay_data:
        if skill_data['status'] == 'outdated':
            color = "#ef4444"
            icon = "🔴"
            bg_color = "rgba(239, 68, 68, 0.1)"
        elif skill_data['status'] == 'moderate':
            color = "#f59e0b"
            icon = "🟡"
            bg_color = "rgba(245, 158, 11, 0.1)"
        else:
            color = "#10b981"
            icon = "🟢"
            bg_color = "rgba(16, 185, 129, 0.1)"
        
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {color}; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
            <strong style="color: white;">{icon} {skill_data['skill']}</strong><br>
            <span style="color: #ccc; font-size: 0.9em;">{skill_data['message']}</span><br>
            <span style="color: {color}; font-size: 0.85em; margin-top: 5px; display: inline-block;">
                Decay Risk: <strong>{skill_data['decay_risk']}</strong> | Last Updated: {skill_data['last_updated']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander(f"📖 Suggested Refresh Courses for {industry_title}", expanded=False):
        st.markdown(f"""
        **🎓 Free Resources to Keep Your {industry_title} Skills Sharp:**
        
        **Coursera** - Audit courses for free
        - [Browse {industry_key} courses](https://www.coursera.org/courses?query={industry_key})
        
        **📺 YouTube Channels:**
        - Search for "{industry_key} training" and "{industry_key} skills"
        - Industry-specific tutorial channels
        
        **📚 Other Free Resources:**
        - LinkedIn Learning - Free with many library cards
        - Industry association websites and training
        - Government-funded training programs
        - Professional body CPD resources
        """)

    st.markdown("---")
    
    # SECTION 6: Skill Gap Analysis Summary
    st.subheader("6️⃣ Skill Gap Analysis Summary")
    st.caption(f"📊 Visual breakdown of your {industry_title} skill levels vs. target requirements")
    
    tech = report.get('tech_score', 50)
    skills_to_analyze = [
        {"name": industry_skills[0] if industry_skills else "Technical Foundation", "current": tech, "target": 90},
        {"name": industry_skills[1] if len(industry_skills) > 1 else "Leadership & Soft Skills", "current": report.get('leader_score', tech - 15), "target": 80},
        {"name": weakest_skill, "current": max(20, tech - 30), "target": 85},
        {"name": industry_skills[2] if len(industry_skills) > 2 else "Industry Knowledge", "current": min(90, tech + 5), "target": 85},
    ]
    
    for skill in skills_to_analyze:
        gap = skill['target'] - skill['current']
        
        if gap > 30:
            gap_color = "#ef4444"
            urgency = "🔴 High Urgency"
        elif gap > 15:
            gap_color = "#f59e0b"
            urgency = "🟡 Medium Urgency"
        elif gap > 0:
            gap_color = "#10b981"
            urgency = "🟢 Low Urgency"
        else:
            gap_color = "#10b981"
            urgency = "✅ On Target"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{skill['name']}**")
            st.progress(skill['current'] / 100)
        
        with col2:
            st.markdown(f"<span style='color: #888;'>Current: {skill['current']}%</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color: #888;'>Target: {skill['target']}%</span>", unsafe_allow_html=True)
        
        with col3:
            if gap > 0:
                st.markdown(f"<span style='color: {gap_color}; font-weight: bold;'>Gap: {gap}%</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: {gap_color}; font-size: 0.8em;'>{urgency}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #10b981; font-weight: bold;'>✅ Exceeds!</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: #10b981; font-size: 0.8em;'>+{abs(gap)}% above target</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.info(f"🔍 **Detected Industry:** {industry_title} | 💡 Upload a new CV anytime to refresh your analysis and track your progress!")

skill_migration_page()
