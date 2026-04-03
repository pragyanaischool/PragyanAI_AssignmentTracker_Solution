import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from rag_engine import AssignmentRAG

# --- Configuration ---
st.set_page_config(page_title="PragyanAI Assignment Tracker", layout="wide")
st.image('PragyanAI_Transperent.png')
# --- Constants & DB Initialization ---
USER_DB = "user_db.xlsx"
MASTER_DB = "PragyanAI - Assignments - Track.xlsx"
STUDENT_DB = "student_db.xlsx"

def init_dbs():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Initialize User DB with Default Admin
    if not os.path.exists(USER_DB):
        df = pd.DataFrame(columns=["Name", "USN", "Dept", "Password", "Role"])
        admin_user = {"Name": "System Admin", "USN": "ADMIN01", "Dept": "Admin", "Password": "admin123", "Role": "Admin"}
        pd.DataFrame([admin_user]).to_excel(USER_DB, index=False)
        
    # Initialize Student Progress DB
    if not os.path.exists(STUDENT_DB):
        pd.DataFrame(columns=["USN", "Name", "Subject", "Topic", "Type", "Status", "Date"]).to_excel(STUDENT_DB, index=False)

init_dbs()

# --- Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'q_idx' not in st.session_state:
    st.session_state.q_idx = 0

# --- Authentication Logic ---
def login_user(usn, pwd):
    df = pd.read_excel(USER_DB)
    user = df[(df['USN'] == usn) & (df['Password'] == pwd)]
    return user.iloc[0] if not user.empty else None

def register_student(name, usn, dept, pwd):
    df = pd.read_excel(USER_DB)
    if usn in df['USN'].values:
        return False, "USN already registered."
    new_user = {"Name": name, "USN": usn, "Dept": dept, "Password": pwd, "Role": "Student"}
    pd.concat([df, pd.DataFrame([new_user])], ignore_index=True).to_excel(USER_DB, index=False)
    return True, "Registration Successful!"

# --- UI: LOGIN / REGISTRATION GATE ---
if not st.session_state.logged_in:
    st.title("🚀 PragyanAI Assignment Tracker")
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        u_id = st.text_input("USN / Admin ID")
        u_pw = st.text_input("Password", type="password")
        if st.button("Login"):
            user_data = login_user(u_id, u_pw)
            if user_data is not None:
                st.session_state.logged_in = True
                st.session_state.user = user_data
                st.rerun()
            else:
                st.error("Invalid ID or Password")

    with auth_tab2:
        reg_name = st.text_input("Full Name")
        reg_usn = st.text_input("New USN")
        reg_dept = st.selectbox("Department", ["CS", "IS", "EC", "ME"])
        reg_pw = st.text_input("Create Password", type="password")
        if st.button("Sign Up"):
            success, msg = register_student(reg_name, reg_usn, reg_dept, reg_pw)
            if success: st.success(msg)
            else: st.error(msg)

else:
    # --- LOGGED IN AREA ---
    user = st.session_state.user
    st.sidebar.title(f"Welcome, {user['Name']}")
    st.sidebar.info(f"Role: {user['Role']} | Dept: {user['Dept']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.questions = []
        st.rerun()

    # --- ADMIN VIEW ---
    if user['Role'] == "Admin":
        st.header("📊 Admin Dashboard")
        m_df = pd.read_excel(MASTER_DB)
        s_df = pd.read_excel(STUDENT_DB)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Assignments", len(m_df))
        c2.metric("Total Submissions", len(s_df))
        c3.metric("Unique Students", s_df['USN'].nunique())
        
        st.subheader("All Submissions")
        st.dataframe(s_df, use_container_width=True)
        
        # Export logic
        target_usn = st.selectbox("Extract Report for Student (USN)", s_df['USN'].unique())
        if st.button("Download Student Excel"):
            report = s_df[s_df['USN'] == target_usn]
            report.to_excel(f"data/{target_usn}_report.xlsx", index=False)
            st.success(f"Report for {target_usn} generated in /data folder.")

    # --- STUDENT VIEW ---
    else:
        menu = ["Assignment Hub", "My Progress"]
        choice = st.sidebar.radio("Navigate", menu)

        if choice == "Assignment Hub":
            st.header("📝 Take Assignment")
            m_df = pd.read_excel(MASTER_DB)
            
            col1, col2 = st.columns(2)
            with col1:
                subj = st.selectbox("Subject", m_df['Subject'].unique())
                topic = st.selectbox("Topic", m_df[m_df['Subject'] == subj]['Topic'].unique())
            with col2:
                a_type = st.selectbox("Type", ["MCQ", "Short Answer", "Coding", "Project"])
            
            if st.button("Start Agentic Test"):
                with st.spinner("Groq Agent is parsing document..."):
                    doc_link = m_df[(m_df['Topic'] == topic)]['Doc Link / Content'].values[0]
                    rag = AssignmentRAG(os.getenv("GROQ_API_KEY"))
                    vstore = rag.process_document(doc_link)
                    st.session_state.questions = rag.get_structured_questions(vstore, topic, a_type)
                    st.session_state.q_idx = 0
                    st.success("Test Ready! Scroll down.")

            # --- One-by-One Question Interface ---
            if st.session_state.questions:
                q_data = st.session_state.questions
                idx = st.session_state.q_idx
                
                st.divider()
                st.subheader(f"Question {idx+1} of {len(q_data)}")
                st.info(q_data[idx]['question'])
                
                with st.expander("💡 Hint"):
                    st.write(q_data[idx]['hint'])
                with st.expander("📝 Example"):
                    st.code(q_data[idx]['example'])
                
                ans = st.text_area("Your Answer", key=f"ans_{idx}")
                
                b1, b2, b3 = st.columns([1,1,2])
                if b1.button("⬅️ Back") and idx > 0:
                    st.session_state.q_idx -= 1
                    st.rerun()
                if b2.button("Next ➡️") and idx < len(q_data) - 1:
                    st.session_state.q_idx += 1
                    st.rerun()
                
                if idx == len(q_data) - 1:
                    if st.button("🚀 Submit Final Assignment"):
                        # Save to Student DB
                        s_df = pd.read_excel(STUDENT_DB)
                        new_sub = {
                            "USN": user['USN'], "Name": user['Name'], "Subject": subj,
                            "Topic": topic, "Type": a_type, "Status": "Submitted",
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        pd.concat([s_df, pd.DataFrame([new_sub])], ignore_index=True).to_excel(STUDENT_DB, index=False)
                        st.balloons()
                        st.success("Assignment Submitted Successfully!")
                        st.session_state.questions = []

        elif choice == "My Progress":
            st.header("📊 My Performance")
            s_df = pd.read_excel(STUDENT_DB)
            my_data = s_df[s_df['USN'] == user['USN']]
            
            st.metric("Total Completed", len(my_data))
            st.dataframe(my_data, use_container_width=True)
            
            csv = my_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download My Report", csv, f"{user['USN']}_report.csv", "text/csv")
