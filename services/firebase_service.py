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
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            # Try to get service account key as JSON string from environment variable (for Vercel)
            service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                # Parse the JSON string to a dictionary
                service_account_info = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_info)
            else:
                # Fallback to file path (from st.secrets for local dev or environment variable)
                try:
                    service_account_path = st.secrets["FIREBASE_SERVICE_ACCOUNT_PATH"]
                except KeyError:
                    service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")

                if not service_account_path:
                    raise ValueError("Firebase service account not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH.")

                cred = credentials.Certificate(service_account_path)

            firebase_admin.initialize_app(cred)

        # Get Firestore client and auth module
        db = firestore.client()
        return db, auth

    except FileNotFoundError:
        st.error(f"Firebase service account file not found at: {service_account_path if 'service_account_path' in locals() else 'unknown'}")
        st.stop()
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()