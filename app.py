import streamlit as st
import os
from streamlit_cookies_manager import EncryptedCookieManager
from services.auth import is_authenticated, login, logout

# Initialize cookie manager directly (not cached to avoid widget warnings)
cookie_password = st.secrets.get("COOKIE_PASSWORD", "a-default-secret-key-for-development-only")
cookies = EncryptedCookieManager(
    prefix="pesa_barbaadi_admin",  # Removed trailing slash for consistency
    password=cookie_password,
)

# Wait for cookies to be ready
if not cookies.ready():
    st.stop()

def login_page():
    st.set_page_config(
        page_title="Pesa Barbaadi Admin",
        page_icon="⛽",
        layout="wide"
    )

    # Get admin credentials from secrets or environment variables
    try:
        ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
    except (KeyError, FileNotFoundError):
        ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")

    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # Create centered column
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Large fuel emoji and title
        st.markdown("<h1 style='text-align: center;'>⛽</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Pesa Barbaadi Admin</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Admin interface for managing trip expenses</p>", unsafe_allow_html=True)

    # Login form
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            # Use the login function from auth service
            if login(cookies, username, password):
                st.rerun()
            else:
                st.error("Invalid username or password")

# Check authentication status using cookie and session state
if not is_authenticated(cookies):
    login_page()
    st.stop()
else:
    st.success("✓ Logged in as admin")
    st.info("Use the sidebar to navigate between pages.")

    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout"):
        logout(cookies)
        st.rerun()