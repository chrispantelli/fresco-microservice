from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from datetime import datetime

def add_header_and_footer(canvas: canvas.Canvas, doc):
        page_width, page_height = A4

        logo_path = "assets/logo.jpeg"
        logo_width = 160
        logo_height = 80

        # Flush-left logo (ignore left margin)
        x = 0               # start at page edge
        y = page_height - logo_height - 0  # a bit below the top edge

        canvas.drawImage(
            logo_path,
            x,
            y,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%d %b %Y')} | Page {doc.page}"
        left_margin = doc.leftMargin
        right_margin = doc.rightMargin
        bottom_margin = doc.bottomMargin
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.25)
        canvas.line(left_margin, bottom_margin - 5, page_width - right_margin, bottom_margin - 5)
        canvas.drawString(left_margin, bottom_margin - 18, footer_text)
        canvas.restoreState()