import streamlit as st
from converter import convert_currency, get_all_currencies
import mysql.connector
from datetime import datetime, timedelta
import re
import pandas as pd
import matplotlib.pyplot as plt
import requests

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

# Function to fetch conversion history for a specific user
def get_conversion_history(username):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT conversion_type, input_value, converted_value, timestamp
            FROM conversion_history
            WHERE username = %s
            ORDER BY timestamp DESC
        """, (username,))
        history = cursor.fetchall()
        return history
    finally:
        cursor.close()
        conn.close()

# Display Conversion History
def show_conversion_history(username):
    st.markdown("### Conversion History")
    history = get_conversion_history(username)
    if history:
        # Convert history to DataFrame for better display
        history_df = pd.DataFrame(history)
        history_df.columns = ["Conversion Type", "Input Value", "Converted Value", "Timestamp"]
        history_df.index += 1
        st.dataframe(history_df)
    else:
        st.info("No conversion history found!")

# Save a conversion to the history (to be used after any conversion operation)
def save_conversion(username, conversion_type, input_value, converted_value):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO conversion_history (username, conversion_type, input_value, converted_value, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, conversion_type, input_value, converted_value, datetime.now()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_historical_rates(base_currency, target_currencies, period='daily', days=30, api_key="3028551a2fd5c87440a51801"):
    """
    Fetch historical exchange rates for multiple currencies
    
    Args:
        base_currency (str): Base currency code
        target_currencies (list): List of target currency codes
        period (str): 'daily', 'weekly', or 'monthly'
        days (int): Number of days to fetch historical data
        api_key (str): API key for exchange rate service
    
    Returns:
        pd.DataFrame: Historical exchange rates
    """
    # Validate input
    if len(target_currencies) > 4:
        st.error("Please select no more than 4 currencies")
        return None

    # Prepare data collection
    historical_data = {}
    historical_data[base_currency] = [1] * days  # Base currency always at 1

    # Fetch historical rates for each target currency
    for currency in target_currencies:
        try:
            # Construct the API URL properly (ensure correct endpoint)
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/history/{base_currency}/{days}?period={period}"
            response = requests.get(url)
            
            # Check for a successful response
            if response.status_code != 200:
                st.error(f"Failed to fetch data for {currency}. HTTP Status Code: {response.status_code}")
                return None
            
            data = response.json()

            # Check if the 'rates' key exists in the API response
            if 'rates' not in data:
                st.error(f"No rate data available for {currency}. Please try again later.")
                return None

            # Extract rates if available
            rates = [data['rates'].get(day, {}).get(currency, None) for day in data['rates']]
            historical_data[currency] = rates
        
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching rates for {currency}: {str(e)}")
            return None

    # Create DataFrame
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    dates.reverse()
    df = pd.DataFrame(historical_data, index=dates)

    # Apply period aggregation (if needed)
    if period == 'weekly':
        df = df.resample('W').mean()
    elif period == 'monthly':
        df = df.resample('M').mean()

    return df

# Example usage (integrating with your Streamlit app):




# Note: This function should replace the existing visualization_page() in your main Streamlit app

def main():
    st.set_page_config(page_title="CurrencyWizard", page_icon="💱", layout="centered")

    # Persistent session state for login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    # Login page
    def login_page():
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
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password!")
            
            # Navigate to Sign Up
            if st.button("Don't have an account? Sign Up"):
                st.session_state.active_tab = "Sign Up"
                st.rerun()
        
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
                        st.rerun()
                    else:
                        st.error(message)
            
            # Navigate to Login
            if st.button("Already have an account? Login"):
                st.session_state.active_tab = "Login"
                st.rerun()

    def app_page():
        st.sidebar.title("Navigation")
        option = st.sidebar.selectbox("", ["Currency Conversion", "Visualization", "History", "Log Out"])

        if option == "Currency Conversion":
            currency_conversion_page()
        elif option == "Visualization":
            visualization_page()
        elif option == "History":
            history_page()
        elif option == "Log Out":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # Currency conversion page
    def currency_conversion_page():
        st.title("Currency Conversion")

        api_key = "3028551a2fd5c87440a51801"

        # Fetch all currencies
        try:
            currencies = get_all_currencies(api_key)
            currency_list = [f"{code} - {name}" for code, name in currencies.items()]
        except Exception as e:
            st.error(f"Failed to fetch currencies: {str(e)}")
            return

        # Function to extract the currency code from the dropdown selection
        def extract_code(selection):
            return selection.split(" - ")[0]

        amount = st.number_input("Enter Amount", min_value=0.0, step=0.01)
        from_currency = st.selectbox("From Currency", options=currency_list)
        to_currency = st.selectbox("To Currency", options=currency_list)

        if st.button("Convert"):
            try:
                from_currency_code = extract_code(from_currency)
                to_currency_code = extract_code(to_currency)
                result = convert_currency(amount, from_currency_code, to_currency_code, api_key)
                st.success(f"Converted Amount: {result:.2f} {to_currency_code}")

                save_conversion(st.session_state['user']['username'], f"{from_currency_code} to {to_currency_code}", amount, result)
            except Exception as e:
                st.error(str(e))

    # Visualization page (placeholder)
    # def visualization_page():
    #     st.title("Visualization")
    def visualization_page():
        st.title("Currency Rate Visualization")

        # Fetch available currencies
        api_key = "3028551a2fd5c87440a51801"
        try:
            currencies = get_all_currencies(api_key)  # This function should return the currencies you need
            currency_list = [f"{code} - {name}" for code, name in currencies.items()]
        except Exception as e:
            st.error(f"Failed to fetch currencies: {str(e)}")
            return

        # Function to extract currency code
        def extract_code(selection):
            return selection.split(" - ")[0]

        # Sidebar for configuration
        st.sidebar.header("Visualization Settings")
        base_currency = st.sidebar.selectbox("Base Currency", options=currency_list, index=0)
        
        # Multi-select for target currencies (max 4)
        target_currencies = st.sidebar.multiselect(
            "Select Target Currencies (Max 4)", 
            options=currency_list, 
            max_selections=4
        )

        # Period selection
        period = st.sidebar.radio(
            "View Period", 
            options=['Daily', 'Weekly', 'Monthly'], 
            index=0
        )

        # Visualization button
        if st.sidebar.button("Generate Visualization"):
            if not target_currencies:
                st.error("Please select at least one target currency")
                return

            # Convert selections to currency codes
            base_code = extract_code(base_currency)
            target_codes = [extract_code(curr) for curr in target_currencies]

            # Get historical rates
            historical_data = get_historical_rates(
                base_currency=base_code, 
                target_currencies=target_codes, 
                period=period.lower()
            )

            if historical_data is not None:
                # Plotting
                plt.figure(figsize=(12, 6))
                for currency in historical_data.columns:
                    if currency != base_code:
                        plt.plot(historical_data.index, historical_data[currency], label=currency)

                plt.title(f"Exchange Rates: {base_code} as Base Currency")
                plt.xlabel("Date")
                plt.ylabel("Exchange Rate")
                plt.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Display plot in Streamlit
                st.pyplot(plt)

                # Optional: Display data table
                st.markdown("### Exchange Rate Data")
                st.dataframe(historical_data)
    

    def history_page():
        st.title("History")
        show_conversion_history(st.session_state['user']['username'])

    # Conditional rendering based on login state
    if st.session_state.logged_in:
        app_page()
    else:
        login_page()

if __name__ == "__main__":
    main()
