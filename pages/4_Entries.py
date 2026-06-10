import streamlit as st
from services.firebase_service import init_firebase
from services.balance_service import recompute_balance
from firebase_admin import firestore
from datetime import datetime
import uuid

try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("📋 Entries")

# Top-level trip selector: Fetch all trips, build dict {tripId: "tripId (Member1 & Member2)"}
try:
    trips_ref = db.collection("trips")
    trips_data = []

    for trip_doc in trips_ref.stream():
        trip_dict = trip_doc.to_dict()
        trip_dict["id"] = trip_doc.id
        trips_data.append(trip_dict)

    if not trips_data:
        st.info("No trips found. Please create a trip first.")
        st.stop()

    # Build trip labels dict
    trip_options = {}
    trip_labels = {}

    for trip in trips_data:
        trip_id = trip["id"]
        members = trip.get("members", {})

        # Get member names for label
        member_names = list(members.values())
        if len(member_names) >= 2:
            label = f"{trip_id} ({member_names[0]} & {member_names[1]})"
        elif len(member_names) == 1:
            label = f"{trip_id} ({member_names[0]})"
        else:
            label = f"{trip_id} (No members)"

        trip_options[trip_id] = trip
        trip_labels[trip_id] = label

    selected_trip_id = st.selectbox(
        "Select a trip",
        options=list(trip_options.keys()),
        format_func=lambda x: trip_labels[x]
    )

except Exception as e:
    st.error(f"Failed to load trips: {e}")
    st.stop()

if not selected_trip_id:
    st.info("Select a trip above")
    st.stop()

# Get the selected trip
try:
    trip = trip_options[selected_trip_id]
    members = trip.get("members", {})
except Exception as e:
    st.error(f"Failed to load trip data: {e}")
    st.stop()

# Show trip balance summary
try:
    balance = trip.get("balance", {})
    if not balance:  # Empty balance
        st.info("ℹ️ No balance data available")
    else:
        # Calculate who owes whom
        owed_to = None
        owed_by = None
        amount_owed = 0

        for uid, amount in balance.items():
            if amount > 0:  # This person is owed money
                owed_to = uid
                amount_owed = amount
            elif amount < 0:  # This person owes money
                owed_by = uid

        if owed_to and owed_by:
            owed_to_name = members.get(owed_to, owed_to)
            owed_by_name = members.get(owed_by, owed_by)
            if amount_owed > 0:
                st.error(f"💸 {owed_by_name} owes {owed_to_name} ₹{int(amount_owed):,.0f}")
            else:
                st.error(f"💸 {owed_to_name} owes {owed_by_name} ₹{int(-amount_owed):,.0f}")
        else:
            st.info("✓ All settled")
except Exception as e:
    st.warning(f"Could not load balance information: {e}")

# Fetch all entries for selected trip
try:
    entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
    entries_stream = list(entries_ref.stream())

    # Convert to list of dicts with id and data
    entries_list = []
    for entry_doc in entries_stream:
        entry_dict = entry_doc.to_dict()
        entry_dict["id"] = entry_doc.id
        entries_list.append(entry_dict)

except Exception as e:
    st.error(f"Failed to load entries: {e}")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["All Entries", "Add Entry", "Edit Entry", "Delete Entry"]
)

