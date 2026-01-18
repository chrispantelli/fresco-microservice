from datetime import datetime, timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph
from reportlab.lib import colors

class ReportTemplate(BaseDocTemplate):
    def __init__(self, filename: str, header_text: str = "Report", **kwargs):
        super().__init__(filename, **kwargs)
        self.styles = getSampleStyleSheet()

        margin = inch
        header_h = 0.25 * inch
        footer_h = 0.25 * inch
        gap = 0.10 * inch

        page_w, page_h = self.pagesize

        body_x = margin
        body_y = margin + footer_h + gap
        body_w = page_w - 2 * margin
        body_h = page_h - (2 * margin) - header_h - footer_h - (2 * gap)

        self.frame = Frame(body_x, body_y, body_w, body_h, id="normal")

        self.header_text = header_text

        self.header_style = self.styles["Heading1"].clone("header_style")
        self.footer_style = self.styles["Normal"].clone("footer_style")
        self.header_style.alignment = 1
        self.footer_style.alignment = 1

        self.header_frame = Frame(
            margin, page_h - margin - header_h, body_w, header_h, id="header", showBoundary=0
        )
        self.footer_frame = Frame(
            margin, margin, body_w, footer_h, id="footer", showBoundary=0
        )

        self.addPageTemplates(
            [PageTemplate(id="Main", frames=[self.frame], onPage=self._draw_header_footer)]
        )

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()

        line_color = colors.lightgrey
        text_color = colors.black
        line_width = 0.75

        left_x = self.header_frame.x1
        right_x = self.header_frame.x1 + self.header_frame.width
        
        header_top_y = self.header_frame.y1 + self.header_frame.height
        header_text_y = self.header_frame.y1 + 8
        footer_y = self.footer_frame.y1 + 4

        canvas.setStrokeColor(line_color)
        canvas.setLineWidth(0.5)
        canvas.line(
            left_x,
            header_top_y + 6,
            right_x,
            header_top_y + 6,
        )

        canvas.setFillColor(text_color)
        canvas.setFont("Helvetica-Bold", 11)

        canvas.drawString(
            left_x,
            header_text_y,
            "Fresco Fisheries (UK) Limited",
        )

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(
            right_x,
            header_text_y,
            self.header_text,
        )

        canvas.setStrokeColor(line_color)
        canvas.setLineWidth(line_width)
        canvas.line(
            left_x,
            self.header_frame.y1 - 4,
            right_x,
            self.header_frame.y1 - 4,
        )

        canvas.drawString(
            left_x,
            footer_y,
            f"Generated on {datetime.now().strftime('%d %b %Y')}",
        )

        canvas.drawRightString(
            right_x,
            footer_y,
            f"Page: {doc.page}",
        )

        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.75)
        canvas.line(
            left_x,
            self.footer_frame.y1 + self.footer_frame.height + 4,
            right_x,
            self.footer_frame.y1 + self.footer_frame.height + 4,
        )

        canvas.restoreState()