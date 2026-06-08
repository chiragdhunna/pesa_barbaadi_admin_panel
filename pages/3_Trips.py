import streamlit as st
from services.firebase_service import init_firebase
from services.balance_service import recompute_balance
from firebase_admin import firestore
from datetime import datetime

# Auth check + Firebase init at top
if not st.session_state.get("authenticated"):
    st.warning("Please log in to access the trips page")
    st.stop()

try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("🛵 Trips")

# Fetch all trips: db.collection("trips").stream()
# For each trip, also get entry count and total spent.
try:
    trips_ref = db.collection("trips")
    trips_data = []

    for trip_doc in trips_ref.stream():
        trip_dict = trip_doc.to_dict()
        trip_dict["id"] = trip_doc.id

        # Get entry count and total spent for this trip
        entries_ref = db.collection("trips").document(trip_doc.id).collection("entries")
        entries = list(entries_ref.stream())
        entry_count = len(entries)
        total_spent = sum(float(entry.to_dict().get("amount", 0)) for entry in entries)  # fix: cast to float

        trip_dict["entry_count"] = entry_count
        trip_dict["total_spent"] = total_spent

        trips_data.append(trip_dict)

    # Display total trips metric
    st.metric("Total Trips", len(trips_data))

except Exception as e:
    st.error(f"Failed to fetch trips: {e}")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["All Trips", "Trip Detail", "Edit Trip", "Delete Trip"]
)

# Tab 1 — All Trips
with tab1:
    if trips_data:
        # Build DataFrame: Trip ID | Members | Entries | Total Spent | Balance | Created
        df_data = []
        for trip in trips_data:
            # Format created date
            created_val = trip.get("createdAt")
            if hasattr(created_val, 'strftime'):
                created_str = created_val.strftime("%d %b %Y")
            else:
                created_str = str(created_val) if created_val else ""

            # Members count
            members = trip.get("members", {})
            members_count = len(members)
            members_str = f"{members_count} members" if members_count > 0 else "No members"

            # Format total spent
            total_spent = trip.get("total_spent", 0)
            total_spent_str = f"₹{total_spent:,.0f}"

            # Balance column
            balance = trip.get("balance", {})
            if not balance:  # Empty balance
                balance_str = "✓ Settled"
            else:
                # Find who owes whom
                owed_to = None
                owed_by = None
                amount_owed = 0

                for uid, amount in balance.items():
                    try:
                        amount = float(amount)
                    except (TypeError, ValueError):
                        continue  # skip corrupted entries (e.g. UID stored as value)
                    if amount > 0:  # This person is owed money
                        owed_to = uid
                        amount_owed = amount
                    elif amount < 0:  # This person owes money
                        owed_by = uid

                # Get names from members dict
                owed_to_name = members.get(owed_to, owed_to) if owed_to else "Unknown"
                owed_by_name = members.get(owed_by, owed_by) if owed_by else "Unknown"

                if owed_to and owed_by and amount_owed != 0:
                    balance_str = f"X owes Y ₹{int(amount_owed):,}"
                    # Replace X and Y with actual names
                    balance_str = balance_str.replace("X", owed_by_name).replace("Y", owed_to_name)
                else:
                    balance_str = "✓ Settled" if amount_owed == 0 else "⚠️ Check balance"

            df_data.append({
                "Trip ID": trip["id"],
                "Members": members_str,
                "Entries": trip["entry_count"],
                "Total Spent": total_spent_str,
                "Balance": balance_str,
                "Created": created_str
            })

        import pandas as pd
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trips found")

