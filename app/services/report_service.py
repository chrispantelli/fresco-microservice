from datetime import datetime
from io import BytesIO
import os, json
from typing import Any
from fastapi import Depends, HTTPException
from supabase import Client

from app.helpers.supabase import superset_client
from app.constants.reports import REPORT_TYPES
from app.utils import current_date_epoch, format_date

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportService:
    def __init__(self, supabase: Client = Depends(superset_client)):
        self.supabase = supabase
    
    async def generate(self, report_id: str, body: dict[str, Any]):
        try:
            response = self.supabase.table("tblreports").select("*").eq("id", report_id).execute()
            data = response.data[0]["body"]
            
            if response.data[0]["type"] == "release-form":
                title = body['storage_company']
                pdf = generate_release_form(data, title)
            elif response.data[0]["type"] == "collection-form":
                title = body['transport_company']
                pdf = generate_collection_form(data, title)
            elif response.data[0]["type"] == "customer-sale-form":
                title = body['customer_name']
                pdf = generate_customer_sale_form(data, title)
            else:
                raise HTTPException(status_code=500, detail="No report type exists.")
                        
            upload_file = self.supabase.storage.from_("generated-reports").upload(
                path=f"{report_id}-{current_date_epoch()}.pdf",
                file=pdf,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            
            if not upload_file:
                raise HTTPException(status_code=500, detail="Failed to upload PDF.")
            
            public_url = (
                f"{os.environ.get('SUPABASE_URL')}/storage/v1/object/public/"
                f"{upload_file.full_path}"
            )
            
            updated_generated_pdf = self.supabase.table("tblreports").update({ "generated_pdf": public_url }).eq("id", report_id).execute()

            if updated_generated_pdf:
                return public_url
            
            raise HTTPException(status_code=500, detail=str("Unable to generate PDF."))
        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

def header_with_line(canvas, doc, title):
    canvas.saveState()
    canvas.setStrokeColor(colors.grey)
    canvas.setLineWidth(0.5)

    page_width, page_height = doc.pagesize

    header_y = page_height - 30

    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.grey)

    canvas.drawString(20, header_y, "Fresco Fisheries (UK) Limited")

    today = datetime.now().strftime("%d %B %Y")

    center_text = title
    canvas.drawCentredString(page_width / 2, header_y, center_text)

    canvas.drawRightString(page_width - 20, header_y, today)

    line_y = header_y - 10
    canvas.line(20, line_y, page_width - 20, line_y)

    logo_path = os.path.join(os.getcwd(), "app", "assets", "logo.jpeg")
    logo_width = 160
    logo_height = 60

    logo_x = doc.leftMargin - 10
    logo_y = line_y - logo_height - 15
    
    canvas.drawImage(
        logo_path,
        logo_x,
        logo_y,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=True,
        mask="auto"
    )

    canvas.restoreState()
    
def footer_with_line(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.grey)
    canvas.setLineWidth(0.5)

    page_width = doc.pagesize[0]

    canvas.line(20, 35, page_width - 20, 35)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20, 20, f"Fresco Fisheries (UK) Limited - Sopers Road, Cuffley, Herts, EN6 4RY")
    canvas.drawRightString(page_width - 20, 20, f"Page {doc.page}")

    canvas.restoreState()

