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
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

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

def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                      (username, password))
        user = cursor.fetchone()
        if user:
            cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", 
                         (datetime.now(), user['user_id']))
            conn.commit()
            return user
        return None
    finally:
        cursor.close()
        conn.close()

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
        if err.errno == 1062:
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
    st.set_page_config(page_title="CurrencyWizard", page_icon="💱", layout="centered")
    
    # Initialize session state for active tab
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Login"

    # Title and Logo
    st.title("🌍 CurrencyWizard")
    st.markdown("##### Your Ultimate Currency Conversion Companion")

    # Custom Tabs
    if st.session_state.active_tab == "Login":
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
        
        # Navigate to Sign Up
        if st.button("Don't have an account? Sign Up"):
            st.session_state.active_tab = "Sign Up"
            st.experimental_rerun()
    
    elif st.session_state.active_tab == "Sign Up":
        st.markdown("### Create New Account")
        with st.form("register_form"):
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email")
            reg_full_name = st.text_input("Full Name")
            reg_password = st.text_input("Password", type="password")
            reg_confirm_password = st.text_input("Confirm Password", type="password")
            
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
                    st.session_state.active_tab = "Login"
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        # Navigate to Login
        if st.button("Already have an account? Login"):
            st.session_state.active_tab = "Login"
            st.experimental_rerun()

if __name__ == "__main__":
    main()
