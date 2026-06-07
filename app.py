import streamlit as st

def login_page():
    st.set_page_config(
        page_title="Pesa Barbaadi Admin",
        page_icon="⛽",
        layout="wide"
    )

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
                # Compare with secrets (direct comparison is acceptable for internal tools)
                if username == st.secrets["ADMIN_USERNAME"] and password == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")

# Check authentication status
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
    st.stop()
else:
    st.success("✓ Logged in as admin")
    st.info("Use the sidebar to navigate between pages.")

    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()