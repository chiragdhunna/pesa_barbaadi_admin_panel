import streamlit as st
import pandas as pd
from services.firebase_service import init_firebase
from firebase_admin import firestore

# Auth check + Firebase init at top
if not st.session_state.get("authenticated"):
    st.warning("Please log in to access the users page")
    st.stop()

try:
    db, auth_client = init_firebase()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()

st.title("👥 Users")

# Fetch all users: iterate auth_client.list_users().iterate_all()
try:
    # Build a list of dicts for display
    users_list = []
    for user in auth_client.list_users().iterate_all():
        users_list.append({
            "uid": user.uid,
            "display_name": user.display_name or "",
            "email": user.email or "",
            "created_at": user.user_metadata.creation_timestamp if hasattr(user.user_metadata, 'creation_timestamp') else "",
            "last_sign_in": user.user_metadata.last_sign_in_timestamp if hasattr(user.user_metadata, 'last_sign_in_timestamp') else "",
            "disabled": user.disabled
        })

    # Display total users metric
    st.metric("Total Users", len(users_list))

except Exception as e:
    st.error(f"Failed to fetch users: {e}")
    st.stop()

# Create tabs
tab1, tab2, tab3 = st.tabs(["All Users", "Edit User", "Delete User"])

# Tab 1 — All Users
with tab1:
    if users_list:
        # Convert to DataFrame for display
        df_data = []
        for user in users_list:
            # Format timestamps
            created_str = ""
            if user["created_at"]:
                try:
                    # Firestore timestamps are in microseconds since epoch
                    created_dt = pd.to_datetime(user["created_at"], unit='ms')
                    created_str = created_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    created_str = str(user["created_at"])

            last_sign_in_str = ""
            if user["last_sign_in"]:
                try:
                    last_sign_in_dt = pd.to_datetime(user["last_sign_in"], unit='ms')
                    last_sign_in_str = last_sign_in_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    last_sign_in_str = str(user["last_sign_in"])

            # Status
            status = "🚫 Disabled" if user["disabled"] else "✅ Active"

            df_data.append({
                "Display Name": user["display_name"] or "(No name)",
                "Email": user["email"] or "(No email)",
                "UID": user["uid"],
                "Created": created_str,
                "Last Sign-In": last_sign_in_str,
                "Status": status
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found")

# Tab 2 — Edit User
with tab2:
    if users_list:
        # Create user_options dict mapping "Name (email)" → uid
        user_options = {}
        for user in users_list:
            name = user["display_name"] or "(No name)"
            email = user["email"] or "(No email)"
            display_text = f"{name} ({email})"
            user_options[display_text] = user["uid"]

        if user_options:
            selected_display = st.selectbox(
                "Select a user to edit",
                options=list(user_options.keys()),
                key="edit_user_select"
            )

            if selected_display:
                uid = user_options[selected_display]
                # Find the selected user
                selected_user = None
                for user in users_list:
                    if user["uid"] == uid:
                        selected_user = user
                        break

                if selected_user:
                    # Show current values
                    st.info(f"""
                    **Current Values:**
                    - Display Name: {selected_user['display_name'] or '(No name)'}
                    - Email: {selected_user['email'] or '(No email)'}
                    - UID: {selected_user['uid']}
                    - Status: {'Disabled' if selected_user['disabled'] else 'Active'}
                    """)

                    # Edit form
                    with st.form("edit_user"):
                        new_display_name = st.text_input(
                            "Display Name",
                            value=selected_user['display_name'] or ""
                        )
                        new_email = st.text_input(
                            "Email",
                            value=selected_user['email'] or ""
                        )
                        submit = st.form_submit_button("Save Changes")

                        if submit:
                            try:
                                update_params = {}
                                if new_display_name is not None:
                                    update_params["display_name"] = new_display_name
                                if new_email is not None:
                                    update_params["email"] = new_email

                                if update_params:  # Only update if there are changes
                                    auth_client.update_user(uid, **update_params)
                                    st.success("User updated")
                                    st.rerun()
                                else:
                                    st.info("No changes to save")
                            except Exception as e:
                                st.error(f"Failed to update user: {e}")

                    # Below form - two columns for actions
                    col1, col2 = st.columns(2)

                    with col1:
                        # Disable/Enable button
                        if selected_user['disabled']:
                            if st.button("Enable User", key=f"enable_{uid}"):
                                try:
                                    auth_client.update_user(uid, disabled=False)
                                    st.success("User enabled")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to enable user: {e}")
                        else:
                            if st.button("Disable User", key=f"disable_{uid}"):
                                try:
                                    auth_client.update_user(uid, disabled=True)
                                    st.success("User disabled")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to disable user: {e}")

                    with col2:
                        # Send Password Reset button
                        if st.button("Send Password Reset", key=f"reset_{uid}"):
                            try:
                                if selected_user['email']:
                                    reset_link = auth_client.generate_password_reset_link(selected_user['email'])
                                    st.info("Password reset link generated")
                                    st.code(reset_link)
                                else:
                                    st.error("User has no email address")
                            except Exception as e:
                                st.error(f"Failed to generate password reset link: {e}")
        else:
            st.info("No users available to edit")
    else:
        st.info("No users found")

# Tab 3 — Delete User
with tab3:
    if users_list:
        # Create user_options dict for deletion
        user_options_del = {}
        for user in users_list:
            name = user["display_name"] or "(No name)"
            email = user["email"] or "(No email)"
            display_text = f"{name} ({email})"
            user_options_del[display_text] = user["uid"]

        if user_options_del:
            selected_display_del = st.selectbox(
                "Select a user to delete",
                options=list(user_options_del.keys()),
                key="delete_user_select"
            )

            if selected_display_del:
                uid = user_options_del[selected_display_del]
                # Find the selected user
                selected_user_del = None
                for user in users_list:
                    if user["uid"] == uid:
                        selected_user_del = user
                        break

                if selected_user_del:
                    # Show warning with user details
                    st.warning(f"""
                    **About to delete:**
                    - Display Name: {selected_user_del['display_name'] or '(No name)'}
                    - Email: {selected_user_del['email'] or '(No email)'}
                    - UID: {selected_user_del['uid']}

                    This action cannot be undone!
                    """)

                    confirm = st.checkbox("I confirm I want to permanently delete this user")

                    if st.button("🗑️ Delete User", disabled=not confirm):
                        try:
                            auth_client.delete_user(uid)
                            st.success("User deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete user: {e}")
        else:
            st.info("No users available to delete")
    else:
        st.info("No users found")