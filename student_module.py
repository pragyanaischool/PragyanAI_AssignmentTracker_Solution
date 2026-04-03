import streamlit as st
import pandas as pd
from datetime import datetime

def show_student(user, rag):
    mode = st.sidebar.radio("Menu", ["Take Assignment", "My Analysis"])
    m_df = pd.read_excel("data/master_db.xlsx")
    s_df = pd.read_excel("data/student_db.xlsx")

    if mode == "Take Assignment":
        # Selection Logic
        subj = st.selectbox("Subject", m_df['Subject'].unique())
        topic = st.selectbox("Topic", m_df[m_df['Subject']==subj]['Topic'])
        a_type = st.selectbox("Type", ["MCQ", "Code", "Short"])

        if st.button("Start Test"):
            link = m_df[m_df['Topic']==topic]['Doc Link / Content'].values[0]
            vs = rag.process_doc(link)
            st.session_state.qs = rag.get_questions(vs, topic, a_type)
            st.session_state.q_idx = 0

        # One by One Interface
        if 'qs' in st.session_state and st.session_state.qs:
            curr = st.session_state.q_idx
            q = st.session_state.qs[curr]
            st.subheader(f"Q{curr+1}: {q['question']}")
            with st.expander("Hint"): st.write(q['hint'])
            st.text_area("Answer", key=f"ans_{curr}")
            
            c1, c2 = st.columns(2)
            if c1.button("Prev") and curr > 0: st.session_state.q_idx -= 1; st.rerun()
            if c2.button("Next") and curr < len(st.session_state.qs)-1: st.session_state.q_idx += 1; st.rerun()
            
            if curr == len(st.session_state.qs)-1 and st.button("Submit"):
                new_data = {"USN": user['USN'], "Name": user['Name'], "Subject": subj, "Topic": topic, "Status": "Done", "Date": datetime.now()}
                pd.concat([s_df, pd.DataFrame([new_data])]).to_excel("data/student_db.xlsx", index=False)
                st.success("Submitted!")

    else:
        # Review Pending Logic
        done = s_df[s_df['USN']==user['USN']]['Topic'].tolist()
        pending = m_df[~m_df['Topic'].isin(done)]
        st.metric("Pending Assignments", len(pending))
        st.dataframe(pending[['Subject', 'Topic']])
