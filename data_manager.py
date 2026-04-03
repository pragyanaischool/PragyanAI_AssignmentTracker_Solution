import pandas as pd
import os

def load_df(file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame()
    return pd.read_excel(file_path)

def save_df(df, file_path):
    df.to_excel(file_path, index=False)

def get_pending_tasks(usn):
    m_df = load_df("data/master_db.xlsx")
    s_df = load_df("data/student_db.xlsx")
    if s_df.empty: return m_df
    
    done_topics = s_df[s_df['USN'] == usn]['Topic'].tolist()
    return m_df[~m_df['Topic'].isin(done_topics)]
