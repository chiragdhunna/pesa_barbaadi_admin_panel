---
name: App implementation
description: Main app.py with login/logout functionality
type: project
---

Created app.py with full implementation of the login/logout system:

**Login page features:**
- Streamlit page config: title "Pesa Barbaadi Admin", ⛽ icon, wide layout
- Centered column layout using st.columns([1,2,1])[1]
- Large fuel emoji (⛽) centered above title
- Title: "Pesa Barbaadi Admin"
- Muted subtitle: "Admin interface for managing trip expenses"
- Login form with:
  - Username text_input
  - Password text_input (type="password")
  - Login submit button
- On submit:
  - Direct comparison with st.secrets["ADMIN_USERNAME"] and st.secrets["ADMIN_PASSWORD"]
  - On success: set st.session_state["authenticated"] = True, st.rerun()
  - On failure: st.error("Invalid username or password")

**Main app logic:**
- Initialize st.session_state["authenticated"] = False if not present
- If not authenticated: call login_page() and st.stop()
- If authenticated:
  - Show st.success("✓ Logged in as admin")
  - Show st.info("Use the sidebar to navigate between pages.")
  - Sidebar logout button: 
    - If clicked: set st.session_state["authenticated"] = False, st.rerun()

**Why:** Provides secure authentication for the admin interface while maintaining simplicity for internal tool usage. The direct string comparison is acceptable for this internal admin tool as noted in the instructions.

**How to apply:** Run with `streamlit run app.py`. The app will automatically handle authentication flow, showing login page when needed and main interface with logout option when authenticated.