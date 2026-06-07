import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth

@st.cache_resource
def init_firebase():
    """Initialize Firebase app and return Firestore client and auth module."""
    try:
        # Get the service account path from secrets
        service_account_path = st.secrets["FIREBASE_SERVICE_ACCOUNT_PATH"]

        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        # Get Firestore client and auth module
        db = firestore.client()
        return db, auth

    except FileNotFoundError:
        st.error(f"Firebase service account file not found at: {service_account_path}")
        st.stop()
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()