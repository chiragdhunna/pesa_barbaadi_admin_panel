---
name: Export page implementation
description: Data export page for exporting trip data in Excel, PDF, and CSV formats
type: project
---

Created pages/5_Export.py with full implementation of the data export interface:

**Authentication & Firebase Init:**
- Auth check at top: verifies st.session_state.get("authenticated")
- Firebase initialization via init_firebase() from services.firebase_service
- Both wrapped in try/except with st.error() on failure
- Imports generate_excel, generate_pdf, generate_csv from services.export_service

**Layout:**
- Two-column layout using st.columns([1, 2])
- Left column: Controls (trip selector, date range, format selection)
- Right column: Preview (metrics, first 5 entries preview, balance summary)
- Divider followed by download section

**Controls (Left Column):**
- Trip Selector:
  - Fetches all trips via db.collection("trips").stream()
  - Builds options dict {tripId: trip data}
  - Uses st.selectbox with format_func showing "Trip {id}"
- Date Range:
  - From date: st.date_input (value=None, help text)
  - To date: st.date_input (value=None, help text)
- Export Format:
  - st.radio(["Excel", "PDF", "CSV"], horizontal=True)

**Preview (Right Column):**
- If trip selected:
  - Gets trip data and members dict
  - Fetches all entries for selected trip via entries subcollection
  - Filters entries by date range if provided (converts dates to date objects for comparison)
  - Shows metrics:
    * Total Entries: len(filtered_entries)
    * Total ₹ Spent: sum of amounts formatted as "₹{total:,.0f}"
  - Preview section:
    * Shows first 5 entries as DataFrame with columns: Date, Paid By, Amount (₹), Type, Note
    * Date formatted as DD MMM YYYY
    * Amount formatted as ₹X,XXX
  - Balance summary:
    * Shows who owes whom with error/success messaging
    * Handles empty balance case

**Download Section (Below Divider):**
- Only shown if a trip is selected
- Re-applies date filtering to entries (same logic as preview)
- Based on export_format selection:
  * Excel:
    - Calls generate_excel(filtered_entries, selected_trip_id, members)
    - Download button with label "⬇️ Download Excel"
    - File name: pesa_barbaadi_{selected_trip_id}.xlsx
    - MIME: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  * PDF:
    - Calls generate_pdf(filtered_entries, selected_trip_id, members, str(date_from), str(date_to))
    - Download button with label "⬇️ Download PDF"
    - File name: pesa_barbaadi_{selected_trip_id}.pdf
    - MIME: application/pdf
  * CSV:
    - Calls generate_csv(filtered_entries)
    - Download button with label "⬇️ Download CSV"
    - File name: pesa_barbaadi_{selected_trip_id}.csv
    - MIME: text/csv
- All download buttons use use_container_width=True for full-width buttons
- If no filtered entries: shows st.warning("No entries found for the selected trip and date range.")

**Error Handling:**
- All Firebase/Firestore calls wrapped in try/except blocks
- Shows descriptive st.error() messages on failure
- Includes proper date parsing with fallbacks for invalid formats
- Validates that entries exist before generating exports

**Why:** Provides administrators with a complete interface to export trip data in multiple formats with date filtering and preview capabilities. Users can select a trip, optionally filter by date range, preview the data, and download in Excel, PDF, or CSV format.

**How to apply:** Access via streamlit navigation after authentication. Select a trip from the dropdown, optionally set date range, choose export format, preview the data, and click the corresponding download button. The exported files will contain properly formatted data with headers, formatting, and calculations as specified in the export service.