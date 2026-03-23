from collections import defaultdict
import os
import datetime

from io import BytesIO

from typing import Any, Dict, List
from fastapi import Depends, HTTPException
from supabase import Client
from uuid import uuid4

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, CondPageBreak
from reportlab.lib import colors

from app.classes.report import ReportTemplate
from app.functions.table import build_collection_table, build_customer_allocation_table, build_release_table, build_shipment_allocation_summary_grid, build_shipment_allocation_table
from app.helpers.db import get_db_connection
from app.helpers.supabase import supabase_user_client, supabase_admin_client

class ReportService:
    def __init__(
        self,
        supabase_user: Client = Depends(supabase_user_client),
        supabase_admin: Client = Depends(supabase_admin_client),
        db_connection: Client = Depends(get_db_connection),
    ):
        self.supabase_user = supabase_user
        self.supabase_admin = supabase_admin
        self.db_connection = db_connection
    
    async def create_release_form(self, body: List[Dict[str, Any]]):
        try:
            response = []

            for company in body:
                storage_company_id = company.get("id")
                storage_company_name = company.get("name")

                buf = BytesIO()
                pdf = ReportTemplate(
                    buf,
                    header_text=f"{storage_company_name} - Release Form",
                    orientation="portrait"
                )

                elements: List[Any] = []

                groups = defaultdict(
                    lambda: defaultdict(
                        lambda: defaultdict(lambda: {"supplier": None, "items": []})
                    )
                )

                for shipment in company["shipments"]:
                    awb = shipment.get("awb")
                    production_date = shipment.get("production_date")
                    supplier = shipment.get("supplier")

                    for item in shipment["shipment_items"]:
                        customer = item.get("customer")
                        customer_name = customer.get("name") if customer else "Unallocated"

                        awb_group = groups[production_date][customer_name][awb]
                        awb_group["supplier"] = supplier
                        awb_group["items"].append(item)

                production_style = pdf.styles["Normal"].clone("production_style")
                production_style.fontName = "Helvetica-Bold"
                production_style.fontSize = 11
                production_style.leading = 13
                production_style.leftIndent = 0
                production_style.firstLineIndent = 0
                production_style.spaceBefore = 0
                production_style.spaceAfter = 6

                dispatch_style = pdf.styles["Normal"].clone("dispatch_style")
                dispatch_style.fontName = "Helvetica-Bold"
                dispatch_style.fontSize = 8
                dispatch_style.leftIndent = 0
                dispatch_style.firstLineIndent = 0
                dispatch_style.spaceBefore = 0
                dispatch_style.spaceAfter = 8

                customer_style = pdf.styles["Normal"].clone("customer_style")
                customer_style.fontName = "Helvetica-Bold"
                customer_style.fontSize = 10
                customer_style.leftIndent = 0
                customer_style.firstLineIndent = 0
                customer_style.spaceBefore = 0
                customer_style.spaceAfter = 6

                summary_title_style = pdf.styles["Normal"].clone("summary_title_style")
                summary_title_style.fontName = "Helvetica-Bold"
                summary_title_style.fontSize = 11
                summary_title_style.leading = 13
                summary_title_style.spaceBefore = 8
                summary_title_style.spaceAfter = 8

                summary_text_style = pdf.styles["Normal"].clone("summary_text_style")
                summary_text_style.fontName = "Helvetica"
                summary_text_style.fontSize = 9
                summary_text_style.leading = 11
                summary_text_style.spaceBefore = 0
                summary_text_style.spaceAfter = 4

                summary = {
                    "total_customers": set(),
                    "total_awbs": set(),
                    "total_boxes": 0,
                    "total_weight": 0.0,
                    "customers": defaultdict(lambda: {
                        "awbs": set(),
                        "boxes": 0,
                        "weight": 0.0
                    })
                }

                for production_date, customers in groups.items():
                    formatted_date = datetime.datetime.fromisoformat(
                        production_date.replace("Z", "+00:00")
                    ).strftime("%d %b %Y")

                    elements.append(
                        Paragraph(f"For products dispatched on: {formatted_date}", dispatch_style)
                    )
                    elements.append(Spacer(1, 8))

                    for customer_name, awb_groups in customers.items():
                        elements.append(Paragraph(customer_name, customer_style))
                        elements.append(Spacer(1, 6))

                        # Update summary
                        summary["total_customers"].add(customer_name)

                        for awb, awb_data in awb_groups.items():
                            summary["total_awbs"].add(awb)
                            summary["customers"][customer_name]["awbs"].add(awb)

                            for item in awb_data["items"]:
                                weight = item.get("net_weight") or 0

                                summary["total_boxes"] += 1
                                summary["total_weight"] += weight
                                summary["customers"][customer_name]["boxes"] += 1
                                summary["customers"][customer_name]["weight"] += weight

                        table = build_release_table(pdf, awb_groups)
                        elements.append(table)
                        elements.append(Spacer(1, 18))

                    elements.append(Spacer(1, 8))

                elements.append(CondPageBreak(120))
                elements.append(Paragraph("Summary", summary_title_style))
                elements.append(
                    Paragraph(
                        f"Total customers: {len(summary['total_customers'])}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total AWBs: {len(summary['total_awbs'])}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total boxes: {summary['total_boxes']}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total weight: {summary['total_weight']:.2f} kg",
                        summary_text_style
                    )
                )

                elements.append(Spacer(1, 12))
                elements.append(Paragraph("Customer Breakdown", summary_title_style))
                elements.append(Spacer(1, 6))

                summary_data = [[
                    Paragraph("Customer", customer_style),
                    Paragraph("AWBs", customer_style),
                    Paragraph("Boxes", customer_style),
                    Paragraph("Weight (kg)", customer_style),
                ]]

                for customer_name, customer_summary in summary["customers"].items():
                    summary_data.append([
                        Paragraph(customer_name, summary_text_style),
                        Paragraph(str(len(customer_summary["awbs"])), summary_text_style),
                        Paragraph(str(customer_summary["boxes"]), summary_text_style),
                        Paragraph(f"{customer_summary['weight']:.2f}", summary_text_style),
                    ])

                summary_table = Table(summary_data, colWidths=[180, 70, 70, 90])
                summary_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                ]))
                elements.append(summary_table)

                pdf.build(elements)
                pdf_bytes = buf.getvalue()
                buf.close()

                file_path = f"release-forms/{uuid4().hex}.pdf"

                res = self.supabase_admin.storage.from_("generated-reports").upload(
                    file_path,
                    pdf_bytes,
                    {"content-type": "application/pdf"},
                )

                url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"

                response.append({
                    "type": "release_form",
                    "storage_company_id": storage_company_id,
                    "url": url,
                    "body": body,
                    "date_generated": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })

            return response

        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
    async def create_shipment_allocation(self, body: List[Dict[str, Any]]):
        try:
            awb = body.get("awb")
            shipment_id = body.get("id")
            shipment_items = body.get("shipment_items")
            supplier = body.get('supplier')
            arrival_date = body.get('arrival_date')
            country = body.get('country')
            production_date = body.get('production_date')
            storage_name = (body.get("storage_companies") or {}).get("name", "")
            expiry_date = body.get('expiry_date')

            buf = BytesIO()
            pdf = ReportTemplate(
                buf,
                header_text=f"Fresco Shipment - {awb}",
                orientation="landscape"
            )
            
            elements: List[Any] = []
            
            summary_table = build_shipment_allocation_summary_grid(pdf, shipment_id, supplier, arrival_date, awb, country, production_date, storage_name, expiry_date)
            elements.append(summary_table)
            
            elements.append(Spacer(1, 16))
            
            table = build_shipment_allocation_table(pdf, shipment_items)
            elements.append(table)
            
            pdf.build(elements)
            pdf_bytes = buf.getvalue()
            buf.close()

            file_path = f"shipment-allocations/{uuid4().hex}.pdf"

            res = self.supabase_admin.storage.from_("generated-reports").upload(
                file_path,
                pdf_bytes,
                {"content-type": "application/pdf"},
            )

            url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"

            return {
                "type": "shipment_allocation",
                "shipment_id": shipment_id,
                "url": url,
                "body": body,
                "date_generated": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
                                        
        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
    async def create_collection_form(self, body: List[Dict[str, Any]]):
        try:
            response = []

            for company in body:
                transport_company_id = company.get("id")
                transport_company_name = company.get("name")

                buf = BytesIO()
                pdf = ReportTemplate(
                    buf,
                    header_text=f"{transport_company_name} - Collection/Delivery Form",
                    orientation="portrait"
                )

                elements: List[Any] = []

                groups = defaultdict(
                    lambda: defaultdict(
                        lambda: defaultdict(list)
                    )
                )

                for shipment in company["shipments"]:
                    awb = shipment.get("awb")
                    production_date = shipment.get("production_date")
                    storage_company_name = shipment.get('storage_companies').get('name')

                    for item in shipment["shipment_items"]:
                        customer = item.get("customer")

                        if customer:
                            customer_name = customer.get("name")
                            groups[production_date][customer_name][awb].append(item)

                production_style = pdf.styles["Normal"].clone("production_style")
                production_style.fontName = "Helvetica-Bold"
                production_style.fontSize = 11
                production_style.leading = 13
                production_style.leftIndent = 0
                production_style.firstLineIndent = 0
                production_style.spaceBefore = 0
                production_style.spaceAfter = 6
                
                dispatch_style = pdf.styles["Normal"].clone("dispatch_style")
                dispatch_style.fontName = "Helvetica-Bold"
                dispatch_style.fontSize = 8
                dispatch_style.leftIndent = 0
                dispatch_style.firstLineIndent = 0
                dispatch_style.spaceBefore = 0
                dispatch_style.spaceAfter = 8

                customer_style = pdf.styles["Normal"].clone("customer_style")
                customer_style.fontName = "Helvetica-Bold"
                customer_style.fontSize = 10
                customer_style.leftIndent = 0
                customer_style.firstLineIndent = 0
                customer_style.spaceBefore = 0
                customer_style.spaceAfter = 6
                
                for production_date, customers in groups.items():
                    formated_date = datetime.datetime.fromisoformat(
                                        production_date.replace("Z", "+00:00")
                                    ).strftime("%d %b %Y")
                    
                    elements.append(
                        Paragraph(f"For products dispatched on: {formated_date}", dispatch_style)
                    )
                    elements.append(Spacer(1, 8))

                    for customer_name, awb_groups in customers.items():
                        elements.append(Paragraph(customer_name, customer_style))
                        elements.append(Spacer(1, 6))

                        table = build_collection_table(pdf, storage_company_name, awb_groups)
                        elements.append(table)
                        elements.append(Spacer(1, 18))

                    elements.append(Spacer(1, 8))

                pdf.build(elements)
                pdf_bytes = buf.getvalue()
                buf.close()

                file_path = f"collection-forms/{uuid4().hex}.pdf"

                res = self.supabase_admin.storage.from_("generated-reports").upload(
                    file_path,
                    pdf_bytes,
                    {"content-type": "application/pdf"},
                )

                url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"

                response.append({
                    "type": "release_form",
                    "transport_company_id": transport_company_id,
                    "url": url,
                    "body": body,
                    "date_generated": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                
            return response

        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
    async def create_customer_allocation_form(self, body: List[Dict[str, Any]]):
        try:
            response = []

            for customer in body:
                customer_id = customer.get("id")
                customer_name = customer.get("name")

                buf = BytesIO()
                pdf = ReportTemplate(
                    buf,
                    header_text=f"{customer_name} - Customer Sales Order",
                    orientation="portrait"
                )

                elements: List[Any] = []

                groups = defaultdict(lambda: defaultdict(list))

                summary = {
                    "total_awbs": set(),
                    "total_products": set(),
                    "total_boxes": 0,
                    "total_weight": 0.0,
                    "products": defaultdict(lambda: {
                        "boxes": 0,
                        "weight": 0.0
                    })
                }

                for shipment in customer.get("shipments", []):
                    production_date = shipment.get("production_date")
                    awb = shipment.get("awb")

                    if awb:
                        summary["total_awbs"].add(awb)

                    for item in shipment.get("shipment_items", []):
                        product = item.get("product")
                        if not product:
                            continue

                        product_name = product.get("description") or "Unknown Product"
                        groups[production_date][product_name].append(item)

                production_style = pdf.styles["Normal"].clone("production_style")
                production_style.fontName = "Helvetica-Bold"
                production_style.fontSize = 11
                production_style.leading = 13
                production_style.leftIndent = 0
                production_style.firstLineIndent = 0
                production_style.spaceBefore = 0
                production_style.spaceAfter = 6

                dispatch_style = pdf.styles["Normal"].clone("dispatch_style")
                dispatch_style.fontName = "Helvetica-Bold"
                dispatch_style.fontSize = 8
                dispatch_style.leftIndent = 0
                dispatch_style.firstLineIndent = 0
                dispatch_style.spaceBefore = 0
                dispatch_style.spaceAfter = 8

                customer_style = pdf.styles["Normal"].clone("customer_style")
                customer_style.fontName = "Helvetica-Bold"
                customer_style.fontSize = 10
                customer_style.leftIndent = 0
                customer_style.firstLineIndent = 0
                customer_style.spaceBefore = 0
                customer_style.spaceAfter = 6

                summary_title_style = pdf.styles["Normal"].clone("summary_title_style")
                summary_title_style.fontName = "Helvetica-Bold"
                summary_title_style.fontSize = 11
                summary_title_style.leading = 13
                summary_title_style.spaceBefore = 8
                summary_title_style.spaceAfter = 8

                summary_text_style = pdf.styles["Normal"].clone("summary_text_style")
                summary_text_style.fontName = "Helvetica"
                summary_text_style.fontSize = 9
                summary_text_style.leading = 11
                summary_text_style.spaceBefore = 0
                summary_text_style.spaceAfter = 4

                for production_date in sorted(groups.keys()):
                    products = groups[production_date]

                    formatted_date = datetime.datetime.fromisoformat(
                        production_date.replace("Z", "+00:00")
                    ).strftime("%d %b %Y")

                    elements.append(
                        Paragraph(f"For products dispatched on: {formatted_date}", dispatch_style)
                    )
                    elements.append(Spacer(1, 8))

                    for product_name in sorted(products.keys()):
                        product_items = products[product_name]

                        summary["total_products"].add(product_name)

                        for item in product_items:
                            weight = (
                                item.get("customer_weight")
                                or item.get("weight")
                                or item.get("net_weight")
                                or 0
                            )

                            try:
                                weight = float(weight)
                            except Exception:
                                weight = 0.0

                            # each item row represents one box
                            summary["total_boxes"] += 1
                            summary["total_weight"] += weight
                            summary["products"][product_name]["boxes"] += 1
                            summary["products"][product_name]["weight"] += weight

                        table = build_customer_allocation_table(pdf, (product_name, product_items))
                        elements.append(table)
                        elements.append(Spacer(1, 18))

                    elements.append(Spacer(1, 8))

                if elements and isinstance(elements[-1], Spacer):
                    elements.pop()

                elements.append(CondPageBreak(140))
                elements.append(Paragraph("Summary", summary_title_style))
                elements.append(
                    Paragraph(
                        f"Total AWBs: {len(summary['total_awbs'])}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total products: {len(summary['total_products'])}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total boxes: {summary['total_boxes']}",
                        summary_text_style
                    )
                )
                elements.append(
                    Paragraph(
                        f"Total weight: {summary['total_weight']:.2f} kg",
                        summary_text_style
                    )
                )

                elements.append(Spacer(1, 12))
                elements.append(Paragraph("Product Breakdown", summary_title_style))
                elements.append(Spacer(1, 6))

                summary_data = [[
                    Paragraph("Product", customer_style),
                    Paragraph("Boxes", customer_style),
                    Paragraph("Weight (kg)", customer_style),
                ]]

                for product_name in sorted(summary["products"].keys()):
                    product_summary = summary["products"][product_name]
                    summary_data.append([
                        Paragraph(product_name, summary_text_style),
                        Paragraph(str(product_summary["boxes"]), summary_text_style),
                        Paragraph(f"{product_summary['weight']:.2f}", summary_text_style),
                    ])

                summary_table = Table(summary_data, colWidths=[300, 80, 100])
                summary_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                ]))
                elements.append(summary_table)

                pdf.build(elements)
                pdf_bytes = buf.getvalue()
                buf.close()

                file_path = f"customer-allocation-forms/{uuid4().hex}.pdf"

                res = self.supabase_admin.storage.from_("generated-reports").upload(
                    file_path,
                    pdf_bytes,
                    {"content-type": "application/pdf"},
                )

                url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"

                response.append({
                    "type": "customer_allocation_form",
                    "customer_id": customer_id,
                    "url": url,
                    "body": body,
                    "date_generated": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })

            return response

        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))