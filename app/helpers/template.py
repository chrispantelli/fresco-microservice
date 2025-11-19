from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
import os

def add_header_and_footer(canvas, doc):
    LOGO_PATH = os.path.join(os.getcwd(), "app", "assets", "logo.jpeg")

    page_width, page_height = A4

    logo_width = 160
    logo_height = 80

    x = 0
    y = page_height - logo_height - 20

    canvas.drawImage(
        LOGO_PATH,
        x,
        y,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=True,
        mask="auto",
    )

    # Footer (left + right text)
    generated_text = f"Generated on {datetime.now().strftime('%d %b %Y')} | Page {doc.page}"
    address_text = f"Cedar House, Sopers Rd, Cuffley, Potters Bar EN6 4RY | E: info@frescofisheries.co.uk | T: 01992 893111"

    left_margin = doc.leftMargin
    right_margin = doc.rightMargin
    bottom_margin = doc.bottomMargin

    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setStrokeColor(colors.grey)
    canvas.setLineWidth(0.25)
    canvas.line(left_margin, bottom_margin - 5, page_width - right_margin, bottom_margin - 5)

    # Draw left footer text
    canvas.drawString(left_margin, bottom_margin - 18, generated_text)

    # Draw right footer text (aligned to right edge)
    text_width = canvas.stringWidth(address_text, "Helvetica", 8)
    canvas.drawString(page_width - right_margin - text_width, bottom_margin - 18, address_text)

    canvas.restoreState()
    
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

base = ParagraphStyle("base", fontName="Helvetica", fontSize=9, leading=11, spaceBefore=0, spaceAfter=0)
header_style = ParagraphStyle("header", parent=base, fontName="Helvetica-Bold", fontSize=9, textColor=colors.black, alignment=0)
customer_style = ParagraphStyle("customer", parent=base, fontName="Helvetica-Bold", fontSize=10, spaceBefore=4, spaceAfter=2)
awb_style = ParagraphStyle("awb", parent=base, fontName="Helvetica-Bold", fontSize=9, leftIndent=0, textColor=colors.HexColor("#333333"))
cell_style = ParagraphStyle("cell", parent=base, leftIndent=0, alignment=0)