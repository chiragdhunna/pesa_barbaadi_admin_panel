import streamlit as st
import os
from streamlit_cookies_manager import EncryptedCookieManager
from services.auth import is_authenticated, login, logout

# Page config must be at the very top
st.set_page_config(
    page_title="Pesa Barbaadi Admin",
    page_icon="⛽",
    layout="wide"
)

# Initialize cookie manager directly (not cached to avoid widget warnings)
cookie_password = st.secrets.get("COOKIE_PASSWORD", "a-default-secret-key-for-development-only")
cookies = EncryptedCookieManager(
    prefix="pesa_barbaadi_admin",
    password=cookie_password,
)

# Wait for cookies to be ready
if not cookies.ready():
    st.stop()

def login_page_func():
    # Show ONLY the login form — centered, no sidebar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>⛽</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Pesa Barbaadi Admin</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Enter your credentials to continue</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login", use_container_width=True)

            if submit_button:
                if login(cookies, username, password):
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

# Check authentication status using cookie and session state
if not is_authenticated(cookies):
    login_pg = st.Page(login_page_func, title="Login", icon="🔒")
    pg = st.navigation([login_pg], position="hidden")
    pg.run()
else:
    # User is logged in — show sidebar logout button and user info
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.get('admin_username', 'Admin')}**")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True, key="logout_sidebar"):
            logout(cookies)
            st.rerun()
        st.divider()

    # Define dynamic navigation structure
    dashboard_pg = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊", default=True)
    users_pg = st.Page("pages/2_Users.py", title="Users", icon="👥")
    trips_pg = st.Page("pages/3_Trips.py", title="Trips", icon="🛵")
    entries_pg = st.Page("pages/4_Entries.py", title="Entries", icon="📋")
    export_pg = st.Page("pages/5_Export.py", title="Export", icon="📥")

    pg = st.navigation([dashboard_pg, users_pg, trips_pg, entries_pg, export_pg])
    pg.run()