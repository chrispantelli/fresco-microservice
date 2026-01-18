import asyncio
import os

from io import BytesIO

from typing import Any, Dict, List
from fastapi import Depends, HTTPException
from supabase import Client
from uuid import uuid4

from reportlab.platypus import Paragraph, Spacer

from app.classes.report import ReportTemplate
from app.functions.table import build_collection_table, build_release_table
from app.helpers.db import get_db_connection
from app.helpers.supabase import supabase_user_client, supabase_admin_client
from app.queries.reports import insert_generated_report
from app.utils import current_date_epoch

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
            conn = get_db_connection()

            try:
                for company in body:
                    storage_company = company.get("storage_company")
                    storage_company_id = storage_company.get('id');       
                    storage_company_name = storage_company.get('name');      
                    file_name = f"{storage_company_name}-{uuid4().hex}-report.pdf"

                    buf = BytesIO()
                    pdf_doc = ReportTemplate(
                        buf,
                        header_text=f"{storage_company_name} - Release Form",
                    )

                    elements: List[Any] = []

                    for customer_items in company.get("customer_items", []):
                        customer_name = customer_items.get("customer_name") or "Unassigned"
                        elements.append(Paragraph(f"Customer: {customer_name}", pdf_doc.styles["Normal"]))
                        elements.append(Spacer(1, 6))

                        customer_total_rows = 0
                        customer_total_weight = 0.0

                        for awb in customer_items.get("awbs", []):
                            awb_id = awb.get("awb") or ""
                            awb_rows = awb.get("items", [])

                            elements.append(Spacer(1, 8))

                            table, awb_total_rows, awb_total_weight = build_release_table(pdf_doc, awb_id, awb_rows)
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

                    file_path = f"release-forms/{file_name}"

                    res = self.supabase_admin.storage.from_("generated-reports").upload(
                        file_path,
                        pdf_bytes,
                        {"content-type": "application/pdf"},
                    )
                    
                    
                    pdf_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{res.full_path}"
                                        
                    await asyncio.to_thread(
                        insert_generated_report,
                        conn,
                        type="release-form",
                        related_to=storage_company_id,
                        pdf_url=pdf_url,
                        date_from=body[0]['dateRange']['dateFrom'],
                        date_to=body[0]["dateRange"]['dateTo']
                    )

                    conn.commit()

                return True
            finally:
                conn.close()

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