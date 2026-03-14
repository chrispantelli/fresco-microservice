import asyncio
from collections import defaultdict
import os
import datetime

from io import BytesIO

from typing import Any, Dict, List
from fastapi import Depends, HTTPException
from supabase import Client
from uuid import uuid4

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from app.classes.report import ReportTemplate
from app.functions.table import build_collection_table, build_release_table, build_shipment_allocation_summary_grid, build_shipment_allocation_table
from app.helpers.db import get_db_connection
from app.helpers.supabase import supabase_user_client, supabase_admin_client
from app.queries.reports import insert_generated_report

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

                groups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

                for shipment in company["shipments"]:
                    awb = shipment.get("awb")
                    production_date = shipment.get("production_date")

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

                        table = build_release_table(pdf, awb_groups)
                        elements.append(table)
                        elements.append(Spacer(1, 18))

                    elements.append(Spacer(1, 8))

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
            conn = get_db_connection()

            try:
                for company in body:
                    transport_company = company.get("transport_company")
                    transport_company_id = transport_company.get('id');       
                    transport_company_name = transport_company.get('name');                
                    file_name = f"{transport_company_name}-{uuid4().hex}-report.pdf"
  
                    buf = BytesIO()
                    pdf_doc = ReportTemplate(
                        buf,
                        header_text=f"{transport_company_name} - Collection Form",
                    )

                    elements: List[Any] = []
                    
                    elements.append(Paragraph(f"Customer"))
                    
                    pdf_doc.build(elements)
                    pdf_bytes = buf.getvalue()
                    buf.close()

                    for customer_items in company.get("customer_items", []):
                        customer_name = customer_items.get("customer_id") or "Unassigned"
                        elements.append(Paragraph(f"Customer: {customer_name}", pdf_doc.styles["Normal"]))
                        elements.append(Spacer(1, 6))

                        customer_total_rows = 0
                        customer_total_weight = 0.0

                        for awb in customer_items.get("awbs", []):
                            awb_id = awb.get("awb") or ""
                            awb_rows = awb.get("items", [])

                            elements.append(Spacer(1, 8))

                            table, awb_total_rows, awb_total_weight = build_collection_table(pdf_doc, transport_company_name, awb_id, awb_rows)
                            elements.append(table)

                            customer_total_rows += awb_total_rows
                            customer_total_weight += awb_total_weight

                        elements.append(Spacer(1, 8))
                        elements.append(
                            Paragraph(
                                f"<b>Customer Totals:</b> &nbsp;&nbsp; "
                                f"Boxes: {customer_total_rows} &nbsp;&nbsp; "
                                f"Weight: {customer_total_weight:.2f}kg",
                                pdf_doc.styles["Normal"],
                            )
                        )
                        elements.append(Spacer(1, 14))

                    pdf_doc.build(elements)
                    pdf_bytes = buf.getvalue()
                    buf.close()

                    file_path = f"collection-forms/{file_name}"

                    res = self.supabase_admin.storage.from_("generated-reports").upload(
                        file_path,
                        pdf_bytes,
                        {"content-type": "application/pdf"},
                    )
                                        
                    pdf_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"

                    await asyncio.to_thread(
                        insert_generated_report,
                        conn,
                        type="collection-form",
                        related_to=transport_company_id,
                        pdf_url=pdf_url,
                        date_from=body[0]['dateRange']['dateFrom'],
                        date_to=body[0]['dateRange']['dateTo']
                    )

                    conn.commit()

                return True
            finally:
                conn.close()

        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))