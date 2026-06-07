---
name: Firebase service setup
description: Firebase service initialized with proper caching and error handling
type: project
---

Firebase service module created with @st.cache_resource decorator to ensure Firebase initializes only once across all pages. Reads FIREBASE_SERVICE_ACCOUNT_PATH from st.secrets, checks if firebase_admin._apps is already initialized before calling initialize_app() to avoid duplicate app errors, and returns a tuple (db, auth) where db is firestore.client() and auth is the firebase_admin.auth module. Handles FileNotFoundError for missing service account with a clear st.error() message and st.stop().

**Why:** To establish a secure, efficient connection to Firebase that avoids re-initialization overhead and provides clear error messages for missing configuration.

**How to apply:** Use `db, auth = services.firebase_service.init_firebase()` in any page that needs Firebase access. The @st.cache_resource decorator ensures the initialization happens only once per session.