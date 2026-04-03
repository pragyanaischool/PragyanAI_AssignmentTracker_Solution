import streamlit as st
import pandas as pd
import plotly.express as px

def show_admin():
    st.header("👨‍🏫 Admin Dashboard")
    s_df = pd.read_excel("data/student_db.xlsx")
    m_df = pd.read_excel("data/master_db.xlsx")

    # Metrics
    c1, c2 = st.columns(2)
    c1.metric("Total Submissions", len(s_df))
    c2.metric("Active Students", s_df['USN'].nunique())

    # Heatmap
    st.subheader("Submission Analysis")
    pivot = s_df.pivot_table(index='Name', columns='Subject', values='Status', aggfunc='count').fillna(0)
    st.dataframe(pivot.style.background_gradient(cmap="Greens"))

    # Excel Extraction (Requirement: Each Student One Excel)
    st.subheader("📥 Extract Student Report")
    target = st.selectbox("Select USN", s_df['USN'].unique())
    if st.button("Generate Excel"):
        report = s_df[s_df['USN'] == target]
        report.to_excel(f"data/{target}_report.xlsx", index=False)
        st.success(f"Report for {target} created in /data folder.")
