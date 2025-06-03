import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment variables or Streamlit secrets
if hasattr(st, 'secrets'):
    # Running on Streamlit Cloud
    AUTH_USERNAME = st.secrets.get('AUTH_USERNAME', 'admin')
    AUTH_PASSWORD = st.secrets.get('AUTH_PASSWORD', 'admin123')
else:
    # Running locally
    AUTH_USERNAME = os.getenv('AUTH_USERNAME', 'admin')
    AUTH_PASSWORD = os.getenv('AUTH_PASSWORD', 'admin123')

def hash_password(password):
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify username and password against environment variables"""
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()

def show_login_page():
    """Display login page"""
    st.title("🔐 Login")
    st.markdown("Please login to access the Embase Conference Dashboard")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if verify_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
   
def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    if 'username' in st.session_state:
        del st.session_state.username
    st.rerun()

def show_user_info():
    """Display current user info and logout button"""
    if st.session_state.authenticated and 'username' in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username}**")
        if st.sidebar.button("🚪 Logout"):
            logout()