# Tab 1 — All Entries
with tab1:
    if entries_list:
        # Sort options
        sort_option = st.radio(
            "Sort by",
            ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"],
            horizontal=True,
            key="entries_sort"
        )

        # Sort the entries list in Python accordingly
        def get_date_for_sorting(entry):
            date_val = entry.get("date")
            if hasattr(date_val, 'timestamp'):
                return date_val.timestamp()
            elif isinstance(date_val, str):
                try:
                    # Try to parse ISO string
                    from datetime import datetime
                    return datetime.fromisoformat(date_val.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            return 0

        def get_amount_for_sorting(entry):
            return entry.get("amount", 0)

        # Apply sorting
        if sort_option == "Date ↓":  # Newest first
            entries_list.sort(key=get_date_for_sorting, reverse=True)
        elif sort_option == "Date ↑":  # Oldest first
            entries_list.sort(key=get_date_for_sorting, reverse=False)
        elif sort_option == "Amount ↓":  # Highest first
            entries_list.sort(key=get_amount_for_sorting, reverse=True)
        elif sort_option == "Amount ↑":  # Lowest first
            entries_list.sort(key=get_amount_for_sorting, reverse=False)

        # Build DataFrame: Date | Paid By | Amount | Type | Note | Created At
        df_data = []
        for entry in entries_list:
            # Format date
            date_val = entry.get("date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%d %b %Y")
            elif isinstance(date_val, str):
                try:
                    # Try to parse and reformat
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%d %b %Y")
                except:
                    date_str = str(date_val) if date_val else ""
            else:
                date_str = str(date_val) if date_val else ""

            # Paid By
            paid_by_uid = entry.get("paidByUid", "")
            paid_by_name = members.get(paid_by_uid, paid_by_uid)

            # Amount
            amount = entry.get("amount", 0)
            amount_formatted = f"₹{int(amount):,}" if isinstance(amount, (int, float)) else "₹0"

            # Type and Note
            entry_type = entry.get("type", "")
            note = entry.get("note", "")

            # Created At
            created_val = entry.get("createdAt")
            if hasattr(created_val, 'strftime'):
                created_str = created_val.strftime("%d %b %Y %H:%M")
            elif isinstance(created_val, str):
                try:
                    from datetime import datetime
                    created_obj = datetime.fromisoformat(created_val.replace('Z', '+00:00'))
                    created_str = created_obj.strftime("%d %b %Y %H:%M")
                except:
                    created_str = str(created_val) if created_val else ""
            else:
                created_str = str(created_val) if created_val else ""

            df_data.append({
                "Date": date_str,
                "Paid By": paid_by_name,
                "Amount": amount_formatted,
                "Type": entry_type,
                "Note": note,
                "Created At": created_str
            })

        if df_data:
            import pandas as pd
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

            # Metrics below
            total_entries = len(entries_list)
            total_spent = sum(entry.get("amount", 0) for entry in entries_list)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Entries", total_entries)
            with col2:
                st.metric("Total ₹ Spent", f"₹{total_spent:,.0f}")
        else:
            st.info("No entries to display")
    else:
        st.info("No entries found for this trip")

# Tab 2 — Add Entry
with tab2:
    if members:
        with st.form("add_entry"):
            # Get trip members for selectbox
            member_uids = list(members.keys())

            paid_by_uid = st.selectbox(
                "Paid By",
                options=member_uids,
                format_func=lambda uid: members[uid]
            )

            amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                step=10.0,
                value=100.0
            )

            date = st.date_input(
                "Date",
                value=datetime.today()
            )

            entry_type = st.radio(
                "Fill Type",
                ["Full tank", "Partial"],
                horizontal=True
            )

            note = st.text_input(
                "Note (optional)",
                placeholder="Add any additional notes..."
            )

            submit = st.form_submit_button("➕ Add Entry")

            if submit:
                if amount > 0:
                    try:
                        # Build entry dict
                        entry_dict = {
                            "id": str(uuid.uuid4()),
                            "paidByUid": paid_by_uid,
                            "paidByName": members[paid_by_uid],
                            "amount": amount,
                            "date": date,  # Will be converted to Timestamp by Firestore
                            "type": "full" if entry_type == "Full tank" else "partial",
                            "note": note,
                            "createdAt": datetime.now()
                        }

                        # Write to entries subcollection
                        entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
                        entries_ref.document(entry_dict["id"]).set(entry_dict)

                        # Call recompute_balance
                        recompute_balance(selected_trip_id, db)

                        st.success(f"Entry added — ₹{int(amount):,} logged")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add entry: {e}")
                else:
                    st.error("Please enter an amount greater than zero")
    else:
        st.info("No members in this trip. Please add members first.")

