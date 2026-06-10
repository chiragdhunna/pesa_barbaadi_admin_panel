import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

def get_cookie_manager():
    """
    Returns an EncryptedCookieManager instance.
    Note: This should be called once per session and the instance reused.
    """
    # Use a secret for the cookie encryption password if available, otherwise fallback to a hardcoded string.
    # In production, you should set COOKIE_PASSWORD in .streamlit/secrets.toml
    cookie_password = st.secrets.get("COOKIE_PASSWORD", "a-default-secret-key-for-development-only")

    return EncryptedCookieManager(
        prefix="pesa_barbaadi_admin",  # Removed trailing slash for consistency
        password=cookie_password,
    )

def is_authenticated(cookies):
    """
    Check if the user is authenticated via session state or cookie.
    Returns True if either indicates authentication.
    """
    # Check session state first (faster)
    if st.session_state.get("authenticated", False):
        return True

    # Check cookie
    auth_cookie = cookies.get("pb_admin_auth")
    if auth_cookie == "true":
        # Set session state to match cookie for consistency
        st.session_state["authenticated"] = True
        return True

    return False

def login(cookies, username, password):
    """
    Validate credentials and set authentication state.
    Returns True on success, False on failure.
    """
    # Validate against secrets
    if username == st.secrets["ADMIN_USERNAME"] and password == st.secrets["ADMIN_PASSWORD"]:
        # Set session state
        st.session_state["authenticated"] = True
        # Set cookie
        cookies["pb_admin_auth"] = "true"
        cookies.save()  # Important: save changes to cookie
        return True
    return False

def logout(cookies):
    """
    Clear authentication state and remove cookie.
    """
    # Clear session state
    st.session_state["authenticated"] = False
    # Remove cookie by setting to empty string
    cookies["pb_admin_auth"] = ""
    cookies.save()