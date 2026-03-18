from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate


class ReportTemplate(BaseDocTemplate):
    def __init__(
        self,
        filename: str,
        header_text: str = "Report",
        orientation: str = "portrait",
        base_pagesize=A4,
        **kwargs
    ):
        if orientation.lower() == "landscape":
            kwargs["pagesize"] = landscape(base_pagesize)
        else:
            kwargs["pagesize"] = portrait(base_pagesize)

        super().__init__(filename, **kwargs)

        # Keep styles available for body content
        self.styles = getSampleStyleSheet()

        self.logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.jpeg"

        margin = 0.5 * inch
        header_h = 0.9 * inch
        footer_h = 0.25 * inch
        gap = 0.10 * inch

        page_w, page_h = self.pagesize

        body_x = margin
        body_y = margin + footer_h + gap
        body_w = page_w - 2 * margin
        body_h = page_h - (2 * margin) - header_h - footer_h - (2 * gap)

        self.frame = Frame(body_x, body_y, body_w, body_h, id="normal")
        self.header_text = header_text

        self.header_frame = Frame(
            margin,
            page_h - margin - header_h,
            body_w,
            header_h,
            id="header",
            showBoundary=0,
        )

        self.footer_frame = Frame(
            margin,
            margin,
            body_w,
            footer_h,
            id="footer",
            showBoundary=0,
        )

        self.addPageTemplates([
            PageTemplate(
                id="Main",
                frames=[self.frame],
                onPage=self._draw_header_footer,
            )
        ])

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()

        line_color = colors.lightgrey
        text_color = colors.black

        left_x = self.header_frame.x1
        right_x = self.header_frame.x1 + self.header_frame.width

        header_y = self.header_frame.y1
        header_h = self.header_frame.height
        header_top_y = header_y + header_h

        footer_y = self.footer_frame.y1 + 4

        # Top header line
        canvas.setStrokeColor(line_color)
        canvas.setLineWidth(0.5)
        canvas.line(left_x, header_top_y + 4, right_x, header_top_y + 4)

        # Logo
        logo_reserved_w = 2.4 * inch

        if self.logo_path.exists():
            try:
                logo = ImageReader(str(self.logo_path))
                img_w, img_h = logo.getSize()

                max_logo_w = logo_reserved_w
                max_logo_h = header_h - 8

                scale = min(max_logo_w / img_w, max_logo_h / img_h)
                logo_w = img_w * scale
                logo_h = img_h * scale

                logo_x = right_x - logo_w
                logo_y = header_y + (header_h - logo_h) / 2

                canvas.drawImage(
                    logo,
                    logo_x,
                    logo_y,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass

        # Text block
        company_font = "Helvetica-Bold"
        company_font_size = 12
        report_font = "Helvetica"
        report_font_size = 9
        line_gap = 4

        text_block_height = company_font_size + line_gap + report_font_size
        center_y = header_y + (header_h / 2)

        company_y = center_y + (text_block_height / 2) - company_font_size + 2
        report_y = company_y - report_font_size - line_gap

        canvas.setFillColor(text_color)

        canvas.setFont(company_font, company_font_size)
        canvas.drawString(left_x, company_y, "Fresco Fisheries (UK) Limited")

        canvas.setFont(report_font, report_font_size)
        canvas.drawString(left_x, report_y, self.header_text)

        # Header bottom divider
        canvas.setStrokeColor(line_color)
        canvas.setLineWidth(0.75)
        canvas.line(left_x, header_y - 4, right_x, header_y - 4)

        # Footer
        canvas.setFont("Helvetica", 9)
        canvas.drawString(
            left_x,
            footer_y,
            f"Generated on {datetime.now().strftime('%d %b %Y')}",
        )
        canvas.drawRightString(right_x, footer_y, f"Page: {doc.page}")

        canvas.line(
            left_x,
            self.footer_frame.y1 + self.footer_frame.height + 4,
            right_x,
            self.footer_frame.y1 + self.footer_frame.height + 4,
        )

        canvas.restoreState()