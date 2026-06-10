import streamlit as st
from services.firebase_service import init_firebase
from services.export_service import generate_excel, generate_pdf, generate_csv
from firebase_admin import firestore
from datetime import datetime

try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("📥 Export Data")

# Layout: two columns
col_left, col_right = st.columns([1, 2])

# Left column — Controls
with col_left:
    # Fetch all trips for selectbox
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

        # Build trip options dict
        trip_options = {trip["id"]: trip for trip in trips_data}

        selected_trip_id = st.selectbox(
            "Select a trip",
            options=list(trip_options.keys()),
            format_func=lambda x: f"Trip {x}"
        )

        date_from = st.date_input(
            "From date",
            value=None,
            help="Leave empty for no lower bound"
        )

        date_to = st.date_input(
            "To date",
            value=None,
            help="Leave empty for no upper bound"
        )

        export_format = st.radio(
            "Format",
            ["Excel", "PDF", "CSV"],
            horizontal=True
        )

    except Exception as e:
        st.error(f"Failed to load trips: {e}")
        st.stop()

# Right column — Preview
with col_right:
    if selected_trip_id:
        try:
            # Get trip data
            trip = trip_options[selected_trip_id]
            members = trip.get("members", {})

            # Fetch all entries for selected trip
            entries_ref = db.collection("trips").document(selected_trip_id).collection("entries")
            entries_stream = list(entries_ref.stream())

            # Convert to list of dicts
            entries_list = []
            for entry_doc in entries_stream:
                entry_dict = entry_doc.to_dict()
                entry_dict["id"] = entry_doc.id
                entries_list.append(entry_dict)

            # Filter entries by date range if provided
            filtered_entries = entries_list
            if date_from or date_to:
                filtered_entries = []
                for entry in entries_list:
                    entry_date = entry.get("date")
                    if entry_date:
                        # Convert to date object for comparison
                        if hasattr(entry_date, 'date'):
                            entry_date_only = entry_date.date()
                        elif isinstance(entry_date, str):
                            try:
                                entry_date_only = datetime.fromisoformat(
                                    entry_date.replace('Z', '+00:00')
                                ).date()
                            except:
                                continue  # Skip if date parsing fails
                        else:
                            continue

                        # Check date range
                        if date_from and entry_date_only < date_from:
                            continue
                        if date_to and entry_date_only > date_to:
                            continue

                        filtered_entries.append(entry)

            # Show metrics
            if filtered_entries:
                total_entries = len(filtered_entries)
                total_spent = sum(entry.get("amount", 0) for entry in filtered_entries)

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Total Entries", total_entries)
                with metric_col2:
                    st.metric("Total ₹ Spent", f"₹{total_spent:,.0f}")

                # Preview first 5 entries
                st.subheader("Preview (first 5 entries)")
                preview_entries = filtered_entries[:5]

                if preview_entries:
                    # Build DataFrame for preview
                    preview_data = []
                    for entry in preview_entries:
                        # Date formatting
                        date_val = entry.get("date")
                        if hasattr(date_val, 'strftime'):
                            date_str = date_val.strftime("%d %b %Y")
                        elif isinstance(date_val, str):
                            try:
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
                        amount_formatted = f"₹{int(amount):,}"

                        # Type and Note
                        entry_type = entry.get("type", "")
                        note = entry.get("note", "")

                        preview_data.append({
                            "Date": date_str,
                            "Paid By": paid_by_name,
                            "Amount": amount_formatted,
                            "Type": entry_type,
                            "Note": note
                        })

                    if preview_data:
                        import pandas as pd
                        preview_df = pd.DataFrame(preview_data)
                        st.dataframe(preview_df, use_container_width=True)
                    else:
                        st.info("No preview data available")
                else:
                    st.info("No entries to preview")

                # Show balance summary
                balance = trip.get("balance", {})
                if not balance:  # Empty balance
                    st.info("ℹ️ No balance data available")
                else:
                    from services.balance_service import parse_balance
                    owed_by, owed_to, amount_owed = parse_balance(balance)

                    if owed_to and owed_by and amount_owed > 0:
                        owed_to_name = members.get(owed_to, owed_to)
                        owed_by_name = members.get(owed_by, owed_by)
                        st.error(f"💸 {owed_by_name} owes {owed_to_name} ₹{int(amount_owed):,.0f}")
                    else:
                        st.info("✓ All settled")
            else:
                st.info("No entries found for the selected trip")
                st.info("💡 Add some entries first to see preview and export options")

        except Exception as e:
            st.error(f"Failed to load entries: {e}")
    else:
        st.info("Select a trip to see preview and export options")

# Divider and download section
st.divider()

if selected_trip_id:
    try:
        # Get trip members dict
        trip = trip_options[selected_trip_id]
        members = trip.get("members", {})

        # Filter entries by date range (same logic as preview)
        filtered_entries = entries_list if 'entries_list' in locals() else []
        if date_from or date_to:
            filtered_entries = []
            for entry in entries_list:
                entry_date = entry.get("date")
                if entry_date:
                    # Convert to date object for comparison
                    if hasattr(entry_date, 'date'):
                        entry_date_only = entry_date.date()
                    elif isinstance(entry_date, str):
                        try:
                            entry_date_only = datetime.fromisoformat(
                                entry_date.replace('Z', '+00:00')
                            ).date()
                        except:
                            continue  # Skip if date parsing fails
                    else:
                        continue

                    # Check date range
                    if date_from and entry_date_only < date_from:
                        continue
                    if date_to and entry_date_only > date_to:
                        continue

                    filtered_entries.append(entry)

        if export_format == "Excel":
            if filtered_entries:
                data = generate_excel(filtered_entries, selected_trip_id, members)
                st.download_button(
                    label="⬇️ Download Excel",
                    data=data,
                    file_name=f"pesa_barbaadi_{selected_trip_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("No entries found for the selected trip and date range.")

        elif export_format == "PDF":
            if filtered_entries:
                data = generate_pdf(filtered_entries, selected_trip_id, members,
                                 str(date_from) if date_from else "",
                                 str(date_to) if date_to else "")
                st.download_button(
                    label="⬇️ Download PDF",
                    data=data,
                    file_name=f"pesa_barbaadi_{selected_trip_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("No entries found for the selected trip and date range.")

        elif export_format == "CSV":
            if filtered_entries:
                data = generate_csv(filtered_entries)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=data,
                    file_name=f"pesa_barbaadi_{selected_trip_id}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No entries found for the selected trip and date range.")

    except Exception as e:
        st.error(f"Failed to prepare export: {e}")
else:
    st.info("Select a trip to enable export options")