def generate_release_form(data, title):
    if isinstance(data, str):
        data = json.loads(data)

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]

    table_text = ParagraphStyle(
        "table_text",
        parent=normal,
        fontSize=9,
        leading=11
    )

    doc = SimpleDocTemplate(
        buffer,
        topMargin=120,
        bottomMargin=50,
        leftMargin=20,
        rightMargin=20,
    )
    story = []
    for idx, group in enumerate(data):
        story.append(Paragraph(f"For products dispatched on {format_date(group['production_date'])}", styles["Heading4"]))
        story.append(Spacer(1, 12))

        rows = [
            [
                Paragraph("Customer / AWB", table_text),
                Paragraph("Transport", table_text),
                Paragraph("Product", table_text),
                Paragraph("Box No", table_text),
                Paragraph("Weight (Kgs)", table_text),
            ]
        ]

        customer_header_row_indices = []
        totals_row_indices = []

        for customer in group["customers"]:
            customer_name = customer["customer_name"] or "Unallocated"

            customer_header_row_indices.append(len(rows))
            rows.append([
                Paragraph(customer_name, table_text),
                "", "", "", ""
            ])

            total_boxes = 0
            total_weight = 0

            for awb in customer["awbs"]:
                for item in awb["shipment_items"]:
                    box_no = item["box_number"]
                    weight = item["net_weight"]

                    total_boxes += box_no
                    total_weight += weight

                    rows.append([
                        Paragraph(f"AWB: {awb['awb']}", table_text),
                        Paragraph(item.get("transport_company", "-"), table_text),
                        Paragraph(item["product"], table_text),
                        Paragraph(str(box_no), table_text),
                        Paragraph(f"{str(weight)}kg", table_text),
                    ])

            # --- Totals row for this customer ---
            totals_row_indices.append(len(rows))
            rows.append([
                Paragraph("Totals", table_text),
                "",
                "",
                Paragraph(str(total_boxes), table_text),
                Paragraph(f"{total_weight}kg", table_text),
            ])

        # Build the table once per date
        table = Table(
            rows,
            colWidths=[110, 90, 260, 40, 45],  # tweak to taste
            repeatRows=1,
        )

        # Base styles
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]

        # Style for each customer separator row
        for r in customer_header_row_indices:
            style_commands.extend([
                ("SPAN", (0, r), (-1, r)),                      # span all 5 columns
                ("BACKGROUND", (0, r), (-1, r), colors.whitesmoke),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        table.setStyle(TableStyle(style_commands))

        story.append(table)
        story.append(Spacer(1, 16))

    doc.build(
        story, 
        onFirstPage=lambda c, d: (header_with_line(c, d, f"Release Form Report - {title}" ), footer_with_line(c, d)), 
        onLaterPages=lambda c, d: (header_with_line(c, d, f"Release Form Report - {title}"), footer_with_line(c, d)),
    )
    buffer.seek(0)
    return buffer.getvalue()

def generate_collection_form(data, title):
    if isinstance(data, str):
        data = json.loads(data)

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]

    table_text = ParagraphStyle(
        "table_text",
        parent=normal,
        fontSize=9,
        leading=11
    )

    doc = SimpleDocTemplate(
        buffer,
        topMargin=120,
        bottomMargin=50,
        leftMargin=20,
        rightMargin=20,
    )

    story = []

    for idx, group in enumerate(data):
        story.append(Paragraph(f"For products dispatched on {format_date(group['production_date'])}", styles["Heading4"]))
        story.append(Spacer(1, 12))

        rows = [
            [
                Paragraph("Customer / AWB", table_text),
                Paragraph("Collection Point", table_text),
                Paragraph("Box No", table_text),
                Paragraph("Weight", table_text)
            ]
        ]

        customer_header_row_indices = []
        totals_row_indices = []

        for customer in group["customers"]:
            customer_name = customer["customer_name"] or "Unallocated"

            customer_header_row_indices.append(len(rows))
            rows.append([
                Paragraph(customer_name, table_text),
                "", "", ""
            ])

            total_boxes = 0
            total_weight = 0

            for awb in customer["awbs"]:
                for item in awb["shipment_items"]:
                    box_no = item["box_number"]
                    weight = item["net_weight"]

                    total_boxes += box_no
                    total_weight += weight

                    rows.append([
                        Paragraph(f"AWB: {awb['awb']}", table_text),
                        Paragraph(item["storage_company"], table_text),
                        Paragraph(str(box_no), table_text),
                        Paragraph(f"{str(weight)}kg", table_text)
                    ])

            # --- Totals row for this customer ---
            totals_row_indices.append(len(rows))
            rows.append([
                Paragraph("Totals", table_text),
                "",
                Paragraph(str(total_boxes), table_text),
                Paragraph(f"{str(total_weight)}kg")
            ])

        # Build the table once per date
        table = Table(
            rows,
            colWidths=[110, 90, 260, 40, 45],  # tweak to taste
            repeatRows=1,
        )

        # Base styles
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]

        # Style for each customer separator row
        for r in customer_header_row_indices:
            style_commands.extend([
                ("SPAN", (0, r), (-1, r)),                      # span all 5 columns
                ("BACKGROUND", (0, r), (-1, r), colors.whitesmoke),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        table.setStyle(TableStyle(style_commands))

        story.append(table)
        story.append(Spacer(1, 16))

    doc.build(
        story, 
        onFirstPage=lambda c, d: (header_with_line(c, d, f"Collection Form Report - {title}"), footer_with_line(c, d)), 
        onLaterPages=lambda c, d: (header_with_line(c, d, f"Collection Form Report - {title}"), footer_with_line(c, d)),
    )
    buffer.seek(0)
    return buffer.getvalue()

def generate_customer_sale_form(data, title):
    if isinstance(data, str):
        data = json.loads(data)

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]

    table_text = ParagraphStyle(
        "table_text",
        parent=normal,
        fontSize=9,
        leading=11
    )

    doc = SimpleDocTemplate(
        buffer,
        topMargin=120,
        bottomMargin=50,
        leftMargin=20,
        rightMargin=20,
    )

    story = []

    for idx, group in enumerate(data):
        story.append(Paragraph(
            f"For products dispatched on {format_date(group['production_date'])}",
            styles["Heading4"],
        ))
        story.append(Spacer(1, 12))

        rows = [
            [
                Paragraph("Customer / AWB", table_text),
                Paragraph("Product", table_text),
                Paragraph("Box No", table_text),
                Paragraph("Weight", table_text),
                Paragraph("Price Per Kg", table_text),
                Paragraph("Total", table_text),
            ]
        ]

        customer_header_row_indices = []
        awb_header_row_indices = []
        product_header_row_indices = []
        totals_row_indices = []

        for customer in group["customers"]:
            customer_name = customer.get("customer_name") or "Unallocated"

            # ---- CUSTOMER (full-width) ----
            customer_header_row_indices.append(len(rows))
            rows.append([
                Paragraph(customer_name, table_text),
                "", "", "", "", "",
            ])

            total_boxes = 0
            total_weight = 0

            for awb in customer["awbs"]:

                # ---- AWB (full-width, like customer but slightly lighter) ----
                awb_header_row_indices.append(len(rows))
                rows.append([
                    Paragraph(f"AWB: {awb['awb']}", table_text),
                    "", "", "", "", "",
                ])

                for product in awb["products"]:

                    product_name = product["product"]

                    # ---- PRODUCT ROW (indent left by leaving col 0 empty) ----
                    product_header_row_indices.append(len(rows))
                    rows.append([
                        "",  # reserved column (same alignment as AWB)
                        Paragraph(product_name, table_text),
                        "", "", "", "",
                    ])

                    # ---- ITEMS ----
                    for item in product["shipment_items"]:
                        box_no = item["box_number"]
                        weight = item["net_weight"]

                        total_boxes += 1
                        total_weight += weight

                        rows.append([
                            "",  # no AWB or customer here (header already shown)
                            "",
                            Paragraph(str(box_no), table_text),
                            Paragraph(f"{weight}kg", table_text),
                            Paragraph(f"£{item['price_per_kg']}", table_text),
                            Paragraph(f"£{item['total']}", table_text),
                        ])

            # ---- Totals for customer ----
            totals_row_indices.append(len(rows))
            rows.append([
                Paragraph("Totals", table_text),
                "",
                Paragraph(str(total_boxes), table_text),
                Paragraph(f"{total_weight}kg", table_text),
                "",
                "",
            ])

        # ---- Build table ----
        table = Table(
            rows,
            colWidths=[110, 120, 50, 50, 70, 70],
            repeatRows=1,
        )

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]

        # ---- CUSTOMER ROW STYLE ----
        for r in customer_header_row_indices:
            style_commands.extend([
                ("SPAN", (0, r), (-1, r)),
                ("BACKGROUND", (0, r), (-1, r), colors.whitesmoke),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        # ---- AWB ROW STYLE ----
        for r in awb_header_row_indices:
            style_commands.extend([
                ("SPAN", (0, r), (-1, r)),
                ("BACKGROUND", (0, r), (-1, r), colors.Color(0.93, 0.93, 0.93)),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        # ---- PRODUCT ROW STYLE ----
        for r in product_header_row_indices:
            style_commands.extend([
                ("SPAN", (1, r), (-1, r)),  # span from col 1 to end
                ("BACKGROUND", (0, r), (-1, r), colors.Color(0.97, 0.97, 0.97)),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        # ---- TOTALS ROW STYLE ----
        for r in totals_row_indices:
            style_commands.extend([
                ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f2f2f2")),
                ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
            ])

        table.setStyle(TableStyle(style_commands))

        story.append(table)
        story.append(Spacer(1, 16))

    doc.build(
        story, 
        onFirstPage=lambda c, d: (header_with_line(c, d, f"Customer Sales Order - {title}"), footer_with_line(c, d)), 
        onLaterPages=lambda c, d: (header_with_line(c, d, f"Customer Sales Order - {title}"), footer_with_line(c, d)),
    )
    buffer.seek(0)
    return buffer.getvalue()