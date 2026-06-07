---
name: Users page implementation
description: User management page with viewing, editing, and deleting Firebase users
type: project
---

Created pages/2_Users.py with full implementation of the user management interface:

**Authentication & Firebase Init:**
- Auth check at top: verifies st.session_state.get("authenticated")
- Firebase initialization via init_firebase() from services.firebase_service
- Both wrapped in try/except with st.error() on failure

**User Listing:**
- Uses auth_client.list_users().iterate_all() to fetch all users with automatic pagination
- Builds list of user dicts with: uid, display_name, email, created_at, last_sign_in, disabled status
- Shows st.metric("Total Users", count)

**Tabbed Interface:**

**Tab 1 — All Users:**
- Displays pandas DataFrame with columns:
  * Display Name | Email | UID | Created | Last Sign-In | Status
  * Status shows "✅ Active" or "🚫 Disabled" based on user.disabled
  * Timestamps formatted as "YYYY-MM-DD HH:MM"
  * Empty values shown as "(No name)" or "(No email)"
- Uses st.dataframe(df, use_container_width=True) for responsive display

**Tab 2 — Edit User:**
- Dropdown (st.selectbox) with options formatted as "Name (email)" → uid mapping
- Shows current user values in st.info() when a user is selected
- Edit form (st.form("edit_user")) with:
  * Display Name text_input (pre-filled with current value)
  * Email text_input (pre-filled with current value)
  * Submit button that calls auth_client.update_user() with changed fields
  * Shows st.success("User updated") and st.rerun() on success
- Below form - two columns:
  * Left: Disable/Enable button toggles user.disabled state
  * Right: "Send Password Reset" button that:
    - Calls auth_client.generate_password_reset_link(email)
    - Shows st.info() and displays link in st.code()

**Tab 3 — Delete User:**
- Dropdown (st.selectbox) to select user for deletion (same format as edit tab)
- Shows st.warning() with user details (name, email, UID) for confirmation
- Confirmation checkbox: "I confirm I want to permanently delete this user"
- Delete button (🗑️ Delete User) that:
  - Is disabled until confirmation checkbox is checked
  - Calls auth_client.delete_user(uid) when clicked
  - Shows st.success("User deleted") and st.rerun() on success

**Error Handling:**
- All Firebase/Admin SDK calls wrapped in try/except blocks
- Shows descriptive st.error() messages on failure
- Includes fallback handling for missing timestamp data
- Validates email presence before generating password reset links

**Why:** Provides administrators with a complete interface to manage Firebase users - view all users, edit profile information, enable/disable accounts, send password reset links, and delete users when necessary - all with proper confirmation and error handling.

**How to apply:** Access via streamlit navigation after authentication. The page automatically loads all users from Firebase and provides real-time updates after modifications.