# Tab 2 — Trip Detail
with tab2:
    if trips_data:
        # Create trip options for selectbox
        trip_options = {trip["id"]: trip for trip in trips_data}

        selected_trip_id = st.selectbox(
            "Select a trip to view details",
            options=list(trip_options.keys()),
            format_func=lambda x: f"Trip {x}",
            key="trip_detail_select"
        )

        if selected_trip_id:
            trip = trip_options[selected_trip_id]

            # Show trip metadata
            created_val = trip.get("createdAt")
            if hasattr(created_val, 'strftime'):
                created_str = created_val.strftime("%Y-%m-%d %H:%M")
            else:
                created_str = str(created_val) if created_val else ""

            st.info(f"""
            **Trip Metadata:**
            - Trip ID: {trip['id']}
            - Created: {created_str}
            """)

            # Members section
            st.subheader("Members")
            members = trip.get("members", {})
            if members:
                members_data = [
                    {"UID": uid, "Display Name": name}
                    for uid, name in members.items()
                ]
                st.dataframe(members_data, use_container_width=True)
            else:
                st.info("No members in this trip")

            # Add member expander
            with st.expander("➕ Add Member"):
                with st.form("add_member"):
                    new_uid = st.text_input("User UID")
                    new_name = st.text_input("Display Name")
                    submit = st.form_submit_button("Add Member")

                    if submit:
                        if new_uid and new_name:
                            try:
                                db.collection("trips").document(selected_trip_id).update(
                                    {f"members.{new_uid}": new_name}
                                )
                                st.success("Member added")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to add member: {e}")
                        else:
                            st.error("Please provide both UID and Display Name")

            # Remove member section
            if members:
                st.subheader("Remove Member")
                member_options = {f"{name} ({uid})": uid for uid, name in members.items()}
                selected_member = st.selectbox(
                    "Select member to remove",
                    options=list(member_options.keys()),
                    key="remove_member_select"
                )

                if selected_member and st.button("Remove Member"):
                    try:
                        uid_to_remove = member_options[selected_member]
                        db.collection("trips").document(selected_trip_id).update(
                            {f"members.{uid_to_remove}": firestore.DELETE_FIELD}
                        )
                        st.success("Member removed")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to remove member: {e}")

            # Balance section
            st.subheader("Balance")
            balance = trip.get("balance", {})
            if not balance:  # Empty balance
                st.success("✓ All settled")
            else:
                # Calculate who owes whom
                owed_to = None
                owed_by = None
                amount_owed = 0

                for uid, amount in balance.items():
                    try:
                        amount = float(amount)
                    except (TypeError, ValueError):
                        continue  # skip corrupted entries (e.g. UID stored as value)
                    if amount > 0:  # This person is owed money
                        owed_to = uid
                        amount_owed = amount
                    elif amount < 0:  # This person owes money
                        owed_by = uid

                if owed_to and owed_by:
                    owed_to_name = members.get(owed_to, owed_to)
                    owed_by_name = members.get(owed_by, owed_by)
                    if amount_owed > 0:
                        st.error(f"{owed_by_name} owes {owed_to_name} ₹{int(amount_owed):,.0f}")
                    else:
                        st.error(f"{owed_to_name} owes {owed_by_name} ₹{int(-amount_owed):,.0f}")
                else:
                    st.info("No balance data or settled")

                if st.button("🔄 Recalculate Balance"):
                    try:
                        recompute_balance(selected_trip_id, db)
                        st.success("Balance recalculated")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to recalculate balance: {e}")
    else:
        st.info("No trips found")

# Tab 3 — Edit Trip
with tab3:
    if trips_data:
        # Create trip options for selectbox
        trip_options = {trip["id"]: trip for trip in trips_data}

        selected_trip_id = st.selectbox(
            "Select a trip to edit",
            options=list(trip_options.keys()),
            format_func=lambda x: f"Trip {x}",
            key="edit_trip_select"
        )

        if selected_trip_id:
            trip = trip_options[selected_trip_id]

            # Edit form
            with st.form("edit_trip"):
                # Parse created date
                created_val = trip.get("createdAt")
                if hasattr(created_val, 'date'):
                    # It's a datetime object
                    default_date = created_val.date()
                elif isinstance(created_val, str):
                    # Try to parse string date
                    try:
                        default_date = datetime.strptime(created_val[:10], "%Y-%m-%d").date()
                    except:
                        default_date = datetime.now().date()
                else:
                    default_date = datetime.now().date()

                created_date = st.date_input(
                    "Created Date",
                    value=default_date
                )

                submit = st.form_submit_button("Update Trip")

                if submit:
                    try:
                        # Create datetime at midnight of selected date
                        new_created_at = datetime.combine(created_date, datetime.min.time())
                        db.collection("trips").document(selected_trip_id).update(
                            {"createdAt": new_created_at}
                        )
                        st.success("Trip updated")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update trip: {e}")
    else:
        st.info("No trips found")

# Tab 4 — Delete Trip
with tab4:
    if trips_data:
        # Create trip options for selectbox
        trip_options = {trip["id"]: trip for trip in trips_data}

        selected_trip_id = st.selectbox(
            "Select a trip to delete",
            options=list(trip_options.keys()),
            format_func=lambda x: f"Trip {x}",
            key="delete_trip_select"
        )

        if selected_trip_id:
            trip = trip_options[selected_trip_id]

            # Show trip summary
            members_count = len(trip.get("members", {}))
            entries_count = trip.get("entry_count", 0) if "entry_count" in trip else 0
            total_spent = trip.get("total_spent", 0) if "total_spent" in trip else 0

            st.warning(f"""
            **About to delete trip:**
            - Trip ID: {selected_trip_id}
            - Members: {members_count}
            - Entries: {entries_count}
            - Total Spent: ₹{total_spent:,.0f}

            WARNING: This will delete this trip and ALL its entries.
            This action cannot be undone!
            """)

            confirm = st.checkbox("I confirm I want to delete this trip and ALL its entries")

            if st.button("🗑️ Delete Trip", disabled=not confirm):
                try:
                    # Batch delete: stream all entries, delete each, then delete trip doc
                    entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
                    entries = entries_ref.stream()

                    # Delete each entry
                    for entry in entries:
                        entry.reference.delete()

                    # Delete the trip document
                    db.collection("trips").document(selected_trip_id).delete()

                    st.success("Trip deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete trip: {e}")
    else:
        st.info("No trips found")