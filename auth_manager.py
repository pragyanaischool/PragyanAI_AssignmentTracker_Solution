import pandas as pd
import os

USER_DB = "user_db.xlsx"

def init_user_db():
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists(USER_DB):
        # Initial schema
        df = pd.DataFrame(columns=["Name", "USN", "Dept", "Password", "Role"])
        # Default Admin Account
        admin = {"Name": "System Admin", "USN": "ADMIN01", "Dept": "Admin", "Password": "admin123", "Role": "Admin"}
        pd.DataFrame([admin]).to_excel(USER_DB, index=False)

def verify_login(usn, pwd):
    if not os.path.exists(USER_DB): init_user_db()
    df = pd.read_excel(USER_DB)
    user = df[(df['USN'] == str(usn)) & (df['Password'] == str(pwd))]
    return user.iloc[0].to_dict() if not user.empty else None

def register_student(name, usn, dept, pwd):
    df = pd.read_excel(USER_DB)
    if str(usn) in df['USN'].astype(str).values:
        return False, "USN already registered!"
    new_user = {"Name": name, "USN": usn, "Dept": dept, "Password": pwd, "Role": "Student"}
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_excel(USER_DB, index=False)
    return True, "Registration successful! Please Login."
