---
name: Trips page implementation
description: Trips management page with viewing, editing, adding members, and deleting trips
type: project
---

Created pages/3_Trips.py with full implementation of the trips management interface:

**Authentication & Firebase Init:**
- Auth check at top: verifies st.session_state.get("authenticated")
- Firebase initialization via init_firebase() from services.firebase_service
- Both wrapped in try/except with st.error() on failure
- Also imports recompute_balance from services.balance_service

**Trips Data Fetching:**
- Fetches all trips via db.collection("trips").stream()
- For each trip, also gets entry count and total spent by querying the entries subcollection
- Shows st.metric("Total Trips", count)

**Tabbed Interface (4 tabs):**

**Tab 1 — All Trips:**
- Displays DataFrame with columns:
  * Trip ID | Members | Entries | Total Spent | Balance | Created
  * Members: shows count like "2 members" or "No members"
  * Entries: number of entries in the trip
  * Total Spent: formatted as "₹X,XXX"
  * Balance: 
    - "✓ Settled" if empty or zero balance
    - "X owes Y ₹amount" format showing who owes whom (with actual names)
  * Created: formatted as "YYYY-MM-DD"
- Uses st.dataframe(df, use_container_width=True)

**Tab 2 — Trip Detail:**
- Dropdown (st.selectbox) to pick a trip ID (formatted as "Trip {id}")
- Shows trip metadata in st.info(): created date and Trip ID
- **Members section:**
  - st.subheader("Members")
  - st.dataframe of {UID: name} dict showing UID and Display Name
  - st.expander("➕ Add Member"):
    - st.form("add_member") with:
      * new_uid = st.text_input("User UID")
      * new_name = st.text_input("Display Name")
      * submit → db.collection("trips").document(tripId).update(
        {"members.{new_uid}": new_name}) + st.success + st.rerun()
  - Remove member:
    - st.selectbox to pick member to remove (formatted as "Name (UID)")
    - if st.button("Remove Member"): 
      * uses FieldValue.delete() to remove the key 
      * st.success + st.rerun()

**Balance section:**
  - st.subheader("Balance")
  - if amount == 0: st.success("✓ All settled")
  - else: st.error(f"owedByName owes owedToName ₹{amount:,.0f}")
  - if st.button("🔄 Recalculate Balance"):
    * calls recompute_balance(tripId, db)
    * st.success("Balance recalculated") + st.rerun()

**Tab 3 — Edit Trip:**
- st.selectbox to pick a trip (formatted as "Trip {id}")
- st.form("edit_trip"):
  * created_date = st.date_input("Created Date", value=trip["createdAt"].date())
  * submit → db.collection("trips").document(tripId).update(
    {"createdAt": datetime(...)}) + st.success + st.rerun()

**Tab 4 — Delete Trip:**
- st.selectbox to pick a trip (formatted as "Trip {id}")
- Shows trip summary in st.warning(): Trip ID, Members count, Entries count, Total Spent
- confirm = st.checkbox("I confirm I want to delete this trip and ALL its entries")
- if st.button("🗑️ Delete Trip", disabled=not confirm):
  * Batch delete: streams all entries, deletes each, then deletes trip doc
  * st.success("Trip deleted") + st.rerun()

**Error Handling:**
- All Firebase/Firestore calls wrapped in try/except blocks
- Shows descriptive st.error() messages on failure
- Includes proper handling for missing data and edge cases

**Why:** Provides administrators with a complete interface to manage trips - view all trips with analytics, see detailed trip information including members and balances, add/remove members, edit trip dates, recalculate balances, and delete trips (with confirmation and cascade deletion of entries).

**How to apply:** Access via streamlit navigation after authentication. The page loads trips data from Firestore and provides real-time updates for all operations.