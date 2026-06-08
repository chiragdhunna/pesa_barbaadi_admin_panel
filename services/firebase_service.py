import streamlit as st
import firebase_admin
import json
import os
from firebase_admin import credentials, firestore
from firebase_admin import auth

@st.cache_resource
def init_firebase():
    """Initialize Firebase app and return Firestore client and auth module."""
    try:
        if not firebase_admin._apps:
            # 1. Try Streamlit secrets (Streamlit Cloud)
            try:
                firebase_config = dict(st.secrets["firebase"])
                cred = credentials.Certificate(firebase_config)

            except (KeyError, FileNotFoundError):
                # 2. Fallback to local file path (local development)
                service_account_path = "firebase_config/service_account.json"
                if not os.path.exists(service_account_path):
                    raise FileNotFoundError(f"Service account file not found at: {service_account_path}")
                cred = credentials.Certificate(service_account_path)

            firebase_admin.initialize_app(cred)

        db = firestore.client()
        return db, auth

    except FileNotFoundError as e:
        st.error(f"Firebase service account file not found: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()