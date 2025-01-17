import streamlit as st
import mysql.connector
import hashlib
from datetime import datetime
import re

# Database connection function
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="jay2416",
        database="currencywizard"
    )

def is_valid_email(email):
    # Regular expression for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

# Password validation function
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# Login function
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                      (username, password))
        user = cursor.fetchone()
        
        if user:
            # Update last login time
            cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", 
                         (datetime.now(), user['user_id']))
            conn.commit()
            return user
        return None
    finally:
        cursor.close()
        conn.close()

# Registration function
def register_user(username, email, password, full_name):
    if not is_valid_password(password):
        return False, "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, full_name) 
            VALUES (%s, %s, %s, %s)
        """, (username, email, password, full_name))
        conn.commit()
        return True, "Registration successful!"
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error
            return False, "Username or email already exists!"
        return False, f"An error occurred: {str(err)}"
    finally:
        cursor.close()
        conn.close()

def reset_password(email, new_password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
            conn.commit()
            return True, "Password reset successful!"
        return False, "Email not found!"
    finally:
        cursor.close()
        conn.close()

def main():
    st.set_page_config(
        page_title="CurrencyWizard",
        page_icon="💱",
        layout="centered"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            background-color: #f0f2f6;
        }
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #007bff;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title and Logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://via.placeholder.com/150", width=150)  # Replace with your logo
    
    st.title("🌍 CurrencyWizard")
    st.markdown("##### Your Ultimate Currency Conversion Companion")

    # Create tabs for Login and Register
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # Login Tab
    with tab1:
        st.markdown("### Login to Your Account")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
        if login_button:
            if not login_username or not login_password:
                st.error("Please fill in all fields!")
            else:
                user = login_user(login_username, login_password)
                if user:
                    st.success(f"Welcome back, {user['full_name']}!")
                    st.session_state['user'] = user
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password!")
                    st.markdown("Don't have an account? [Sign Up](#Sign-Up)")
                    if st.button("Forgot Password?"):
                        with st.form("forgot_password_form"):
                            reset_email = st.text_input("Enter your registered email")
                            reset_new_password = st.text_input("Enter new password", type="password")
                            reset_confirm_password = st.text_input("Confirm new password", type="password")
                            reset_submit = st.form_submit_button("Reset Password")
                        
                        if reset_submit:
                            if reset_new_password != reset_confirm_password:
                                st.error("Passwords do not match!")
                            elif not is_valid_password(reset_new_password):
                                st.error("Password does not meet the requirements!")
                            else:
                                success, message = reset_password(reset_email, reset_new_password)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)

    # Register Tab
    with tab2:
        st.markdown("### Create New Account")
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_full_name = st.text_input("Full Name", key="reg_full_name")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm_password = st.text_input("Confirm Password", type="password")
            
            # Password requirements info
            st.markdown("""
                🗒 Password must contain:
                - At least 8 characters
                - At least one uppercase letter
                - At least one lowercase letter
                - At least one number
                - At least one special character
            """)
            
            register_button = st.form_submit_button("Create Account")
        
        if register_button:
            if not all([reg_username, reg_email, reg_full_name, reg_password, reg_confirm_password]):
                st.error("Please fill in all fields!")
            elif reg_password != reg_confirm_password:
                st.error("Passwords do not match!")
            else:
                success, message = register_user(reg_username, reg_email, reg_password, reg_full_name)
                if success:
                    st.success(message)
                    st.info("Please login with your new account!")
                else:
                    st.error(message)

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center'>
            <p>© 2024 CurrencyWizard. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
