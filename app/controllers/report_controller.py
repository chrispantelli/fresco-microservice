from typing import Any, Dict
from fastapi import APIRouter, Body, Depends
from fastapi_restful.cbv import cbv

from app.services.report_service import ReportService

report_router = APIRouter()

@cbv(report_router)
class ReportController:
    report_service: ReportService = Depends(ReportService)
        
    @report_router.post('/reports/release-forms', operation_id="create_release_form")
    async def create_release_form(self, body: Any = Body(...)):
        return await self.report_service.create_release_form(body)
    
    @report_router.post('/reports/shipment-allocations', operation_id="create_shipment_allocation")
    async def create_shipment_allocation(self, body: Any = Body(...)):
        return await self.report_service.create_shipment_allocation(body)
    
    @report_router.post('/reports/collection-forms', operation_id="create_collection_form")
    async def create_collection_form(self, body: Any = Body(...)):
        return await self.report_service.create_collection_form(body)
    
    @report_router.post('/reports/customer-allocation-forms', operation_id="create_customer_allocation_form")
    async def create_customer_allocation_form(self, body: Any = Body(...)):
        return await self.report_service.create_customer_allocation_form(body)
        
        