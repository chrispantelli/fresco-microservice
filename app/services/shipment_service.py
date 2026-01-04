from datetime import datetime, timezone
from io import BytesIO
from typing import Any
from fastapi import Body, Depends, HTTPException
from supabase import Client
import os, json

from ulid import ULID
from app.helpers.supabase import supabase_user_client, supabase_admin_client
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.utils import current_date_epoch

class ShipmentService:
    def __init__(
        self,
        supabase_user: Client = Depends(supabase_user_client),
        supabase_admin: Client = Depends(supabase_admin_client),
    ):
        self.supabase_user = supabase_user
        self.supabase_admin = supabase_admin
        
    async def generate_customer_allocation(self, shipment_id: str, body: Any = Body(...)):
        try:
            results = []

            for i in body:
                customer_id = i["customer_id"]
                customer_name = i["customer_name"]

                pdf_bytes = generate_allocation_sheet(i, f"Customer Sales Order - {customer_name}")

                path = f"shipments/{shipment_id}/{customer_id}/{current_date_epoch()}.pdf"

                upload_res = self.supabase_admin.storage.from_("generated-reports").upload(
                    path=path,
                    file=pdf_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"},
                )

                if not upload_res:
                    raise HTTPException(status_code=500, detail="Failed to upload PDF.")

                public_url = f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/generated-reports/{path}"

                now = datetime.now(timezone.utc).isoformat()

                db_res = self.supabase_user.table("tblshipmentallocationsheets").upsert({
                    "id": f"{shipment_id}-{customer_id}",
                    "shipment_id": shipment_id,
                    "customer_id": customer_id,
                    "url": public_url,
                    "date_generated": now
                }).execute()

                results.append({
                    "customer_id": customer_id,
                    "path": path,
                    "url": public_url,
                    "db": db_res.data if hasattr(db_res, "data") else db_res,
                })

            return {"ok": True, "results": results}

        except HTTPException:
            raise
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

    center_text = ""
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
    
def generate_allocation_sheet(data, title):
    if isinstance(data, str):
        data = json.loads(data)

    # Normalize to list
    if isinstance(data, dict):
        data = [data]

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

    rows = [
        [
            Paragraph("Product", table_text),
            Paragraph("Box No", table_text),
            Paragraph("Weight (Kgs)", table_text),
            Paragraph("£/kg", table_text),
            Paragraph("Box Price", table_text),
        ]
    ]

    customer_header_row_indices = []
    totals_row_indices = []

    for customer in data:
        customer_header_row_indices.append(len(rows))

        total_boxes = 0
        total_weight = 0.0
        total_value = 0.0

        for item in customer.get("items", []):
            print(item)
            box_no = item.get("box_number", 0) or 0
            weight = float(item.get("net_weight", 0) or 0)
            ppk = item.get("price_per_kg")
            box_price = item.get("box_price")

            # Totals
            total_boxes += 1              # count boxes (recommended)
            total_weight += weight
            total_value += float(box_price or 0)

            rows.append([
                Paragraph(str(item.get("product", "-")), table_text),
                Paragraph(str(box_no), table_text),
                Paragraph(f"{weight:g}kg", table_text),
                Paragraph(f"£{ppk:g}" if ppk is not None else "-", table_text),
                Paragraph(f"£{float(box_price):g}" if box_price is not None else "-", table_text),
            ])

        totals_row_indices.append(len(rows))
        rows.append([
            Paragraph("Totals", table_text),
            "",
            Paragraph(str(total_boxes), table_text),
            Paragraph(f"{total_weight:g}kg", table_text),
            "",
            Paragraph(f"£{total_value:g}", table_text),
        ])

    table = Table(
        rows,
        colWidths=[110, 220, 45, 55, 45, 55],  # tweak as needed
        repeatRows=1,
    )

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

    # Customer separator rows (bold + spanning)
    for r in customer_header_row_indices:
        style_commands.extend([
            ("SPAN", (0, r), (-1, r)),
            ("BACKGROUND", (0, r), (-1, r), colors.whitesmoke),
            ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
        ])

    # Totals rows (optional styling)
    for r in totals_row_indices:
        style_commands.extend([
            ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F3F4F6")),  # light grey
            ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
        ])

    table.setStyle(TableStyle(style_commands))

    story.append(Paragraph(f"Release Form Report - {title}", styles["Heading4"]))
    story.append(Spacer(1, 12))
    story.append(table)
    story.append(Spacer(1, 16))

    doc.build(
        story,
        onFirstPage=lambda c, d: (header_with_line(c, d, f"Release Form Report - {title}"), footer_with_line(c, d)),
        onLaterPages=lambda c, d: (header_with_line(c, d, f"Release Form Report - {title}"), footer_with_line(c, d)),
    )

    buffer.seek(0)
    return buffer.getvalue()