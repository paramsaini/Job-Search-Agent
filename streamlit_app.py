# --- Visualization Render (IMPROVED DESIGN) ---
def render_strategy_visualizations(report):
    """Renders the Strategy Funnel and Progress Meter Dashboard using dense data presentation."""
    
    st.header("🧠 Strategic Visualization Suite")
    
    score = report.get('predictive_score', 0)
    score_float = float(score) / 100.0 if score is not None else 0.0
    
    # --- 1. KPI Metrics (Denser presentation with st.metric) ---
    st.subheader("Key Predictive Metrics")
    
    col_kpi_1, col_kpi_2, col_kpi_3 = st.columns(3)
    
    # KPI 1: Overall Match Score
    with col_kpi_1:
        # Determine status for st.metric delta color
        if score >= 85:
            score_status = "normal"
            score_color = "#10B981" # Green
        elif score >= 70:
            score_status = "off"
            score_color = "#F59E0B" # Yellow
        else:
            score_status = "inverse"
            score_color = "#FF8C00" # Orange
        
        st.markdown(f"**Overall Predictive Match**")
        st.metric(label="Score", value=f"{score}%", delta_color=score_status)
        st.progress(score_float)
    
    # KPI 2: Weakest Link / Mitigation Focus
    with col_kpi_2:
        weak_link = report.get('weakest_link_skill', 'N/A')
        st.markdown(f"**Targeted Mitigation Focus**")
        st.warning(f"**{weak_link}**")
        st.caption("*Highest priority for CV optimization.*")
        
    # KPI 3: Next Action Step
    with col_kpi_3:
        st.markdown(f"**Immediate Tactical Goal**")
        st.success(f"**Optimize CV in Compiler**")
        st.caption("*Test against a specific Job Description.*")

    st.markdown("---")

    # --- 2. Deep Dive: Predictive Skill Breakdown (More dense information) ---
    st.subheader("Deep Dive: Capability Breakdown")
    
    # Extract sub-scores safely, default to 0 if missing
    tech_score = report.get('tech_score', 0) / 100
    leader_score = report.get('leader_score', 0) / 100
    domain_score = report.get('domain_score', 0) / 100
    
    st.markdown("**Technical Depth (Hard Skills)**")
    st.progress(tech_score, text=f"{int(tech_score * 100)}%")

    st.markdown("**Leadership Potential (Soft Skills/Management)**")
    st.progress(leader_score, text=f"{int(leader_score * 100)}%")

    st.markdown("**Domain Expertise (Industry Specific)**")
    st.progress(domain_score, text=f"{int(domain_score * 100)}%")
    
    st.markdown("---")
    
    # --- 3. Action Strategy Pipeline (Restored structure) ---
    st.subheader("Action Strategy Pipeline")
    
    col_flow_1, col_flow_2, col_flow_3 = st.columns(3)
    
    with col_flow_1:
        st.container(border=True, height=150).markdown(f"**1. ANALYSIS**\n\nCV scanned against 1,000 elite profiles. Match Score established.")

    with col_flow_2:
        st.container(border=True, height=150).markdown(f"**2. OPTIMIZATION**\n\nUse Compiler to eliminate the Weakest Link and pass the ATS/Recruiter filters.")

    with col_flow_3:
        st.container(border=True, height=150).markdown(f"**3. EXECUTION**\n\nTarget employers and initiate the Visa Action Plan (see report below).")
