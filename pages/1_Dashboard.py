import streamlit as st
from services.firebase_service import init_firebase
from firebase_admin import firestore
from firebase_admin.auth import UidIdentifier

# Firebase init
try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("📊 Dashboard")

# Create a placeholder for the shimmer skeleton
shimmer_placeholder = st.empty()
with shimmer_placeholder.container():
    from services.ui_service import show_dashboard_shimmer
    show_dashboard_shimmer()

# 1. Total Users
total_users = "Error"
try:
    total_users = 0
    page = auth_client.list_users()
    while page:
        total_users += len(page.users)
        page = page.get_next_page()
except Exception as e:
    st.error(f"Failed to fetch total users: {e}")

# 2. Total Trips
total_trips = "Error"
try:
    trips_ref = db.collection("trips")
    total_trips = len(list(trips_ref.stream()))
except Exception as e:
    st.error(f"Failed to fetch total trips: {e}")

# 3. Total Entries and Total Spent
total_entries = "Error"
total_spent = "Error"
try:
    entries_ref = db.collection_group("entries")
    total_entries = 0
    total_spent_val = 0.0
    for entry in entries_ref.stream():
        entry_data = entry.to_dict()
        total_entries += 1
        total_spent_val += entry_data.get("amount", 0)
    total_spent = f"₹{total_spent_val:,.0f}"
except Exception as e:
    st.error(f"Failed to fetch entries data: {e}")

# 4. Recent Activity
activity_list = []
recent_activity_error = None
try:
    # Fetch last 20 entries
    entries_query = (
        db.collection_group("entries")
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(20)
    )
    entries_stream = list(entries_query.stream())

    if entries_stream:
        # Collect unique paidByUids for batch user lookup
        paid_by_uids = set()
        entries_data = []
        for entry in entries_stream:
            entry_data = entry.to_dict()
            entry_data["id"] = entry.id
            entry_data["ref"] = entry.reference
            paid_by_uid = entry_data.get("paidByUid")
            if paid_by_uid:
                paid_by_uids.add(paid_by_uid)
            entries_data.append(entry_data)

        # Fetch user data for the UIDs
        user_map = {}
        if paid_by_uids:
            try:
                # Get users in batches (max 100 per call)
                uids_list = list(paid_by_uids)
                for i in range(0, len(uids_list), 100):
                    batch = uids_list[i:i + 100]
                    identifiers = [UidIdentifier(uid) for uid in batch]
                    users_result = auth_client.get_users(identifiers)
                    for user in users_result.users:
                        user_map[user.uid] = user.display_name or user.email or user.uid
            except Exception as e:
                # Fallback to using UIDs
                for uid in paid_by_uids:
                    user_map[uid] = uid

        # Build list of dicts for dataframe
        for entry_data in entries_data:
            entry_ref = entry_data["ref"]
            trip_ref = entry_ref.parent.parent
            trip_id = trip_ref.id

            # Format date
            date_val = entry_data.get("date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%d %b %Y")
            else:
                date_str = str(date_val) if date_val else ""

            # Paid by name
            paid_by_uid = entry_data.get("paidByUid", "")
            paid_by_name = user_map.get(paid_by_uid, paid_by_uid)

            # Amount
            amount = entry_data.get("amount", 0)
            amount_formatted = f"₹{int(amount):,}" if isinstance(amount, (int, float)) else "₹0"

            # Type
            entry_type = entry_data.get("type", "")

            activity_list.append({
                "Date": date_str,
                "Trip ID": trip_id,
                "Paid By": paid_by_name,
                "Amount": amount_formatted,
                "Type": entry_type
            })
except Exception as e:
    recent_activity_error = e

# Clear the shimmer skeleton once loaded
shimmer_placeholder.empty()

# Stat cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Users", value=total_users)
with col2:
    st.metric(label="Total Trips", value=total_trips)
with col3:
    st.metric(label="Total Entries", value=total_entries)
with col4:
    st.metric(label="Total ₹ Spent", value=total_spent)

st.divider()

# Recent Activity section
st.subheader("Recent Activity")
if recent_activity_error:
    st.error(f"Failed to load recent activity: {recent_activity_error}")
elif activity_list:
    st.dataframe(activity_list, use_container_width=True)
else:
    st.info("No activity to display")