# Tab 3 — Edit Entry
with tab3:
    if entries_list:
        # Create entry options for selectbox
        entry_options = {}

        for entry in entries_list:
            # Format as "DD MMM YYYY — PaidByName — ₹amount"
            date_val = entry.get("date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%d %b %Y")
            elif isinstance(date_val, str):
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%d %b %Y")
                except:
                    date_str = str(date_val) if date_val else ""
            else:
                date_str = str(date_val) if date_val else ""

            paid_by_uid = entry.get("paidByUid", "")
            paid_by_name = members.get(paid_by_uid, paid_by_uid)

            amount = entry.get("amount", 0)
            amount_formatted = f"₹{int(amount):,}"

            display_text = f"{date_str} — {paid_by_name} — {amount_formatted}"
            entry_options[display_text] = entry["id"]

        if entry_options:
            selected_display = st.selectbox(
                "Select an entry to edit",
                options=list(entry_options.keys()),
                key="edit_entry_select"
            )

            if selected_display:
                entry_id = entry_options[selected_display]
                # Find the selected entry
                selected_entry = None
                for entry in entries_list:
                    if entry["id"] == entry_id:
                        selected_entry = entry
                        break

                if selected_entry:
                    # Prefill form with current values
                    with st.form("edit_entry"):
                        # Date
                        date_val = selected_entry.get("date")
                        if hasattr(date_val, 'date'):
                            # It's a datetime object
                            default_date = date_val.date()
                        elif isinstance(date_val, str):
                            try:
                                from datetime import datetime
                                date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                                default_date = date_obj.date()
                            except:
                                default_date = datetime.today().date()
                        else:
                            default_date = datetime.today().date()

                        edit_date = st.date_input(
                            "Date",
                            value=default_date
                        )

                        # Paid By
                        current_paid_by_uid = selected_entry.get("paidByUid", "")
                        member_uids = list(members.keys())

                        try:
                            current_index = member_uids.index(current_paid_by_uid)
                        except (ValueError, AttributeError):
                            current_index = 0 if member_uids else 0

                        edit_paid_by_uid = st.selectbox(
                            "Paid By",
                            options=member_uids,
                            format_func=lambda uid: members[uid],
                            index=current_index if member_uids else 0
                        )

                        # Amount
                        current_amount = selected_entry.get("amount", 0)
                        edit_amount = st.number_input(
                            "Amount (₹)",
                            min_value=0.01,
                            step=10.0,
                            value=current_amount
                        )

                        # Type
                        current_type = selected_entry.get("type", "full")
                        type_options = ["Full tank", "Partial"]
                        try:
                            current_type_index = type_options.index(
                                "Full tank" if current_type == "full" else "Partial"
                            )
                        except (ValueError, AttributeError):
                            current_type_index = 0

                        edit_entry_type = st.radio(
                            "Fill Type",
                            type_options,
                            horizontal=True,
                            index=current_type_index
                        )

                        # Note
                        current_note = selected_entry.get("note", "")
                        edit_note = st.text_input(
                            "Note (optional)",
                            value=current_note
                        )

                        submit = st.form_submit_button("💾 Save Changes")

                        if submit:
                            try:
                                # Build update dict
                                update_dict = {
                                    "date": edit_date,
                                    "paidByUid": edit_paid_by_uid,
                                    "paidByName": members[edit_paid_by_uid],
                                    "amount": edit_amount,
                                    "type": "full" if edit_entry_type == "Full tank" else "partial",
                                    "note": edit_note
                                }

                                # Update entry doc
                                entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
                                entries_ref.document(entry_id).update(update_dict)

                                # Call recompute_balance
                                recompute_balance(selected_trip_id, db)

                                st.success("Entry updated")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to update entry: {e}")
        else:
            st.info("No entries available to edit")
    else:
        st.info("No entries found")

# Tab 4 — Delete Entry
with tab4:
    if entries_list:
        # Create entry options for selectbox (same format as Tab 3)
        entry_options = {}

        for entry in entries_list:
            # Format as "DD MMM YYYY — PaidByName — ₹amount"
            date_val = entry.get("date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%d %b %Y")
            elif isinstance(date_val, str):
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%d %b %Y")
                except:
                    date_str = str(date_val) if date_val else ""
            else:
                date_str = str(date_val) if date_val else ""

            paid_by_uid = entry.get("paidByUid", "")
            paid_by_name = members.get(paid_by_uid, paid_by_uid)

            amount = entry.get("amount", 0)
            amount_formatted = f"₹{int(amount):,}"

            display_text = f"{date_str} — {paid_by_name} — {amount_formatted}"
            entry_options[display_text] = entry["id"]

        if entry_options:
            selected_display = st.selectbox(
                "Select an entry to delete",
                options=list(entry_options.keys()),
                key="delete_entry_select"
            )

            if selected_display:
                entry_id = entry_options[selected_display]
                # Find the selected entry
                selected_entry = None
                for entry in entries_list:
                    if entry["id"] == entry_id:
                        selected_entry = entry
                        break

                if selected_entry:
                    # Show entry details
                    date_val = selected_entry.get("date")
                    if hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime("%d %b %Y")
                    elif isinstance(date_val, str):
                        try:
                            from datetime import datetime
                            date_obj = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                            date_str = date_obj.strftime("%d %b %Y")
                        except:
                            date_str = str(date_val) if date_val else ""
                    else:
                        date_str = str(date_val) if date_val else ""

                    paid_by_uid = selected_entry.get("paidByUid", "")
                    paid_by_name = members.get(paid_by_uid, paid_by_uid)

                    amount = selected_entry.get("amount", 0)
                    amount_formatted = f"₹{int(amount):,}"

                    entry_type = selected_entry.get("type", "")

                    st.warning(f"""
                    **About to delete entry:**
                    - Date: {date_str}
                    - Paid By: {paid_by_name}
                    - Amount: {amount_formatted}
                    - Type: {entry_type}
                    - Note: {selected_entry.get('note', '')}

                    This action cannot be undone!
                    """)

                    confirm = st.checkbox("I confirm I want to delete this entry")

                    if st.button("🗑️ Delete Entry", disabled=not confirm):
                        try:
                            # Delete entry doc
                            entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
                            entries_ref.document(entry_id).delete()

                            # Call recompute_balance
                            recompute_balance(selected_trip_id, db)

                            st.success("Entry deleted and balance recalculated")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete entry: {e}")
        else:
            st.info("No entries available to delete")
    else:
        st.info("No entries found")