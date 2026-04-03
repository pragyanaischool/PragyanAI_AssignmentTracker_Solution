import streamlit as st
import pandas as pd
import os
import plotly.express as px

def run_student_dashboard(usn, user_name):
    st.header(f"👋 Welcome Back, {user_name}!")
    
    # 1. Load Data Sources
    if not os.path.exists("data/student_db.xlsx"):
        st.info("🚀 You haven't started any assignments yet. Head over to 'Select Assignment' to begin!")
        return

    master_df = pd.read_excel("data/master_db.xlsx")
    student_df = pd.read_excel("data/student_db.xlsx")

    # 2. Filter data for the logged-in student
    my_submissions = student_df[student_df['USN'] == usn]
    
    # 3. Calculate "Pending" Assignments
    # We compare the Master list against the student's completed topics
    completed_topics = my_submissions['Topic'].unique()
    pending_df = master_df[~master_df['Topic'].isin(completed_topics)]

    # 4. Top-level Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Completed", len(my_submissions), delta=f"{len(my_submissions)} done")
    c2.metric("Pending", len(pending_df), delta=f"-{len(pending_df)}", delta_color="inverse")
    
    # Calculate Completion %
    completion_rate = (len(my_submissions) / len(master_df)) * 100 if len(master_df) > 0 else 0
    c3.metric("Completion Rate", f"{int(completion_rate)}%")

    st.divider()

    # 5. Visual Progress
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📝 Submission History")
        if not my_submissions.empty:
            # Clean up display
            display_df = my_submissions[['Subject', 'Topic', 'Type', 'Date', 'Status']].sort_values(by='Date', ascending=False)
            st.dataframe(display_df, use_container_width=True)
            
            # Download Personal Excel (Requirement: "Each Student One Excel")
            csv = my_submissions.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download My Assignment Report (CSV)",
                data=csv,
                file_name=f"{usn}_assignment_report.csv",
                mime='text/csv'
            )
        else:
            st.warning("No submissions recorded yet.")

    with col_right:
        st.subheader("⚠️ Pending Tasks")
        if not pending_df.empty:
            for _, row in pending_df.head(5).iterrows():
                st.warning(f"**{row['Subject']}**: {row['Topic']}")
            if len(pending_df) > 5:
                st.write(f"...and {len(pending_df)-5} more.")
        else:
            st.success("🎉 All caught up!")

    # 6. Performance Analysis (RAG Feedback)
    st.divider()
    st.subheader("🎯 Performance Insights")
    if not my_submissions.empty:
        # Simple Logic: If user has 'Coding' assignments, show a specific chart
        fig = px.pie(my_submissions, names='Subject', title="Distribution of Completed Subjects", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete an assignment to see your performance breakdown.")
