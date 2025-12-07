# --- Inside compiler_page() function in pages/4_CV_Compiler.py ---

# ... (Previous code ending the "Finalize & Log Application" section)

    st.markdown("---")
    st.subheader("4. Application History Ledger")
    
    # Display Ledger and allow user to select an index for updating
    if not st.session_state['ledger_data'].empty:
        df_ledger = st.session_state['ledger_data'].copy()
        df_ledger.index.name = 'Index'
        
        st.dataframe(df_ledger.style.applymap(
            lambda x: f'background-color: {ACCENT_GREEN}30' if x == 'Interview' or x == 'Offer' else (
                      f'background-color: {ACCENT_ORANGE}30' if x == 'Rejected' else ''))
                      .format({"Compliance": "{:.0f}%", "Clarity": "{:.0f}%"}), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Update Application Outcome")
        
        col_update_1, col_update_2, col_update_3 = st.columns([1, 1, 2])
        
        # 1. Select Index to Update
        entry_indices = df_ledger.index.tolist()
        selected_index = col_update_1.selectbox("Select Entry Index to Update", entry_indices)
        
        # 2. Select New Outcome
        new_outcome = col_update_2.selectbox("Set Final Outcome", 
                                            ['Pending', 'Interview', 'Rejected', 'Offer'])
        
        # 3. Update Button
        if col_update_3.button("Apply Outcome Change", type="secondary", use_container_width=True):
            st.session_state['ledger_data'].loc[selected_index, 'Outcome'] = new_outcome
            st.success(f"Outcome for Index {selected_index} updated to {new_outcome}.")
            st.rerun() # Rerun to refresh the dataframe
