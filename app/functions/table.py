from typing import Dict, List, Any, Tuple
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

from app.classes.report import ReportTemplate
from app.utils import format_date, to_float, to_number

def build_release_table(
    pdf_doc: ReportTemplate,
    awb_groups: Dict[str, List[Dict[str, Any]]]
):
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

    col_fracs = [0.20, 0.20, 0.40, 0.10, 0.10]
    col_widths = [frame_w * f for f in col_fracs]

    data: List[List[Any]] = [[
        Paragraph("AWB", header),
        Paragraph("Transport Company", header),
        Paragraph("Product", header),
        Paragraph("Box", header),
        Paragraph("Weight", header),
    ]]

    total_box_number = 0
    total_customer_weight = 0.0

    for awb, items in awb_groups.items():
        for index, item in enumerate(items):
            awb_header = awb if index == 0 else ""
            weight = float(item.get("net_weight") or 0)

            data.append([
                Paragraph(str(awb_header or ""), normal),
                Paragraph(str(item.get("transportCompany", {}).get("name", "") or ""), normal),
                Paragraph(str(item.get("product", {}).get("description", "") or ""), normal),
                Paragraph(str(item.get("box_number", "") or ""), normal),
                Paragraph(f"{weight:.2f}", normal),
            ])

            total_box_number += 1
            total_customer_weight += weight

    data.append([
        Paragraph("Totals", footer),
        Paragraph("", footer),
        Paragraph("", footer),
        Paragraph(str(total_box_number), footer),
        Paragraph(f"{total_customer_weight:.2f}kg", footer),
    ])

    last_row = len(data) - 1

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.transparent),
        ("BACKGROUND", (0, 0), (-1, 0), colors.transparent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table

def build_shipment_allocation_summary_grid(pdf_doc, shipment_id, supplier_name, arrival_date, awb, country, production_date, storage_location, expiry_date):
    width = pdf_doc.frame.width
    styles = pdf_doc.styles
    normal = styles["Normal"].clone("grid_normal")
    normal.fontSize = 9
    normal.leading = 11

    data = [
        [
            Paragraph(f"<b>Shipment ID:</b> {shipment_id}", normal),
            Paragraph(f"<b>Supplier:</b> {supplier_name}", normal),
            Paragraph(f"<b>Arrival Date:</b> {format_date(arrival_date)}", normal),
        ],
        [
            Paragraph(f"<b>AWB:</b> {awb}", normal),
            Paragraph(f"<b>Country:</b> {country}", normal),
            Paragraph(f"<b>Production Date:</b> {format_date(production_date)}", normal),
        ],
        [
            Paragraph("", normal),
            Paragraph(f"<b>Storage Location:</b> {storage_location}", normal),
            Paragraph(f"<b>Expiry Date:</b> {format_date(expiry_date)}", normal),
        ],
    ]

    table = Table(
        data,
        colWidths=[width / 3] * 3,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.transparent),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    return table

def build_shipment_allocation_table(
    pdf_doc: ReportTemplate,
    shipment_items: Dict[str, List[Dict[str, Any]]]
):
    frame_w = pdf_doc.frame.width

    normal = pdf_doc.styles["Normal"].clone("tbl_normal")
    normal.fontSize = 9
    normal.leading = 11

    header = pdf_doc.styles["Normal"].clone("tbl_header")
    header.fontName = "Helvetica-Bold"
    header.fontSize = 9
    header.leading = 11
    
    small_style = normal.clone("small_style")
    small_style.fontSize = 8
    small_style.textColor = colors.grey

    footer = pdf_doc.styles["Normal"].clone("tbl_footer")
    footer.fontName = "Helvetica-Bold"
    footer.fontSize = 9
    footer.leading = 11

    col_fracs = [0.05, 0.40, 0.10, 0.05, 0.05, 0.10, 0.10, 0.10, 0.05]
    col_widths = [frame_w * f for f in col_fracs]

    data: List[List[Any]] = [[
        Paragraph("Box No", header),
        Paragraph("Product/Customer", header),
        Paragraph("Currency", header),
        Paragraph("Rate", header),
        Paragraph("Net Weight", header),
        Paragraph("Pieces Per Box", header),
        Paragraph("Price Per Kilo", header),
        Paragraph("Transport Company", header),
        Paragraph("Price", header)
    ]]

    for item in shipment_items:
        price = to_number(item.get("price"))
        net_weight = to_number(item.get("net_weight"))
        pieces_per_box = to_number(item.get("pieces_per_box"))

        data.append([
            Paragraph(str(item.get("box_number") or ""), normal),
            [
                Paragraph((item.get("product") or {}).get("description", ""), normal),
                Paragraph((item.get("customer") or {}).get("name") or "Unallocated", small_style)
            ],
            Paragraph(str(item.get("currency") or ""), normal),
            Paragraph(str(item.get("rate") or ""), normal),
            Paragraph(f"{net_weight:.2f}kg", normal),
            Paragraph(str(int(pieces_per_box)) if pieces_per_box else "", normal),
            Paragraph(str(item.get("todays_price_per_kilo") or ""), normal),
            Paragraph((item.get("transport_companies") or {}).get("name") or "-", normal),
            Paragraph(f"£{price:.2f}", normal),
        ])
    
    total_weight = sum(to_number(item.get("net_weight")) for item in shipment_items)
    total_pieces_per_box = sum(to_number(item.get("pieces_per_box")) for item in shipment_items)
    total_price = sum(to_number(item.get("price")) for item in shipment_items)
    
    data.append([
        Paragraph(f"{len(shipment_items)}", footer),
        Paragraph("", footer),
        Paragraph("", footer),
        Paragraph("", footer),
        Paragraph(f"{total_weight:.2f}kg", footer),
        Paragraph(f"{int(total_pieces_per_box)}", footer),
        Paragraph("", footer),
        Paragraph("", footer),
        Paragraph(f"£{total_price:.2f}", footer)
    ])

    last_row = len(data) - 1

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )
    
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.transparent),
        ("BACKGROUND", (0, 0), (-1, 0), colors.transparent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table

def build_release_table_legacy(
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
    storage_company_name: str,
    awb_groups: Dict[str, List[Dict[str, Any]]]
):
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

    col_fracs = [0.25, 0.25, 0.25, 0.25]
    col_widths = [frame_w * f for f in col_fracs]

    data: List[List[Any]] = [[
        Paragraph("AWB", header),
        Paragraph("Collection Point", header),
        Paragraph("Box", header),
        Paragraph("Weight", header)
    ]]

    total_box_number = 0
    total_customer_weight = 0.0

    for awb, items in awb_groups.items():
        for index, item in enumerate(items):
            awb_header = awb if index == 0 else ""
            weight = float(item.get("net_weight") or 0)

            data.append([
                Paragraph(str(awb_header or ""), normal),
                Paragraph(storage_company_name, normal),
                Paragraph(str(item.get("box_number", "") or ""), normal),
                Paragraph(f"{weight:.2f}", normal),
            ])

            total_box_number += 1
            total_customer_weight += weight

    data.append([
        Paragraph("Totals", footer),
        Paragraph("", footer),
        Paragraph(str(total_box_number), footer),
        Paragraph(f"{total_customer_weight:.2f}kg", footer),
    ])

    last_row = len(data) - 1

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.transparent),
        ("BACKGROUND", (0, 0), (-1, 0), colors.transparent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table

def build_customer_allocation_table(
    pdf_doc: ReportTemplate,
    product_groups: Dict[str, List[Dict[str, Any]]],
):
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

    col_fracs = [0.30, 0.20, 0.05, 0.10, 0.1, 0.15, 0.1]
    col_widths = [frame_w * f for f in col_fracs]

    data: List[List[Any]] = [[
        Paragraph("Product", header),
        Paragraph("AWB", header),
        Paragraph("Box No", header),
        Paragraph("Number of Pieces", header),
        Paragraph("Net Weight", header),
        Paragraph("Price Per Kg", header),
        Paragraph("Price", header)
    ]]

    total_box_number = 0
    total_price_per_kilo = 0.0
    total_customer_weight = 0.0
    total_price = 0.0
         
    product, items = product_groups
    
    for index, item in enumerate(items):
        product_header = product if index == 0 else ""

        net_weight = to_float(item.get("net_weight"))
        price_per_kilo = to_float(item.get("todays_price_per_kilo"))
        price = to_float(item.get("price"))

        data.append([
            Paragraph(str(product_header or ""), normal),
            Paragraph(str(item.get("awb") or ""), normal),
            Paragraph(str(item.get("box_number") or ""), normal),
            Paragraph(str(item.get("pieces_per_box") or ""), normal),
            Paragraph(f"{net_weight:.2f}", normal),
            Paragraph(f"£{price_per_kilo:.2f}", normal),
            Paragraph(f"£{price:.2f}", normal),
        ])

        total_box_number += 1
        total_customer_weight += net_weight
        total_price_per_kilo += price_per_kilo
        total_price += price
        
    data.append([
        Paragraph("Totals", footer),
        Paragraph("", footer),
        Paragraph(str(total_box_number), footer),
        Paragraph("", footer),
        Paragraph(f"{total_customer_weight:.2f}kg", footer),
        Paragraph(f"£{total_price_per_kilo:.2f}", footer),
        Paragraph(f"£{total_price:.2f}", footer)
    ])

    last_row = len(data) - 1

    table = Table(
        data,
        colWidths=col_widths,
        hAlign="CENTER",
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.transparent),
        ("BACKGROUND", (0, 0), (-1, 0), colors.transparent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, last_row), (-1, last_row), colors.whitesmoke),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.0, colors.grey),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
    ]))

    return table