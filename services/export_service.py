import io
from datetime import datetime
from typing import List, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_excel(entries: list, trip_id: str, member_names: dict) -> io.BytesIO:
    """
    Generate Excel report for trip entries.

    Args:
        entries: List of entry dictionaries
        trip_id: ID of the trip
        member_names: Dictionary mapping user IDs to names

    Returns:
        BytesIO object containing the Excel file
    """
    # Create workbook and select active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Entries"

    # Define styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="5B7FFF", end_color="5B7FFF", fill_type="solid")
    bold_font = Font(bold=True)
    center_alignment = Alignment(horizontal="center")

    # Add headers
    headers = ["Date", "Paid By", "Amount (₹)", "Type", "Note"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    # Add data rows
    row_num = 2
    for entry in entries:
        # Date as DD MMM YYYY string
        date_str = entry.get("date", "")
        if isinstance(date_str, str):
            try:
                # Try to parse ISO date string
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_display = date_obj.strftime("%d %b %Y")
            except:
                date_display = date_str
        else:
            date_display = str(date_str) if date_str else ""

        # Paid by name
        paid_by_uid = entry.get("paidByUid", "")
        paid_by_name = member_names.get(paid_by_uid, paid_by_uid)

        # Amount as float
        amount = float(entry.get("amount", 0))

        # Type and note
        entry_type = entry.get("type", "")
        note = entry.get("note", "")

        # Add row data
        ws.cell(row=row_num, column=1, value=date_display)
        ws.cell(row=row_num, column=2, value=paid_by_name)
        ws.cell(row=row_num, column=3, value=amount)
        ws.cell(row=row_num, column=4, value=entry_type)
        ws.cell(row=row_num, column=5, value=note)

        # Center align date and type cells
        ws.cell(row=row_num, column=1).alignment = center_alignment
        ws.cell(row=row_num, column=4).alignment = center_alignment

        row_num += 1

    # Calculate subtotals per member
    if entries:
        subtotals = {}
        for entry in entries:
            paid_by_uid = entry.get("paidByUid", "")
            amount = float(entry.get("amount", 0))
            subtotals[paid_by_uid] = subtotals.get(paid_by_uid, 0) + amount

        # Add subtotal rows
        subtotal_row = row_num + 1
        ws.cell(row=subtotal_row, column=1, value="Subtotals").font = bold_font
        ws.cell(row=subtotal_row, column=2, value="").font = bold_font

        col_offset = 3
        for uid, member_name in member_names.items():
            if uid in subtotals:
                ws.cell(row=subtotal_row, column=col_offset, value=subtotals[uid]).font = bold_font
                col_offset += 1

        # Add grand total
        grand_total = sum(subtotals.values())
        ws.cell(row=subtotal_row + 1, column=1, value="Grand Total").font = bold_font
        ws.cell(row=subtotal_row + 1, column=2, value="").font = bold_font
        ws.cell(row=subtotal_row + 1, column=3, value=grand_total).font = bold_font

        # Adjust row numbers for column width calculation
        max_row = subtotal_row + 2
    else:
        max_row = row_num - 1

    # Auto-fit column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to BytesIO
    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    return excel_buffer


def generate_pdf(entries, trip_id: str, member_names: dict, date_from: str, date_to: str) -> io.BytesIO:
    """
    Generate PDF report for trip entries.

    Args:
        entries: List of entry dictionaries
        trip_id: ID of the trip
        member_names: Dictionary mapping user IDs to names
        date_from: Start date string
        date_to: End date string

    Returns:
        BytesIO object containing the PDF file
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Build story (content)
    story = []

    # Title
    title = Paragraph("Pesa Barbaadi — Trip Report", title_style)
    story.append(title)

    # Subtitle
    subtitle_text = f"Trip ID: {trip_id} | Period: {date_from} to {date_to}"
    subtitle = Paragraph(subtitle_text, subtitle_style)
    story.append(subtitle)

    # Spacer
    story.append(Spacer(1, 20))

    # Calculate member statistics
    member_stats = {}
    total_spent = 0

    for entry in entries:
        paid_by_uid = entry.get("paidByUid", "")
        amount = float(entry.get("amount", 0))
        member_name = member_names.get(paid_by_uid, paid_by_uid)

        if paid_by_uid not in member_stats:
            member_stats[paid_by_uid] = {
                'name': member_name,
                'paid': 0,
                'entries': 0
            }

        member_stats[paid_by_uid]['paid'] += amount
        member_stats[paid_by_uid]['entries'] += 1
        total_spent += amount

    # Fair share (assuming 2 members)
    fair_share = total_spent / 2.0 if len(member_names) >= 2 else total_spent

    # Summary table
    if member_stats:
        summary_data = [["Member", "Amount Paid (₹)", "Fair Share (₹)", "Balance (₹)"]]

        for uid, stats in member_stats.items():
            amount_paid = stats['paid']
            balance = amount_paid - fair_share
            summary_data.append([
                stats['name'],
                f"{amount_paid:.2f}",
                f"{fair_share:.2f}",
                f"{balance:.2f}"
            ])

        # Add total row
        summary_data.append(["TOTAL", f"{total_spent:.2f}", f"{fair_share * len(member_names):.2f}", ""])

        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 20))

    # Entries table
    if entries:
        entries_data = [["Date", "Paid By", "Amount (₹)", "Type", "Note"]]

        for i, entry in enumerate(entries):
            # Date formatting
            date_str = entry.get("date", "")
            if isinstance(date_str, str):
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = date_obj.strftime("%d %b %Y")
                except:
                    date_display = date_str
            else:
                date_display = str(date_str) if date_str else ""

            # Paid by
            paid_by_uid = entry.get("paidByUid", "")
            paid_by_name = member_names.get(paid_by_uid, paid_by_uid)

            # Amount
            amount = float(entry.get("amount", 0))

            # Type and note
            entry_type = entry.get("type", "")
            note = entry.get("note", "")

            entries_data.append([
                date_display,
                paid_by_name,
                f"{amount:.2f}",
                entry_type,
                note
            ])

        # Create entries table with alternating row colors
        entries_table = Table(entries_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 2*inch])

        # Build table style
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]

        # Add alternating row colors
        for i in range(1, len(entries_data)):
            if i % 2 == 0:  # Even rows (0-indexed, so these are odd-numbered rows)
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))

        entries_table.setStyle(TableStyle(table_style))
        story.append(entries_table)

    # Footer
    story.append(Spacer(1, 30))
    today_str = datetime.now().strftime("%d %b %Y")
    footer = Paragraph(f"Generated on {today_str}", styles['Normal'])
    footer.alignment = TA_CENTER
    story.append(footer)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer


def generate_csv(entries: list) -> str:
    """
    Generate CSV report for trip entries.

    Args:
        entries: List of entry dictionaries

    Returns:
        String containing CSV data
    """
    # Define headers
    headers = ["id", "paidByName", "paidByUid", "amount", "date", "type", "note", "createdAt"]

    # If no entries, return header only
    if not entries:
        return ",".join(headers)

    # Build CSV lines
    lines = [",".join(headers)]

    for entry in entries:
        # Get values with defaults for missing fields
        entry_id = str(entry.get("id", ""))
        paid_by_name = str(entry.get("paidByName", ""))
        paid_by_uid = str(entry.get("paidByUid", ""))
        amount = str(entry.get("amount", ""))
        date_val = entry.get("date", "")

        # Convert date to ISO string if it's a datetime object
        if hasattr(date_val, 'isoformat'):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val) if date_val else ""

        entry_type = str(entry.get("type", ""))
        note = str(entry.get("note", ""))
        created_at = entry.get("createdAt", "")

        # Convert createdAt to ISO string if needed
        if hasattr(created_at, 'isoformat'):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at) if created_at else ""

        # Create CSV row (escape quotes and commas if needed)
        row = [
            f'"{entry_id}"' if ',' in entry_id or '"' in entry_id else entry_id,
            f'"{paid_by_name}"' if ',' in paid_by_name or '"' in paid_by_name else paid_by_name,
            f'"{paid_by_uid}"' if ',' in paid_by_uid or '"' in paid_by_uid else paid_by_uid,
            amount,  # Amount is numeric, usually safe
            f'"{date_str}"' if ',' in date_str or '"' in date_str else date_str,
            f'"{entry_type}"' if ',' in entry_type or '"' in entry_type else entry_type,
            f'"{note}"' if ',' in note or '"' in note else note,
            f'"{created_at_str}"' if ',' in created_at_str or '"' in created_at_str else created_at_str
        ]

        lines.append(",".join(row))

    return "\n".join(lines)