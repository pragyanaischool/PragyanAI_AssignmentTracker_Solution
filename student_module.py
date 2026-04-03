import streamlit as st
from datetime import datetime
from data_manager import load_df, save_df, get_pending_tasks

def show_student(user, rag):
    st.title(f"👋 Student Dashboard: {user['Name']}")
    
    s_tab = st.tabs(["Take Test", "Analysis & Progress"])

    with s_tab[0]:
        st.subheader("🎯 Select and Start Test")
        m_df = load_df("data/master_db.xlsx")
        
        # Selection UI
        subj = st.selectbox("Subject", m_df['Subject'].unique())
        topic = st.selectbox("Topic", m_df[m_df['Subject']==subj]['Topic'])
        
        if st.button("Generate & Start Test"):
            link = m_df[m_df['Topic']==topic]['Doc Link / Content'].values[0]
            with st.spinner("Agent fetching content..."):
                vs = rag.process_doc(link)
                st.session_state.qs = rag.get_questions(vs, topic, "Mixed Type")
                st.session_state.q_idx = 0
                st.session_state.active_test = topic
                st.rerun()

        # Navigation logic (Standard Forward/Backward)
        if 'qs' in st.session_state:
            # ... (Existing One-by-One UI Code) ...
            if st.button("Final Submit"):
                s_df = load_df("data/student_db.xlsx")
                new_entry = {
                    "USN": user['USN'], "Name": user['Name'], 
                    "Subject": subj, "Topic": topic, 
                    "Status": "Submitted", "Date": datetime.now()
                }
                save_df(pd.concat([s_df, pd.DataFrame([new_entry])]), "data/student_db.xlsx")
                st.success("Test Submitted!")
                del st.session_state.qs

    with s_tab[1]:
        st.subheader("📈 My Personal Analysis")
        pending = get_pending_tasks(user['USN'])
        s_df = load_df("data/student_db.xlsx")
        my_done = s_df[s_df['USN'] == user['USN']]

        c1, c2 = st.columns(2)
        c1.metric("Tests Completed", len(my_done))
        c2.metric("Tests Pending", len(pending))

        st.write("### ⏳ Remaining Assignments")
        st.dataframe(pending[['Subject', 'Topic']], use_container_width=True)
