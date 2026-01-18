from typing import Dict, List, Any, Tuple
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

from app.classes.report import ReportTemplate

def build_release_table(
    pdf_doc: ReportTemplate,
    awb: str,
    rows: List[Dict[str, Any]]
) -> Tuple[Table, int, float]:
    frame_w = pdf_doc.frame.width

    normal = pdf_doc.styles["Normal"].clone("tbl_normal")
    normal.fontSize = 9
    normal.leading = 11

    header = pdf_doc.styles["Normal"].clone("tbl_header")
    header.fontName = "Helvetica-Bold"
    header.fontSize = 9
    header.leading = 11

    footer = pdf_doc.styles["Normal"].clone("tbl_footer")
    footer.fontName = "Helvetica-Bold"
    footer.fontSize = 9
    footer.leading = 11

    data: List[List[Any]] = [[
        Paragraph("AWB", header),
        Paragraph("Transport Company", header),
        Paragraph("Product", header),
        Paragraph("Box No", header),
        Paragraph("Weight", header),
    ]]

    total_weight = 0.0

    for r in rows or []:
        transport_name = (r.get("transport_company") or {}).get("name") or ""
        product_name = (r.get("product") or {}).get("name") or ""
        box_number = r.get("box_number") or ""
        net_weight = r.get("net_weight") or 0

        try:
            total_weight += float(net_weight)
        except (TypeError, ValueError):
            pass

        data.append([
            Paragraph(str(awb), normal),
            Paragraph(str(transport_name), normal),
            Paragraph(str(product_name), normal),
            Paragraph(str(box_number), normal),
            Paragraph(str(net_weight), normal),
        ])

    total_rows = len(rows or [])

    # AWB footer row
    data.append([
        Paragraph("Total", footer),
        Paragraph("", footer),
        Paragraph("", footer),
        Paragraph(f"{total_rows}", footer),
        Paragraph(f"{total_weight:.2f}kg", footer),
    ])

    col_fracs = [0.20, 0.20, 0.40, 0.10, 0.10]
    col_widths = [frame_w * f for f in col_fracs]

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )

    last_row = len(data) - 1

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),

        # Style AWB totals row
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table, total_rows, total_weight

def build_collection_table(
    pdf_doc: ReportTemplate,
    transport_company: str,
    awb: str,
    rows: List[Dict[str, Any]]
) -> Tuple[Table, int, float]:
    frame_w = pdf_doc.frame.width

    normal = pdf_doc.styles["Normal"].clone("tbl_normal")
    normal.fontSize = 9
    normal.leading = 11

    header = pdf_doc.styles["Normal"].clone("tbl_header")
    header.fontName = "Helvetica-Bold"
    header.fontSize = 9
    header.leading = 11

    footer = pdf_doc.styles["Normal"].clone("tbl_footer")
    footer.fontName = "Helvetica-Bold"
    footer.fontSize = 9
    footer.leading = 11

    data: List[List[Any]] = [[
        Paragraph("AWB", header),
        Paragraph("Collection Point", header),
        Paragraph("Box No")
    ]]

    total_weight = 0.0
    
    for r in rows or []:
        box_number = r.get("box_number") or ""
        net_weight = r.get("net_weight") or 0
        
        try:
            total_weight += float(net_weight)
        except (TypeError, ValueError):
            pass

        data.append([
            Paragraph(str(awb), normal),
            Paragraph(str(transport_company), normal),
            Paragraph(str(box_number), normal),
        ])

        

    total_rows = len(rows or [])

    # AWB footer row
    data.append([
        Paragraph("Total", footer),
        Paragraph("", footer),
        Paragraph(f"{total_rows}", footer),
    ])

    col_fracs = [0.50, 0.40, 0.10]
    col_widths = [frame_w * f for f in col_fracs]

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )

    last_row = len(data) - 1

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),

        # Style AWB totals row
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table, total_rows, total_weight