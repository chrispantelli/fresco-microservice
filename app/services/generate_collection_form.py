import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from datetime import datetime
from app.helpers.template import add_header_and_footer
from io import BytesIO

def generate_collection_form_pdf(payload, transport_comany):
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    buffer = BytesIO()
        
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=110,   
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    story = []
    
    # --- Styles ---
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9, leading=11, spaceBefore=0, spaceAfter=0)
    header_style = ParagraphStyle("header", parent=base, fontName="Helvetica-Bold", fontSize=9, textColor=colors.black, alignment=0)
    customer_style = ParagraphStyle("customer", parent=base, fontName="Helvetica-Bold", fontSize=10, spaceBefore=4, spaceAfter=2)
    awb_style = ParagraphStyle("awb", parent=base, fontName="Helvetica-Bold", fontSize=9, leftIndent=0, textColor=colors.HexColor("#333333"))
    cell_style = ParagraphStyle("cell", parent=base, leftIndent=0, alignment=0)

    story.append(Paragraph(
        f"Fresco Collection/Delivery Form {transport_comany}",
        ParagraphStyle("header", parent=base, fontName="Helvetica-Bold", fontSize=14, textColor=colors.black, alignment=0)
    ))
    
    for batch in payload:
        # Production date header
        prod_date = datetime.fromisoformat(batch["production_date"].replace("Z", "+00:00"))
        heading_style = ParagraphStyle(
            "dispatch_heading_strict",
            parent=styles["Normal"],        # neutral, no auto-indent
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#000000"),
            spaceBefore=6,
            spaceAfter=6,
            leading=14,
            alignment=0,                    # left align
            leftIndent=0,
            firstLineIndent=0,              # disable paragraph indent
            rightIndent=0,
        )
        
        story.append(Paragraph(
            f"For products dispatched on {prod_date.strftime('%d %b %Y')}",
            heading_style
        ))
        story.append(Spacer(1, 4))

        # Table header
        table_data = [[
            Paragraph("Customer/AWB", header_style),
            Paragraph("Collection Point", header_style),
            Paragraph("Box No", header_style),
            Paragraph("Weight (Kgs)", header_style),
        ]]

        # Data rows
        for cust in batch["customers"]:
            customer_name = cust["customer_name"] or "Unallocated"
            total_box_number = 0
            total_net_weight = 0
            table_data.append([Paragraph(f"{customer_name}", customer_style), "", "", "", ""])

            for awb_entry in cust["awbs"]:
                awb = awb_entry["awb"]

                for index, item in enumerate(awb_entry["shipment_items"]):
                    # Only include the AWB value in the first row of each group
                    awb_cell = Paragraph(awb, awb_style) if index == 0 else Paragraph("", cell_style)

                    table_data.append([
                        awb_cell,
                        Paragraph(item.get("storage_company", "") or "-", cell_style),
                        Paragraph(str(item["box_number"]), cell_style),
                        Paragraph(str(item["net_weight"]), cell_style),
                    ])

                    total_box_number += item["box_number"]
                    total_net_weight += item["net_weight"]
            
            table_data.append([
                Paragraph("Totals:", header_style),
                Paragraph(""),
                Paragraph(f"{str(total_box_number)}", header_style),
                Paragraph(f"{str(total_net_weight)}kg", header_style)
            ])

        # Table formatting
        table = Table(table_data, colWidths=[150, 200, 60, 60], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.transparent),
        ]))

        story.append(table)
        story.append(Spacer(1, 12))

    pdf.build(story, onFirstPage=add_header_and_footer, onLaterPages=add_header_and_footer)
    buffer.seek(0)
    return buffer.getvalue()
