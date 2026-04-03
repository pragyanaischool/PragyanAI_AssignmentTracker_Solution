import streamlit as st
import pandas as pd
import plotly.express as px
import os

def run_admin_dashboard():
    st.title("Admin Command Center")
    
    # 1. Load Data
    if not os.path.exists("data/master_db.xlsx") or not os.path.exists("data/student_db.xlsx"):
        st.error("Missing Data Files! Please ensure master_db.xlsx and student_db.xlsx exist in /data.")
        return

    master_df = pd.read_excel("data/master_db.xlsx")
    student_df = pd.read_excel("data/student_db.xlsx")

    # 2. High-Level Metrics
    total_assignments_available = len(master_df)
    unique_students = student_df['USN'].nunique()
    total_submissions = len(student_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Course Assignments", total_assignments_available)
    col2.metric("Active Students", unique_students)
    col3.metric("Total Submissions", total_submissions)

    st.divider()

    # 3. Submission Analytics (Pending vs Completed)
    st.subheader("📈 Global Submission Trends")
    
    # Grouping by Subject to see completion rates
    sub_stats = student_df.groupby('Subject').size().reset_index(name='Completed')
    fig = px.bar(sub_stats, x='Subject', y='Completed', title="Submissions per Subject", color='Completed')
    st.plotly_chart(fig, use_container_width=True)

    # 4. Student-Wise Detailed Report (The "One Student One Excel" Logic)
    st.subheader("🔍 Individual Student Drill-down")
    
    selected_student = st.selectbox("Select Student by USN", student_df['USN'].unique())
    
    if selected_student:
        personal_report = student_df[student_df['USN'] == selected_student]
        
        # Calculate Pending for this specific student
        # We compare what they've done vs what is in the master list
        completed_topics = personal_report['Topic'].tolist()
        pending_df = master_df[~master_df['Topic'].isin(completed_topics)]

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Completed Assignments**")
            st.dataframe(personal_report[['Topic', 'Date', 'Type']])
        with c2:
            st.write("**Pending Assignments**")
            st.dataframe(pending_df[['Topic', 'Subject']])

        # Export Feature
        st.download_button(
            label="📥 Export Student Excel Report",
            data=personal_report.to_csv(index=False).encode('utf-8'),
            file_name=f"Report_{selected_student}.csv",
            mime='text/csv'
        )

    # 5. Bulk Extract
    st.divider()
    if st.button("Generate Master Completion Report"):
        # Merging data to show exactly who is missing what
        st.write("Generating cross-reference report...")
        # This creates a matrix of Student vs Assignment completion
        report = student_df.pivot_table(index='Name', columns='Subject', values='Status', aggfunc='count').fillna(0)
        st.dataframe(report)

if __name__ == "__main__":
    # If running as a standalone admin app
    run_admin_dashboard()
