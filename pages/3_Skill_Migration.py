import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# --- Configuration ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
GRID_CYAN = "rgba(0, 255, 255, 0.6)" 
GRID_ORANGE = "rgba(255, 140, 0, 0.6)" 

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

supabase = init_supabase()

# --- Logic: Data Retrieval & Simulation ---

def get_skill_migration_data(report):
    """Generates the data for the migration map based on user's scores."""
    user_data = {
        'X_Tech': [report.get('tech_score', 50)],
        'Y_Leader': [report.get('leader_score', 50)],
        'Type': ['Your Current Profile'],
        'Name': ['You']
    }
    
    target_data = [
        {'X_Tech': 85, 'Y_Leader': 65, 'Type': 'Target Cluster: Specialist Architect', 'Name': 'Role: Solution Architect'},
        {'X_Tech': 65, 'Y_Leader': 85, 'Type': 'Target Cluster: Management Track', 'Name': 'Role: Product Lead'},
        {'X_Tech': 75, 'Y_Leader': 75, 'Type': 'Target Cluster: Domain Expert/Consultant', 'Name': 'Role: Industry Consultant'},
    ]
    
    df_user = pd.DataFrame(user_data)
    df_targets = pd.DataFrame(target_data)
    
    def calculate_gap(row):
        user_x = df_user['X_Tech'].iloc[0]
        user_y = df_user['Y_Leader'].iloc[0]
        return abs(row['X_Tech'] - user_x) + abs(row['Y_Leader'] - user_y)
    
    df_targets['Gap_Score'] = df_targets.apply(calculate_gap, axis=1)
    return pd.concat([df_user, df_targets], ignore_index=True)

def fetch_latest_report():
    """Fetches the most recent analysis from Supabase if session is empty."""
    user_id = st.session_state.get('user_id')
    if not user_id or not supabase: return None
    
    try:
        response = supabase.table("analyses").select("report_json")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        
        if response.data:
            return response.data[0]['report_json']
    except Exception as e:
        st.error(f"Database Error: {e}")
    return None

# --- Page Render ---

def skill_migration_page():
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🌍 Aequor: Skill Migration Map</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # 1. Auth Check
    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to view your skill migration map.")
        return

    # 2. Data Loading Strategy (Session -> DB -> Fail)
    report = st.session_state.get('skill_gap_report')
    
    if not report:
        with st.spinner("Fetching latest profile data from cloud..."):
            report = fetch_latest_report()
            if report:
                st.session_state['skill_gap_report'] = report # Cache it back
    
    if not report:
        st.info("👋 No analysis found. Go to the **Dashboard** and run your first strategy analysis to generate this map.")
        return

    # 3. Visualization
    df_map = get_skill_migration_data(report)
    closest_target = df_map[df_map['Type'].str.contains('Target')].sort_values(by='Gap_Score').iloc[0]
    
    st.subheader("1. Dynamic Skill Map")
    
    fig = px.scatter(
        df_map, x='X_Tech', y='Y_Leader', color='Type', text='Name',
        size=df_map['Type'].apply(lambda x: 15 if 'Current' in x else 10),
        color_discrete_map={'Your Current Profile': ACCENT_ORANGE, 
                            'Target Cluster: Specialist Architect': '#8888FF',
                            'Target Cluster: Management Track': ACCENT_GREEN,
                            'Target Cluster: Domain Expert/Consultant': ACCENT_CYAN},
        height=600
    )

    user_x, user_y = df_map[df_map['Type'] == 'Your Current Profile'][['X_Tech', 'Y_Leader']].iloc[0].values
    fig.add_shape(
        type='line', x0=user_x, y0=user_y, x1=closest_target['X_Tech'], y1=closest_target['Y_Leader'],
        line=dict(color=ACCENT_ORANGE, width=3, dash='dot')
    )
    fig.update_traces(marker=dict(line=dict(width=2, color='white')), selector=dict(mode='markers+text'))
    fig.update_layout(
        plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK, font=dict(color="white"),
        xaxis=dict(title="Technical Depth (%)", range=[40, 100], gridcolor=GRID_CYAN),
        yaxis=dict(title="Leadership Potential (%)", range=[40, 100], gridcolor=GRID_ORANGE)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("2. Strategic Pivot")
    st.success(f"🎯 **Target:** {closest_target['Name']} (Gap: {closest_target['Gap_Score']:.1f})")
    st.info(f"**Mitigation Focus:** {report.get('weakest_link_skill', 'N/A')}")

skill_migration_page()
