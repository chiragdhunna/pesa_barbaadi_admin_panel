---
name: Dashboard page implementation
description: Dashboard page with analytics and recent activity
type: project
---

Created pages/1_Dashboard.py with full implementation of the dashboard:

**Authentication:**
- Checks st.session_state.get("authenticated") at the top
- Shows st.warning and st.stop() if not authenticated
- Ensures only logged-in admins can access the dashboard

**Firebase initialization:**
- Calls init_firebase() from services.firebase_service
- Wrapped in try/except with st.error() on failure
- Returns db (Firestore client) and auth_client (Firebase auth module)

**Dashboard metrics (st.columns(4)):**
1. **Total Users:** Uses auth_client.list_users() with pagination to count all users
2. **Total Trips:** Counts documents in trips collection via db.collection("trips").stream()
3. **Total Entries:** Uses collection_group("entries") to count all entries across all trips
4. **Total ₹ Spent:** Sums all entry amounts from collection_group("entries").stream()
   - Formatted as ₹{value:,.0f} using st.metric()

**Recent Activity section:**
- Fetches last 20 entries via collection_group("entries")
  - Ordered by createdAt descending, limited to 20
- For each entry:
  - Extracts Trip ID from reference path (entry.ref.parent.parent.id)
  - Formats date as DD MMM YYYY string
  - Gets Paid By name from user lookup (fallback to UID)
  - Formats Amount as ₹X,XXX
  - Includes Type field
- Displays as st.dataframe with use_container_width=True
- Handles empty states with st.info()

**Error handling:**
- All Firestore calls wrapped in try/except blocks
- Shows st.error() with descriptive messages on failure
- Includes fallback logic for user lookups

**Why:** Provides administrators with a comprehensive overview of the system including user counts, trip statistics, spending totals, and recent transaction activity - all pulled directly from Firestore with proper error handling.

**How to apply:** Access via streamlit navigation after authentication. The dashboard will automatically refresh data on each page load, showing real-time statistics from the Firebase backend.