import pandas as pd
import os
import hashlib

USER_DB = "data/user_db.xlsx"

def init_user_db():
    if not os.path.exists(USER_DB):
        df = pd.DataFrame(columns=["Name", "USN", "Dept", "Password", "Role"])
        # Default Admin Account
        admin_row = pd.DataFrame([{
            "Name": "System Admin", 
            "USN": "ADMIN01", 
            "Dept": "Admin", 
            "Password": "admin123", # In production, use werkzeug.security
            "Role": "Admin"
        }])
        df = pd.concat([df, admin_row], ignore_index=True)
        df.to_excel(USER_DB, index=False)

def hash_pw(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_user(usn, password):
    df = pd.read_excel(USER_DB)
    user = df[df['USN'] == usn]
    if not user.empty:
        if str(user.iloc[0]['Password']) == password: # Simple check for this demo
            return user.iloc[0]
    return None

def register_student(name, usn, dept, password):
    df = pd.read_excel(USER_DB)
    if usn in df['USN'].values:
        return False, "USN already exists!"
    
    new_user = pd.DataFrame([{
        "Name": name, "USN": usn, "Dept": dept, 
        "Password": password, "Role": "Student"
    }])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_excel(USER_DB, index=False)
    return True, "Registration Successful!"
