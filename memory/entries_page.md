---
name: Entries page implementation
description: Entries management page for adding, editing, deleting, and viewing trip expenses
type: project
---

Created pages/4_Entries.py with full implementation of the entries management interface:

**Authentication & Firebase Init:**
- Auth check at top: verifies st.session_state.get("authenticated")
- Firebase initialization via init_firebase() from services.firebase_service
- Also imports recompute_balance from services.balance_service
- Both wrapped in try/except with st.error() on failure

**Trip Selector:**
- Fetches all trips via db.collection("trips").stream()
- Builds dict {tripId: "tripId (Member1 & Member2)"} for display
- Uses st.selectbox with custom format_func to show trip ID with member names
- If no trip selected: shows st.info("Select a trip above") and st.stop()
- Shows trip balance summary in st.info() or st.error() depending on balance state

**Entries Data Fetching:**
- Fetches all entries for selected trip via db.collection("trips").document(selected_trip_id).collection("entries")
- Converts to list of dicts with id and data for manipulation

**Tabbed Interface (4 tabs):**

**Tab 1 — All Entries:**
- Sort options: st.radio("Sort by", ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"], horizontal=True)
- Sorts entries list in Python according to selection
- Builds DataFrame with columns: Date | Paid By | Amount | Type | Note | Created At
  * Date formatted as DD MMM YYYY
  * Paid By looks up name from members dict
  * Amount formatted as ₹X,XXX
  * Type and Note as-is
  * Created At formatted as DD MMM YYYY HH:MM
- Displays via st.dataframe(df, use_container_width=True)
- Shows metrics below: total entries count and total ₹ spent

**Tab 2 — Add Entry:**
- Gets trip members from trip doc
- st.form("add_entry") with:
  * Paid By: st.selectbox with member UIDs, formatted to show member names
  * Amount: st.number_input (min_value=0.01, step=10.0)
  * Date: st.date_input (value=datetime.today())
  * Fill Type: st.radio(["Full tank", "Partial"], horizontal=True)
  * Note: st.text_input (optional)
  * Submit: st.form_submit_button("➕ Add Entry")
- On submit (if amount > 0):
  * Builds entry dict with:
    - uuid4 id
    - paidByUid, paidByName from members dict
    - amount
    - date as Firestore Timestamp
    - type ("full" or "partial")
    - note
    - createdAt as now()
  * Writes to entries subcollection
  * Calls recompute_balance(selected_trip_id, db)
  * Shows st.success(f"Entry added — ₹{amount:,.0f} logged")
  * Calls st.rerun()

**Tab 3 — Edit Entry:**
- st.selectbox to pick entry: formatted as "DD MMM YYYY — PaidByName — ₹amount"
- Prefills st.form("edit_entry") with all current values
- On submit:
  * Updates entry doc fields
  * Calls recompute_balance()
  * Shows st.success() then st.rerun()

**Tab 4 — Delete Entry:**
- st.selectbox to pick entry (same format as Tab 3)
- Shows entry details in st.warning()
- confirm = st.checkbox("I confirm I want to delete this entry")
- if st.button("🗑️ Delete Entry", disabled=not confirm):
  * Delete entry doc
  * Call recompute_balance(selected_trip_id, db)
  * st.success("Entry deleted and balance recalculated")
  * st.rerun()

**Error Handling:**
- All Firebase/Firestore calls wrapped in try/except blocks
- Shows descriptive st.error() messages on failure
- Includes proper date parsing and formatting fallbacks
- Validates amount > 0 before adding entries

**Why:** Provides administrators with a complete interface to manage trip expenses - view all entries with sorting options, add new entries with proper validation, edit existing entries, and delete entries - all while automatically maintaining trip balances through the recompute_balance function.

**How to apply:** Access via streamlit navigation after authentication. First select a trip from the dropdown, then use the tabs to manage entries for that trip. All changes immediately update the trip's balance and are persisted to Firestore.