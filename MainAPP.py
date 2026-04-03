import streamlit as st
import pandas as pd
import os
from rag_engine import AssignmentRAG
from datetime import datetime

# --- Configuration & Styling ---
st.set_page_config(page_title="Agentic Assignment Portal", layout="wide")
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007BFF; color: white; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #007BFF , #00CCFF); }
    </style>
    """, unsafe_allow_html=True)
st.image('PragyanAI_Transperent.png')
# --- Session State Initialization ---
if 'rag' not in st.session_state: st.session_state.rag = None
if 'questions' not in st.session_state: st.session_state.questions = []
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
if 'answers' not in st.session_state: st.session_state.answers = {}

# --- Helper Functions ---
def load_master_data():
    # Ensure this file exists in your directory
    return pd.read_excel("data/master_db.xlsx")

# --- Sidebar: User Authentication ---
st.sidebar.title("🎓 Student Portal")
user_name = st.sidebar.text_input("Full Name")
usn = st.sidebar.text_input("USN / ID")
dept = st.sidebar.selectbox("Department", ["CS", "IS", "EC", "ME"])

# --- Main Navigation ---
tabs = ["Select Assignment", "Take Test", "Performance Analytics"]
choice = st.sidebar.radio("Navigation", tabs)

master_df = load_master_data()

# --- 1. SELECT ASSIGNMENT ---
if choice == "Select Assignment":
    st.header("📋 Initialize Your Assignment")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox("Select Subject", master_df['Subject'].unique())
        sub_df = master_df[master_df['Subject'] == subject]
        topic = st.selectbox("Select Topic", sub_df['Topic'].unique())
    
    with col2:
        a_type = st.selectbox("Assignment Type", ["MCQ", "Short Answer", "Coding", "Project"])
        doc_link = sub_df[sub_df['Topic'] == topic]['Doc Link'].values[0]

    if st.button("Generate Questions via Groq Agent"):
        with st.spinner("Agent is analyzing document and generating questions..."):
            # Initialize RAG Engine
            api_key = os.getenv("GROQ_API_KEY") # Ensure this is in your .env
            st.session_state.rag = AssignmentRAG(api_key)
            
            # Process Doc & Generate
            vstore = st.session_state.rag.process_document(doc_link)
            st.session_state.questions = st.session_state.rag.get_structured_questions(vstore, topic, a_type)
            st.session_state.q_idx = 0
            st.success("Questions generated! Please head to 'Take Test'.")

# --- 2. TAKE TEST (One by One) ---
elif choice == "Take Test":
    if not st.session_state.questions:
        st.warning("⚠️ No assignment selected. Please go to 'Select Assignment' first.")
    else:
        questions = st.session_state.questions
        curr = st.session_state.q_idx
        
        # Progress Bar
        progress = (curr + 1) / len(questions)
        st.progress(progress)
        st.write(f"**Question {curr + 1} of {len(questions)}**")
        
        # Question Display
        st.subheader(questions[curr]['question'])
        
        # Hint & Example Section
        col_h, col_e = st.columns(2)
        with col_h:
            with st.expander("💡 View Hint"):
                st.info(questions[curr]['hint'])
        with col_e:
            with st.expander("📝 View Example"):
                st.code(questions[curr]['example'])

        # Answer Input
        st.session_state.answers[curr] = st.text_area("Your Response", value=st.session_state.answers.get(curr, ""), height=150)

        # Navigation Buttons
        nb_col1, nb_col2, nb_col3 = st.columns([1,1,2])
        if nb_col1.button("⬅️ Previous") and curr > 0:
            st.session_state.q_idx -= 1
            st.rerun()
        
        if nb_col2.button("Next ➡️") and curr < len(questions) - 1:
            st.session_state.q_idx += 1
            st.rerun()
            
        if curr == len(questions) - 1:
            st.divider()
            st.subheader("📤 Final Submission")
            uploaded_file = st.file_uploader("Upload Completed Document (Optional)")
            
            if st.button("✅ Submit Assignment"):
                submission_data = {
                    "USN": usn, "Name": user_name, "Subject": subject, 
                    "Topic": topic, "Type": a_type, "Status": "Submitted",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Doc_Link": doc_link
                }
                st.session_state.rag.update_student_excel(submission_data)
                st.balloons()
                st.success("Assignment Submitted and Recorded in Excel!")

# --- 3. PERFORMANCE ANALYTICS ---
elif choice == "Performance Analytics":
    st.header("📊 Submission Review")
    if os.path.exists("data/student_db.xlsx"):
        student_df = pd.read_excel("data/student_db.xlsx")
        
        # Filter for current student
        my_df = student_df[student_df['USN'] == usn]
        
        st.subheader(f"Summary for {user_name}")
        c1, c2 = st.columns(2)
        c1.metric("Total Submitted", len(my_df))
        c2.metric("Pending (Estimated)", len(master_df) - len(my_df))
        
        st.dataframe(my_df, use_container_width=True)
        
        # CSV Download for 'One Student One Excel'
        csv = my_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download My Progress Report", data=csv, file_name=f"{usn}_progress.csv")
    else:
        st.info("No records found yet.")
