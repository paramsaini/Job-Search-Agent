import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- Configuration (Copied from main app for consistency) ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
GRID_CYAN = "rgba(0, 255, 255, 0.6)" 
GRID_ORANGE = "rgba(255, 140, 0, 0.6)" 

# --- Logic: Skill Migration Data Simulation ---

def get_skill_migration_data(report):
    """Generates the data for the migration map based on user's current scores."""
    
    # 1. User's Current Position (from Gemini report)
    user_data = {
        'X_Tech': [report.get('tech_score', 50)],
        'Y_Leader': [report.get('leader_score', 50)],
        'Type': ['Your Current Profile'],
        'Name': ['You']
    }
    
    # 2. Hardcoded Target Roles (Simulated Skill Requirements)
    # These represent the optimal skill mix for pivot roles.
    target_data = [
        # Pivot 1: High Tech / Medium Leadership
        {'X_Tech': 85, 'Y_Leader': 65, 'Type': 'Target Cluster: Specialist Architect', 'Name': 'Role: Solution Architect'},
        # Pivot 2: Medium Tech / High Leadership
        {'X_Tech': 65, 'Y_Leader': 85, 'Type': 'Target Cluster: Management Track', 'Name': 'Role: Product Lead'},
        # Pivot 3: Balanced/High Tech
        {'X_Tech': 75, 'Y_Leader': 75, 'Type': 'Target Cluster: Domain Expert/Consultant', 'Name': 'Role: Industry Consultant'},
    ]
    
    df_user = pd.DataFrame(user_data)
    df_targets = pd.DataFrame(target_data)
    
    # 3. Calculate Gap Metric (Manhattan Distance to Target)
    def calculate_gap(row):
        user_x = df_user['X_Tech'].iloc[0]
        user_y = df_user['Y_Leader'].iloc[0]
        # Manhattan Distance: |x1 - x2| + |y1 - y2|
        distance = abs(row['X_Tech'] - user_x) + abs(row['Y_Leader'] - user_y)
        return distance
    
    df_targets['Gap_Score'] = df_targets.apply(calculate_gap, axis=1)
    
    df = pd.concat([df_user, df_targets], ignore_index=True)
    return df

# --- Page Render ---

def skill_migration_page():
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🌍 Role-to-Role Skill Migration Map</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: {ACCENT_CYAN}; font-size: 1.1em; font-weight: 500; text-shadow: 0 0 2px {ACCENT_CYAN}40;">
        **Niche Solution: Transition Uncertainty.** Visualize your current skill position (Tech vs. Leadership) relative to three key career pivot targets. Find the shortest path to your next role.
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    report = st.session_state.get('skill_gap_report', None)

    if not report or report.get('error'):
        st.error("⚠️ **PREREQUISITE:** Please run a full analysis on the Home Page first to load your skill scores.")
        return

    df_map = get_skill_migration_data(report)
    
    # Find the closest target to the user's profile
    closest_target = df_map[df_map['Type'].str.contains('Target')].sort_values(by='Gap_Score').iloc[0]
    
    st.subheader("1. Dynamic Skill Map Visualization")
    
    # --- Plotly Scatter Chart (2D) ---
    fig = px.scatter(
        df_map, 
        x='X_Tech', 
        y='Y_Leader', 
        color='Type', 
        text='Name',
        size=df_map['Type'].apply(lambda x: 15 if 'Current' in x else 10),
        color_discrete_map={'Your Current Profile': ACCENT_ORANGE, 
                            'Target Cluster: Specialist Architect': '#8888FF',
                            'Target Cluster: Management Track': ACCENT_GREEN,
                            'Target Cluster: Domain Expert/Consultant': ACCENT_CYAN},
        title="Technical Depth vs. Leadership Potential",
        height=600
    )

    # Draw the shortest migration path (from user to closest target)
    user_x, user_y = df_map[df_map['Type'] == 'Your Current Profile'][['X_Tech', 'Y_Leader']].iloc[0].values
    
    fig.add_shape(
        type='line',
        x0=user_x, y0=user_y,
        x1=closest_target['X_Tech'], y1=closest_target['Y_Leader'],
        line=dict(color=ACCENT_ORANGE, width=3, dash='dot')
    )
    
    fig.update_traces(marker=dict(size=20, line=dict(width=2, color='white')), selector=dict(mode='markers+text'))

    fig.update_layout(
        plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK, font=dict(color="white"),
        xaxis=dict(title="Technical Depth (%)", range=[40, 100], gridcolor=GRID_CYAN),
        yaxis=dict(title="Leadership Potential (%)", range=[40, 100], gridcolor=GRID_ORANGE)
    )
    st.plotly_chart(fig, use_container_width=True) 

    st.markdown("---")
    
    # --- Actionable Summary ---
    st.subheader("2. Optimized Migration Strategy")
    st.markdown(f"""
    <div style='background-color: {ACCENT_ORANGE}10; padding: 15px; border-radius: 8px; border-left: 5px solid {ACCENT_ORANGE};'>
        <p style='color: {ACCENT_ORANGE}; font-size: 1.1rem; font-weight: bold; margin: 0;'>
            🎯 Your Highest Priority Pivot Target is: {closest_target['Name']} ({closest_target['Type'].split(': ')[1]})
        </p>
        <p style='color: #ccc; margin-top: 10px;'>
            The closest path requires mitigating a **Total Skill Gap** of **{closest_target['Gap_Score']:.1f} points**.
            The current focus should be on shifting your skill profile towards **{closest_target['Name']}** by prioritizing skills in the area(s) where your current score is lower than the target cluster average.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("The full detailed action plan is available on the Home Page and in the Predictive Skill Health Score card.")

skill_migration_page()
