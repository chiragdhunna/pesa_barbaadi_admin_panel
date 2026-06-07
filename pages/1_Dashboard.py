import streamlit as st
from services.firebase_service import init_firebase
from firebase_admin import firestore

# Auth check at top
if not st.session_state.get("authenticated"):
    st.warning("Please log in to access the dashboard")
    st.stop()

# Firebase init
try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("📊 Dashboard")

# Stat cards
col1, col2, col3, col4 = st.columns(4)

# Total Users
try:
    total_users = 0
    page = auth_client.list_users()
    while page:
        total_users += len(page.users)
        page = page.get_next_page()
    with col1:
        st.metric(label="Total Users", value=total_users)
except Exception as e:
    with col1:
        st.metric(label="Total Users", value="Error")
    st.error(f"Failed to fetch total users: {e}")

# Total Trips
try:
    trips_ref = db.collection("trips")
    total_trips = len(list(trips_ref.stream()))
    with col2:
        st.metric(label="Total Trips", value=total_trips)
except Exception as e:
    with col2:
        st.metric(label="Total Trips", value="Error")
    st.error(f"Failed to fetch total trips: {e}")

# Total Entries and Total ₹ Spent
try:
    entries_ref = db.collection_group("entries")
    total_entries = 0
    total_spent = 0.0
    for entry in entries_ref.stream():
        entry_data = entry.to_dict()
        total_entries += 1
        total_spent += entry_data.get("amount", 0)
    with col3:
        st.metric(label="Total Entries", value=total_entries)
    with col4:
        st.metric(label="Total ₹ Spent", value=f"₹{total_spent:,.0f}")
except Exception as e:
    with col3:
        st.metric(label="Total Entries", value="Error")
    with col4:
        st.metric(label="Total ₹ Spent", value="Error")
    st.error(f"Failed to fetch entries data: {e}")

st.divider()

# Recent Activity section
st.subheader("Recent Activity")
try:
    # Fetch last 20 entries
    entries_query = (
        db.collection_group("entries")
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(20)
    )
    entries_stream = list(entries_query.stream())

    if not entries_stream:
        st.info("No entries found")
    else:
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
                    batch = uids_list[i:i+100]
                    users_result = auth_client.get_users(batch)
                    for user in users_result.users:
                        user_map[user.uid] = user.display_name or user.email or user.uid
            except Exception as e:
                st.warning(f"Could not fetch user details: {e}")
                # Fallback to using UIDs
                for uid in paid_by_uids:
                    user_map[uid] = uid

        # Build list of dicts for dataframe
        activity_list = []
        for entry_data in entries_data:
            # Get trip ID from reference path
            entry_ref = entry_data["ref"]
            # Path: projects/(project_id)/databases/(default)/documents/trips/{tripId}/entries/{entryId}
            # So parent.parent is the trip document
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

        # Display as dataframe
        if activity_list:
            st.dataframe(activity_list, use_container_width=True)
        else:
            st.info("No activity to display")
except Exception as e:
    st.error(f"Failed to load recent activity: {e}")